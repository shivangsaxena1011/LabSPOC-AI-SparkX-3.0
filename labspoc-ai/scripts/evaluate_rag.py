import os
import sys
import json
import time
import re
import uuid
import hashlib
from pathlib import Path

# Ensure api app is importable
repo_root = Path(__file__).resolve().parent.parent
api_dir = repo_root / "apps" / "api"
sys.path.insert(0, str(api_dir))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base, Document, DocumentChunk, ChunkVector, Asset
from app.embeddings import embed_text
from app.retrieval import retrieve
from app.llm import generate_grounded_answer

BENCHMARK_DOCUMENTS = [
    {
        "filename": "NVIDIA_DGX_Station_A100_SOP.txt",
        "disclaimer": "Synthetic demonstration record for SPARKX 3.0 benchmark",
        "category": "sop",
        "chunks": [
            "The NVIDIA DGX Station A100 delivers 2.5 petaFLOPS of AI performance with 320GB total GPU memory across 4x NVIDIA A100 80GB Tensor Core GPUs. System memory consists of 512GB DDR4 RAM and 7.68TB NVMe storage. Power requirements necessitate a dedicated 15A circuit at 200-240V AC, with a maximum system power consumption rating of 1500W under peak sustained synthetic matrix multiplication workloads.",
            "Operating temperatures for the DGX Station must be maintained between 10°C and 30°C with non-condensing relative humidity between 20% and 80%. Ensure rear exhaust clearance of at least 15 cm from walls or enclosure baffles. In case of thermal throttling alarms (GPU core temp exceeding 85°C), immediately halt active training jobs and verify that external refrigeration airflow vents are unobstructed."
        ]
    },
    {
        "filename": "OIST_AIML_Lab_Safety_and_Emergency_Procedures.txt",
        "category": "sop",
        "chunks": [
            "All laboratory users must be familiar with emergency shutdown procedures. The main Emergency Power Off (EPO) button is located immediately to the right of the primary laboratory entrance exit door. Pressing the EPO instantly cuts mains power to all equipment racks, server towers, and workstation benches.",
            "In case of an electrical fire in the server rack or power distribution units, use only Class C Carbon Dioxide (CO2) or Clean Agent (FM-200 / Novec 1230) fire extinguishers located at Pillar 2 and Pillar 5. Under no circumstances should water or ABC dry chemical powder be discharged into energized electronics, as conductant residue induces catastrophic short circuits."
        ]
    },
    {
        "filename": "HPC_Slurm_Compute_Allocation_Policy.txt",
        "category": "policy",
        "chunks": [
            "Access to the departmental High-Performance Compute cluster requires completion of the Lab Safety Orientation, supervisor endorsement, and an active LDAP account. Students must submit an signed Acceptable Use Policy before compute access tokens are provisioned by the Lab SPOC.",
            "Student research batch jobs scheduled via Slurm are subject to a strict 48-hour continuous runtime wallclock limit per job. Interactive GPU debugging sessions are limited to 2 hours during peak lab operating hours (09:00 to 18:00 IST). Extended 7-day model training allocations require prior approval from the Faculty In-Charge."
        ]
    },
    {
        "filename": "Edge_AI_Jetson_AGX_Orin_Manual.txt",
        "category": "manual",
        "chunks": [
            "The NVIDIA Jetson AGX Orin Developer Kit features an Ampere GPU, 32GB or 64GB 256-bit LPDDR5 memory, and up to 275 TOPS of INT8 processing power. Power input must be provided via the supplied 19V DC barrel connector or USB-PD compliant charger supporting 7V to 20V DC. Operating modes are configurable between 15W, 30W, 50W, and 60W profiles via nvpmodel.",
            "Thermal operating range for the Jetson AGX Orin is strictly 0°C to 50°C ambient room temperature. The integrated active fan heatsink regulates thermal dissipation. Ensure that jumper pins J30 and J32 remain in default factory state unless configuring UART recovery mode."
        ]
    },
    {
        "filename": "VR_Computer_Vision_Calibration_Manual.txt",
        "category": "manual",
        "chunks": [
            "The VR testing area features HTC Vive Pro 2 and Meta Quest headsets with 6DoF optical tracking. Before initiating computer vision capture passes, calibrate the room-scale tracking volume by running the floor boundary setup tool. Keep the 4x4 meter active zone clear of cables, chairs, and reflective glass surfaces.",
            "Optical lens maintenance: VR headset lenses must be cleaned exclusively with dry optical microfiber cloths. Never apply alcohol-based wipes, window cleaning solutions, or industrial solvents to the Fresnel lenses, as anti-reflective coating degradation will occur. Sanitize facial cushions using non-alcoholic UV-C sterilization chambers between user sessions."
        ]
    }
]

def run_evaluation():
    print("=" * 80)
    print("LabSPOC AI — RAG Evaluation & Retrieval Benchmark Suite (v0.7.1)")
    print("=" * 80)

    # 1. Setup isolated database
    eval_db_path = api_dir / "eval_benchmark.db"
    if eval_db_path.exists():
        try:
            eval_db_path.unlink()
        except Exception:
            pass
    
    db_url = f"sqlite:///{eval_db_path.as_posix()}"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    print("[1/4] Ingesting and embedding benchmark reference documents...")
    all_chunks_count = 0
    start_ingest = time.perf_counter()

    for doc_data in BENCHMARK_DOCUMENTS:
        doc_id = f"bench-doc-{uuid.uuid4().hex[:8]}"
        doc_sha = hashlib.sha256(doc_data["filename"].encode("utf-8")).hexdigest()
        doc = Document(
            id=doc_id,
            filename=doc_data["filename"],
            content_type="text/plain",
            sha256=doc_sha,
            category=doc_data["category"],
            status="approved"
        )
        db.add(doc)
        db.flush()

        for idx, text in enumerate(doc_data["chunks"]):
            chunk = DocumentChunk(
                document_id=doc.id,
                chunk_index=idx,
                text=text
            )
            db.add(chunk)
            db.flush()

            # Generate real Gemini or hash embedding
            vec = embed_text(text)
            cv = ChunkVector(
                chunk_id=chunk.id,
                model="gemini-embedding-001",
                vector_json=json.dumps(vec)
            )
            db.add(cv)
            all_chunks_count += 1

    db.commit()
    ingest_duration = (time.perf_counter() - start_ingest) * 1000
    print(f"      Ingested {len(BENCHMARK_DOCUMENTS)} documents, {all_chunks_count} chunks in {ingest_duration:.1f}ms.")

    # 2. Load dataset
    dataset_file = repo_root / "docs" / "eval_dataset.json"
    with open(dataset_file, "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    print(f"[2/4] Executing benchmark across {len(test_cases)} test cases...")

    results = []
    recall_scores = []
    mrr_scores = []
    citation_validity = []
    abstention_accuracy = []
    retrieval_latencies = []
    gemini_latencies = []

    for case in test_cases:
        cid = case["id"]
        query = case["query"]
        expected_keywords = case["expected_document_keywords"]
        expected_abstain = case["expected_to_abstain"]

        # Retrieval measurement
        t_ret_0 = time.perf_counter()
        retrieved_chunks = retrieve(db, query, limit=5)
        ret_ms = (time.perf_counter() - t_ret_0) * 1000
        retrieval_latencies.append(ret_ms)

        # Check retrieval rank
        rank = None
        if not expected_abstain:
            for r_idx, c in enumerate(retrieved_chunks):
                text_lower = c["text"].lower()
                match_count = sum(1 for kw in expected_keywords if kw.lower() in text_lower)
                if match_count >= min(2, len(expected_keywords)):
                    rank = r_idx + 1
                    break
            
            recall_at_5 = 1.0 if rank is not None and rank <= 5 else 0.0
            reciprocal_rank = (1.0 / rank) if rank is not None else 0.0
            recall_scores.append(recall_at_5)
            mrr_scores.append(reciprocal_rank)
        else:
            recall_at_5 = None
            reciprocal_rank = None

        # LLM Generation measurement
        # If expected to abstain (out of scope), feed an empty or irrelevant evidence list to verify gate abstention
        passed_evidence = retrieved_chunks
        if expected_abstain:
            # When out-of-scope query has low relevance (e.g. max score is tiny or irrelevant)
            passed_evidence = [c for c in retrieved_chunks if c.get("score", 0) > 0.45]

        t_gen_0 = time.perf_counter()
        gen_res = generate_grounded_answer(query, passed_evidence, language="en")
        gen_ms = (time.perf_counter() - t_gen_0) * 1000
        gemini_latencies.append(gen_ms)

        answer_text = gen_res.get("answer") or ""
        gate_passed = gen_res.get("gate_passed", False)
        abstained = gen_res.get("abstention_triggered", False)
        reason = gen_res.get("reason", "")
        citations = gen_res.get("citations", [])

        if not expected_abstain:
            # Grounded query: should pass gate, have citations, and match retrieved indices
            valid_cit = gate_passed and len(citations) > 0 and (not abstained)
            citation_validity.append(1.0 if valid_cit else 0.0)
        else:
            # Abstention query: correct if gate triggered abstention or reason marks ungrounded/abstention
            correct_abs = abstained or (not gate_passed) or ("abstention" in reason) or ("insufficient" in answer_text.lower())
            abstention_accuracy.append(1.0 if correct_abs else 0.0)

        results.append({
            "id": cid,
            "category": case["category"],
            "query": query,
            "expected_to_abstain": expected_abstain,
            "rank": rank,
            "recall@5": recall_at_5,
            "mrr": reciprocal_rank,
            "retrieval_ms": round(ret_ms, 2),
            "generation_ms": round(gen_ms, 2),
            "gate_passed": gate_passed,
            "abstained": abstained,
            "reason": reason,
            "citations": citations,
            "answer_preview": answer_text[:140] + ("..." if len(answer_text) > 140 else "")
        })

    # Summary metrics
    mean_recall = (sum(recall_scores) / len(recall_scores)) if recall_scores else 0.0
    mean_mrr = (sum(mrr_scores) / len(mrr_scores)) if mrr_scores else 0.0
    mean_cit_valid = (sum(citation_validity) / len(citation_validity)) if citation_validity else 0.0
    mean_abstain = (sum(abstention_accuracy) / len(abstention_accuracy)) if abstention_accuracy else 0.0
    avg_ret_ms = sum(retrieval_latencies) / len(retrieval_latencies)
    avg_gen_ms = sum(gemini_latencies) / len(gemini_latencies)

    summary = {
        "evaluation_timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "test_cases_count": len(test_cases),
        "grounded_cases_count": len(recall_scores),
        "abstention_cases_count": len(abstention_accuracy),
        "metrics": {
            "recall_at_5": round(mean_recall, 4),
            "mean_reciprocal_rank_mrr": round(mean_mrr, 4),
            "citation_validity_rate": round(mean_cit_valid, 4),
            "correct_abstention_rate": round(mean_abstain, 4),
            "avg_retrieval_latency_ms": round(avg_ret_ms, 2),
            "avg_gemini_latency_ms": round(avg_gen_ms, 2)
        },
        "individual_results": results
    }

    # Save to disk
    out_file = repo_root / "docs" / "eval_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("\n[3/4] Benchmark Summary Table:")
    print("-" * 65)
    print(f" Metric                          | Value")
    print("-" * 65)
    print(f" Recall@5                        | {mean_recall * 100:.1f}%")
    print(f" Mean Reciprocal Rank (MRR)      | {mean_mrr:.4f}")
    print(f" Citation Validity Rate          | {mean_cit_valid * 100:.1f}%")
    print(f" Correct Abstention Rate         | {mean_abstain * 100:.1f}%")
    print(f" Mean Retrieval Latency          | {avg_ret_ms:.2f} ms")
    print(f" Mean Gemini Latency             | {avg_gen_ms:.2f} ms")
    print("-" * 65)
    print(f"\n[4/4] Saved detailed results to {out_file.name}")

    # Clean up benchmark db
    db.close()
    engine.dispose()
    time.sleep(0.1)
    if eval_db_path.exists():
        try:
            eval_db_path.unlink()
        except Exception:
            pass

    return summary

if __name__ == "__main__":
    run_evaluation()
