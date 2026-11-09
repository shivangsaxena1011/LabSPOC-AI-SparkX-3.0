"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import Link from "next/link";
import {
  Activity,
  ArrowRight,
  ArrowUpRight,
  BookOpen,
  Bot,
  Building2,
  CheckCircle2,
  ChevronRight,
  Clock,
  Download,
  ExternalLink,
  Eye,
  FileCheck2,
  FileText,
  FileUp,
  FlaskConical,
  HelpCircle,
  Image as ImageIcon,
  Layers,
  LayoutDashboard,
  Link2,
  Lock,
  LogOut,
  MapPin,
  RefreshCw,
  Search,
  Settings2,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  Trash2,
  UploadCloud,
  Users,
  Waypoints,
  X
} from "lucide-react";
import { api, API } from "@/lib/api";

const LabScene = dynamic(() => import("@/components/LabScene"), { ssr: false });

type Asset = {
  id: string;
  name: string;
  category: string;
  zone: string;
  description: string;
  manufacturer: string;
  model_number: string;
  specifications: Record<string, any>;
  source_reference: string;
  verified_at: string | null;
  photos?: { id: string; url: string; caption: string }[];
  linked_documents?: { document_id: string; filename: string; link_type: string; category: string }[];
};

type Project = {
  id: string;
  title: string;
  problem: string;
  methodology: string;
  technologies: string;
  outcomes: string;
  societal_impact: string;
  demo_url: string;
  author_name: string;
  author_type: string;
  approved: boolean;
  submitted_at: string;
};

type Doc = {
  id: string;
  filename: string;
  status: string;
  category: string;
  version: string;
  description: string;
  uploaded_at: string;
};

type SpatialZone = {
  id: string;
  name: string;
  description: string;
  floor: string;
  sort_order: number;
  verified: boolean;
  x: number;
  z: number;
  width: number;
  depth: number;
  asset_count: number;
  assets: Asset[];
};

type GraphData = {
  graph_type: string;
  node_count: number;
  edge_count: number;
  nodes: { id: string; raw_id: string; type: string; name: string; verified?: boolean; coordinates?: any }[];
  edges: { id?: number; source: string; target: string; relation: string }[];
};

const navigation = [
  ["Overview", LayoutDashboard],
  ["Virtual Lab", Building2],
  ["Knowledge", BookOpen],
  ["Projects", Waypoints],
  ["Analytics", Activity]
] as const;

export default function OperationsWorkspace() {
  const [section, setSection] = useState<string>("Overview");
  const [assets, setAssets] = useState<Asset[]>([]);
  const [spatialZones, setSpatialZones] = useState<SpatialZone[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [docs, setDocs] = useState<Doc[]>([]);
  const [analytics, setAnalytics] = useState<any>(null);
  const [graphData, setGraphData] = useState<GraphData | null>(null);

  const [selectedId, setSelectedId] = useState<string>("");
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<any>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  // Tour Planner State
  const [persona, setPersona] = useState("Academic visitor");
  const [duration, setDuration] = useState(5);
  const [tour, setTour] = useState<any>(null);

  // Authentication State
  const [adminUsername, setAdminUsername] = useState("admin");
  const [adminPassword, setAdminPassword] = useState("");
  const [adminKey, setAdminKey] = useState("");
  const [adminToken, setAdminToken] = useState("");
  const [authUser, setAuthUser] = useState<any>(null);
  const [authBusy, setAuthBusy] = useState(false);

  // Asset Creation Form
  const [newAssetId, setNewAssetId] = useState("");
  const [newAssetName, setNewAssetName] = useState("");
  const [newAssetZone, setNewAssetZone] = useState("Computing Bay");
  const [newAssetCategory, setNewAssetCategory] = useState("compute");
  const [newAssetDesc, setNewAssetDesc] = useState("");
  const [newAssetMfg, setNewAssetMfg] = useState("");
  const [newAssetModel, setNewAssetModel] = useState("");

  // Zone Layout Editing
  const [activeZoneId, setActiveZoneId] = useState("");
  const [zoneX, setZoneX] = useState<number>(0);
  const [zoneZ, setZoneZ] = useState<number>(0);
  const [zoneW, setZoneW] = useState<number>(2.0);
  const [zoneD, setZoneD] = useState<number>(1.5);

  // Document Upload & Inspection
  const [uploadCategory, setUploadCategory] = useState("manual");
  const [uploadVersion, setUploadVersion] = useState("1.0");
  const [uploadDesc, setUploadDesc] = useState("");
  const [uploadBusy, setUploadBusy] = useState(false);
  const [inspectDoc, setInspectDoc] = useState<any>(null);
  const [reindexResult, setReindexResult] = useState<any>(null);
  const [evalResult, setEvalResult] = useState<any>(null);

  // Graph Link Form
  const [linkAssetId, setLinkAssetId] = useState("");
  const [linkTargetId, setLinkTargetId] = useState("");
  const [linkType, setLinkType] = useState("manual");

  // Photo Upload
  const [photoAssetId, setPhotoAssetId] = useState("");
  const [photoCaption, setPhotoCaption] = useState("");
  const [photoFile, setPhotoFile] = useState<File | null>(null);

  const adminHeaders = (): Record<string, string> => {
    if (adminToken) return { Authorization: `Bearer ${adminToken}` };
    if (adminKey) return { "X-Admin-Key": adminKey };
    return {};
  };

  const isAuthorized = Boolean(adminToken || adminKey);

  useEffect(() => {
    refreshAll();
  }, []);

  async function refreshAll() {
    try {
      const [assetsData, sceneData, docsData, analyticsData, graphRes] = await Promise.all([
        api<Asset[]>("/api/assets"),
        api<any>("/api/spatial/scene"),
        api<Doc[]>("/api/knowledge/documents"),
        api<any>("/api/analytics/overview"),
        api<GraphData>("/api/graph/overview").catch(() => null)
      ]);

      setAssets(assetsData);
      setSpatialZones(sceneData.zones || []);
      setDocs(docsData);
      setAnalytics(analyticsData);
      if (graphRes) setGraphData(graphRes);

      // If authorized, also fetch all projects (including pending)
      if (adminToken || adminKey) {
        api<Project[]>("/api/projects/all", { headers: adminHeaders() })
          .then((p) => setProjects(p))
          .catch(() => {
            api<Project[]>("/api/projects").then((p) => setProjects(p));
          });
      } else {
        api<Project[]>("/api/projects").then((p) => setProjects(p));
      }
    } catch (e: any) {
      setError(e.message);
    }
  }

  async function login() {
    setAuthBusy(true);
    setError("");
    try {
      const result = await api<any>("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: adminUsername, password: adminPassword })
      });
      setAdminToken(result.access_token);
      setAuthUser(result.user);
      setAdminPassword("");
      await refreshAll();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setAuthBusy(false);
    }
  }

  function logout() {
    setAdminToken("");
    setAuthUser(null);
  }

  async function askQuestion(q = question) {
    if (!q.trim()) return;
    setBusy(true);
    setAnswer(null);
    setError("");
    try {
      const r = await api<any>("/api/assistant/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: q,
          hotspot_id: selectedId || null
        })
      });
      setAnswer(r);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  async function compileTour() {
    setBusy(true);
    setError("");
    try {
      const t = await api<any>("/api/tours/plan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          persona,
          agenda: "explore institutional artificial intelligence and lab infrastructure",
          duration_minutes: duration,
          interests: []
        })
      });
      setTour(t);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  async function registerAsset() {
    if (!newAssetId.trim() || !newAssetName.trim()) return;
    setBusy(true);
    setError("");
    try {
      await api("/api/assets", {
        method: "POST",
        headers: { "Content-Type": "application/json", ...adminHeaders() },
        body: JSON.stringify({
          id: newAssetId.trim(),
          name: newAssetName.trim(),
          zone: newAssetZone,
          category: newAssetCategory,
          description: newAssetDesc || "Verified institutional laboratory asset record.",
          manufacturer: newAssetMfg,
          model_number: newAssetModel,
          specifications: {},
          source_reference: "OIST Bhopal AI & ML Laboratory Inventory"
        })
      });
      setNewAssetId("");
      setNewAssetName("");
      setNewAssetDesc("");
      setNewAssetMfg("");
      setNewAssetModel("");
      await refreshAll();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  async function verifyAsset(id: string) {
    try {
      await api(`/api/assets/${id}/verify`, { method: "POST", headers: adminHeaders() });
      await refreshAll();
    } catch (e: any) {
      setError(e.message);
    }
  }

  async function deleteAsset(id: string) {
    if (!confirm(`Are you sure you want to delete asset ${id}?`)) return;
    try {
      await api(`/api/assets/${id}`, { method: "DELETE", headers: adminHeaders() });
      await refreshAll();
    } catch (e: any) {
      setError(e.message);
    }
  }

  async function saveZoneLayout() {
    if (!activeZoneId) return;
    setBusy(true);
    try {
      await api(`/api/zones/${activeZoneId}/layout`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json", ...adminHeaders() },
        body: JSON.stringify({ x: zoneX, z: zoneZ, width: zoneW, depth: zoneD })
      });
      await refreshAll();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  async function uploadDocument(file?: File) {
    if (!file) return;
    setUploadBusy(true);
    setError("");
    try {
      const fd = new FormData();
      fd.append("file", file);
      fd.append("category", uploadCategory);
      fd.append("version", uploadVersion);
      fd.append("description", uploadDesc);
      await api("/api/knowledge/upload", {
        method: "POST",
        headers: adminHeaders(),
        body: fd
      });
      await refreshAll();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setUploadBusy(false);
    }
  }

  async function approveDoc(id: string) {
    try {
      await api(`/api/knowledge/documents/${id}/approve`, { method: "POST", headers: adminHeaders() });
      await refreshAll();
    } catch (e: any) {
      setError(e.message);
    }
  }

  async function unapproveDoc(id: string) {
    try {
      await api(`/api/knowledge/documents/${id}/unapprove`, { method: "POST", headers: adminHeaders() });
      await refreshAll();
    } catch (e: any) {
      setError(e.message);
    }
  }

  async function deleteDoc(id: string) {
    if (!confirm("Are you sure you want to delete this document from the knowledge base?")) return;
    try {
      await api(`/api/knowledge/documents/${id}`, { method: "DELETE", headers: adminHeaders() });
      await refreshAll();
    } catch (e: any) {
      setError(e.message);
    }
  }

  async function inspectChunks(docId: string) {
    try {
      const details = await api<any>(`/api/knowledge/documents/${docId}`);
      setInspectDoc(details);
    } catch (e: any) {
      setError(e.message);
    }
  }

  async function rebuildIndex() {
    setBusy(true);
    try {
      const res = await api<any>("/api/knowledge/reindex", { method: "POST", headers: adminHeaders() });
      setReindexResult(res);
      await refreshAll();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  async function runOfflineEvaluation() {
    setBusy(true);
    try {
      // Benchmark cases against approved OIST laboratory docs
      const firstDoc = docs.find((d) => d.status === "approved");
      const cases = [
        {
          question: "What GPU compute workstations are available?",
          expected_document_ids: firstDoc ? [firstDoc.id] : []
        },
        {
          question: "What are the laboratory safety and SOP procedures?",
          expected_document_ids: firstDoc ? [firstDoc.id] : []
        }
      ];
      const res = await api<any>("/api/knowledge/evaluate", {
        method: "POST",
        headers: { "Content-Type": "application/json", ...adminHeaders() },
        body: JSON.stringify({ cases })
      });
      setEvalResult(res);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  async function approveProject(id: string) {
    try {
      await api(`/api/projects/${id}/approve`, { method: "POST", headers: adminHeaders() });
      await refreshAll();
    } catch (e: any) {
      setError(e.message);
    }
  }

  async function createGraphLink() {
    if (!linkAssetId || !linkTargetId) return;
    try {
      await api("/api/graph/links", {
        method: "POST",
        headers: { "Content-Type": "application/json", ...adminHeaders() },
        body: JSON.stringify({
          asset_id: linkAssetId,
          target_id: linkTargetId,
          link_type: linkType
        })
      });
      alert("SAEG link created successfully!");
      await refreshAll();
    } catch (e: any) {
      setError(e.message);
    }
  }

  async function uploadPhoto() {
    if (!photoAssetId || !photoFile) return;
    try {
      const fd = new FormData();
      fd.append("file", photoFile);
      fd.append("caption", photoCaption);
      await api(`/api/assets/${photoAssetId}/photos`, {
        method: "POST",
        headers: adminHeaders(),
        body: fd
      });
      setPhotoFile(null);
      setPhotoCaption("");
      alert("Photo uploaded successfully!");
      await refreshAll();
    } catch (e: any) {
      setError(e.message);
    }
  }

  const activeAsset = assets.find((a) => a.id === selectedId);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      {/* Top Navbar */}
      <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/95 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-700 text-white shadow-md">
              <FlaskConical size={20} />
            </div>
            <div>
              <div className="text-base font-bold tracking-tight text-slate-900">
                LabSPOC <span className="text-blue-700">AI</span>
              </div>
              <div className="text-[11px] font-medium text-slate-500">
                Institutional Operations & Intelligence Workspace · OIST Bhopal
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Link
              href="/visit"
              className="flex items-center gap-1.5 rounded-lg border border-blue-200 bg-blue-50 px-3 py-1.5 text-xs font-semibold text-blue-700 transition hover:bg-blue-100"
            >
              <Sparkles size={14} /> Visitor Experience ↗
            </Link>

            <button onClick={refreshAll} className="btn btn-secondary text-xs">
              <RefreshCw size={13} /> Refresh
            </button>

            {authUser ? (
              <div className="flex items-center gap-2 rounded-lg bg-emerald-50 px-3 py-1 text-xs text-emerald-800 font-semibold">
                <span>{authUser.username} ({authUser.role})</span>
                <button onClick={logout} title="Sign out" className="text-emerald-600 hover:text-emerald-900">
                  <LogOut size={13} />
                </button>
              </div>
            ) : (
              <button onClick={() => setSection("Knowledge")} className="btn btn-primary text-xs">
                <Lock size={13} /> Sign In
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Main Layout */}
      <div className="mx-auto grid max-w-7xl grid-cols-1 gap-6 px-4 py-6 sm:px-6 lg:grid-cols-[230px_1fr]">
        {/* Sidebar */}
        <aside className="panel h-fit p-3 space-y-1">
          <div className="px-3 pb-3 pt-2">
            <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Navigation</div>
            <div className="text-sm font-bold text-slate-800">Laboratory Operations</div>
          </div>

          {navigation.map(([name, Icon]) => (
            <button
              key={name}
              onClick={() => setSection(name)}
              className={`flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left text-xs font-semibold transition ${
                section === name
                  ? "bg-blue-50 text-blue-800 shadow-sm"
                  : "text-slate-600 hover:bg-slate-50"
              }`}
            >
              <Icon size={16} />
              <span>{name}</span>
              <ChevronRight className="ml-auto text-slate-300" size={14} />
            </button>
          ))}

          <div className="mt-6 rounded-xl bg-slate-50 p-3.5 space-y-2 border border-slate-100">
            <div className="flex items-center gap-1.5 text-xs font-bold text-slate-800">
              <ShieldCheck size={16} className="text-teal-700" />
              <span>Evidence-First AI</span>
            </div>
            <p className="text-[11px] leading-relaxed text-slate-500">
              Only verified equipment records and approved documents ground assistant answers.
            </p>
          </div>

          <div className="px-3 pt-3 text-[10px] text-slate-400">
            LabSPOC AI · Release 0.9.0
          </div>
        </aside>

        {/* Content Body */}
        <main className="min-w-0 space-y-6">
          {/* Section Header */}
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <div className="text-[10px] font-bold uppercase tracking-wider text-blue-700">
                OIST Smart Campus Platform
              </div>
              <h1 className="text-2xl font-bold tracking-tight text-slate-900">{section}</h1>
            </div>
            <div className="flex items-center gap-2 text-xs text-slate-500 font-medium">
              <span className="h-2 w-2 rounded-full bg-emerald-500" />
              <span>API Gateway Connected</span>
            </div>
          </div>

          {error && (
            <div className="flex items-center justify-between rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-xs text-rose-800">
              <span>{error}</span>
              <button onClick={() => setError("")}><X size={14} /></button>
            </div>
          )}

          {/* TAB 1: OVERVIEW */}
          {section === "Overview" && (
            <div className="space-y-6">
              {/* Stat Cards */}
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                {[
                  ["Registered Assets", assets.length, Building2, `${assets.filter((a) => a.verified_at).length} Verified`],
                  ["Approved Projects", projects.filter((p) => p.approved).length, Waypoints, `${projects.length} Total Submissions`],
                  ["Approved Documents", docs.filter((d) => d.status === "approved").length, FileText, `${docs.length} Uploaded`],
                  ["Recorded Visits", analytics?.total_sessions ?? 0, Users, `${analytics?.consented_sessions ?? 0} Consented`]
                ].map(([label, val, Icon, note]: any) => (
                  <div key={label} className="panel p-4">
                    <div className="flex items-center justify-between text-xs text-slate-500">
                      <span>{label}</span>
                      <Icon size={16} />
                    </div>
                    <div className="mt-2 text-2xl font-extrabold text-slate-900">{val}</div>
                    <div className="mt-1 text-[11px] text-slate-400 font-medium">{note}</div>
                  </div>
                ))}
              </div>

              {/* 3D Scene + Assistant */}
              <div className="grid gap-6 xl:grid-cols-[1.3fr_0.9fr]">
                <div className="panel p-5 space-y-3">
                  <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                    <div>
                      <h3 className="text-sm font-bold text-slate-800">Interactive Laboratory Digital Twin</h3>
                      <p className="text-xs text-slate-500">Click a zone block or equipment sphere to inspect records</p>
                    </div>
                    <span className="rounded-full bg-amber-50 px-2.5 py-1 text-[10px] font-semibold text-amber-700">
                      Illustrative Layout
                    </span>
                  </div>

                  <LabScene onSelect={(id) => setSelectedId(id)} zones={spatialZones} selectedId={selectedId} height="400px" />
                </div>

                <div className="panel p-5 space-y-3">
                  <div className="flex items-center gap-2 border-b border-slate-100 pb-2">
                    <Bot size={18} className="text-blue-700" />
                    <div>
                      <h3 className="text-sm font-bold text-slate-800">Lab Knowledge Assistant</h3>
                      <p className="text-xs text-slate-500">Test groundings against approved laboratory documents</p>
                    </div>
                  </div>

                  {activeAsset && (
                    <div className="rounded-lg border border-blue-200 bg-blue-50/70 p-2.5 text-xs">
                      <span className="font-semibold text-blue-900">Selected Hotspot:</span> {activeAsset.name} ({activeAsset.id})
                    </div>
                  )}

                  <div className="space-y-2">
                    <textarea
                      className="input min-h-[90px] text-xs py-2"
                      placeholder="Ask a technical or operational question..."
                      value={question}
                      onChange={(e) => setQuestion(e.target.value)}
                    />
                    <button
                      onClick={() => askQuestion()}
                      disabled={busy || !question.trim()}
                      className="btn btn-primary w-full justify-center text-xs"
                    >
                      {busy ? "Checking Evidence Gate..." : "Ask Assistant"}
                    </button>
                  </div>

                  {answer && (
                    <div className="mt-3 rounded-xl border border-slate-200 bg-slate-50 p-3 text-xs space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-slate-700">Response</span>
                        <span
                          className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                            answer.status === "answered_with_evidence"
                              ? "bg-emerald-100 text-emerald-800"
                              : "bg-amber-100 text-amber-800"
                          }`}
                        >
                          {answer.status?.replaceAll("_", " ")}
                        </span>
                      </div>
                      <p className="whitespace-pre-wrap leading-relaxed text-slate-800">{answer.answer}</p>
                      {answer.citations?.length > 0 && (
                        <div className="border-t border-slate-200 pt-1.5 text-[10px] text-blue-800 space-y-1">
                          <div className="font-bold uppercase tracking-wider text-slate-400">Sources</div>
                          {answer.citations.map((c: any, i: number) => (
                            <div key={i}>
                              [{i + 1}] {c.filename} {c.page ? `p.${c.page}` : ""} · {c.document_id.slice(0, 8)}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>

              {/* Tour Preview & Knowledge Readiness */}
              <div className="grid gap-6 sm:grid-cols-2">
                <div className="panel p-5 space-y-3">
                  <div className="flex items-center gap-2">
                    <Sparkles size={16} className="text-blue-700" />
                    <h3 className="text-sm font-bold text-slate-800">Agenda-to-Tour Compiler</h3>
                  </div>
                  <p className="text-xs text-slate-500">Preview persona-specific time-boxed itineraries.</p>

                  <div className="grid grid-cols-2 gap-3 text-xs">
                    <div>
                      <label className="font-semibold text-slate-600">Visitor Persona</label>
                      <select className="input mt-1" value={persona} onChange={(e) => setPersona(e.target.value)}>
                        <option>Academic visitor</option>
                        <option>Undergraduate student</option>
                        <option>Industry executive</option>
                        <option>Accreditation reviewer</option>
                      </select>
                    </div>
                    <div>
                      <label className="font-semibold text-slate-600">Duration</label>
                      <select className="input mt-1" value={duration} onChange={(e) => setDuration(Number(e.target.value))}>
                        <option value={2}>2 minutes</option>
                        <option value={5}>5 minutes</option>
                        <option value={15}>15 minutes</option>
                      </select>
                    </div>
                  </div>

                  <button onClick={compileTour} disabled={busy} className="btn btn-secondary w-full justify-center text-xs">
                    Compile Tour Itinerary
                  </button>

                  {tour && (
                    <div className="rounded-lg bg-slate-50 p-3 text-xs space-y-1.5 border border-slate-100">
                      <div className="font-bold text-slate-800">
                        {tour.status === "planned" ? `${tour.allocated_minutes} min of ${tour.duration_minutes} min allocated` : tour.message}
                      </div>
                      {tour.stops?.map((s: any, idx: number) => (
                        <div key={s.id} className="flex justify-between border-t border-slate-100 pt-1 text-[11px]">
                          <span>{idx + 1}. {s.title}</span>
                          <span className="font-semibold">{s.allocated_minutes} min</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <div className="panel p-5 space-y-3">
                  <div className="flex items-center gap-2">
                    <ShieldCheck size={16} className="text-teal-700" />
                    <h3 className="text-sm font-bold text-slate-800">Governance & Knowledge Readiness</h3>
                  </div>
                  <p className="text-xs text-slate-500">
                    Document approval is mandatory before chunks can ground AI responses.
                  </p>

                  <div className="rounded-xl bg-slate-50 p-4 border border-slate-100 flex items-center justify-between text-xs">
                    <div>
                      <span className="text-slate-500">Pending Review:</span>
                      <div className="text-xl font-bold text-amber-700">
                        {docs.filter((d) => d.status === "pending_review").length}
                      </div>
                    </div>
                    <div>
                      <span className="text-slate-500">Approved Sources:</span>
                      <div className="text-xl font-bold text-emerald-700">
                        {docs.filter((d) => d.status === "approved").length}
                      </div>
                    </div>
                  </div>

                  <button onClick={() => setSection("Knowledge")} className="btn btn-primary w-full justify-center text-xs">
                    Manage Documents & Approvals <ChevronRight size={14} />
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: VIRTUAL LAB & SPATIAL DIGITAL TWIN */}
          {section === "Virtual Lab" && (
            <div className="space-y-6">
              <div className="panel p-5 space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3">
                  <div>
                    <h3 className="text-sm font-bold text-slate-800">3D Laboratory Floor Plan & Zone Configuration</h3>
                    <p className="text-xs text-slate-500">Interactive scene layout synchronized with persistent coordinates</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs text-slate-600 font-semibold">
                      {spatialZones.length} Zones
                    </span>
                  </div>
                </div>

                <LabScene onSelect={(id) => setSelectedId(id)} zones={spatialZones} selectedId={selectedId} height="420px" />

                {/* Zone Geometry Editor */}
                {isAuthorized && (
                  <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700">
                        Configure Zone Spatial Coordinates (Admin)
                      </h4>
                      <select
                        className="input text-xs max-w-xs"
                        value={activeZoneId}
                        onChange={(e) => {
                          setActiveZoneId(e.target.value);
                          const z = spatialZones.find((x) => x.id === e.target.value);
                          if (z) {
                            setZoneX(z.x);
                            setZoneZ(z.z);
                            setZoneW(z.width);
                            setZoneD(z.depth);
                          }
                        }}
                      >
                        <option value="">Select Zone to Adjust...</option>
                        {spatialZones.map((z) => (
                          <option key={z.id} value={z.id}>
                            {z.name} ({z.id})
                          </option>
                        ))}
                      </select>
                    </div>

                    {activeZoneId && (
                      <div className="grid gap-3 sm:grid-cols-5 text-xs">
                        <div>
                          <label className="text-slate-500 font-medium">X Pos (-8 to 8)</label>
                          <input
                            type="number"
                            step="0.1"
                            className="input mt-1"
                            value={zoneX}
                            onChange={(e) => setZoneX(Number(e.target.value))}
                          />
                        </div>
                        <div>
                          <label className="text-slate-500 font-medium">Z Pos (-6 to 6)</label>
                          <input
                            type="number"
                            step="0.1"
                            className="input mt-1"
                            value={zoneZ}
                            onChange={(e) => setZoneZ(Number(e.target.value))}
                          />
                        </div>
                        <div>
                          <label className="text-slate-500 font-medium">Width (0.8 to 6)</label>
                          <input
                            type="number"
                            step="0.1"
                            className="input mt-1"
                            value={zoneW}
                            onChange={(e) => setZoneW(Number(e.target.value))}
                          />
                        </div>
                        <div>
                          <label className="text-slate-500 font-medium">Depth (0.8 to 5)</label>
                          <input
                            type="number"
                            step="0.1"
                            className="input mt-1"
                            value={zoneD}
                            onChange={(e) => setZoneD(Number(e.target.value))}
                          />
                        </div>
                        <div className="flex items-end">
                          <button onClick={saveZoneLayout} disabled={busy} className="btn btn-primary w-full text-xs">
                            Save Layout
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Equipment Hotspot Registry */}
              <div className="panel p-5 space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3">
                  <div>
                    <h3 className="text-sm font-bold text-slate-800">Equipment Hotspot Registry</h3>
                    <p className="text-xs text-slate-500">Database-backed laboratory assets and verified specifications</p>
                  </div>
                  <span className="text-xs text-slate-500">{assets.length} Assets Registered</span>
                </div>

                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {assets.map((a) => (
                    <div
                      key={a.id}
                      onClick={() => setSelectedId(a.id)}
                      className={`cursor-pointer rounded-xl border p-4 transition ${
                        selectedId === a.id
                          ? "border-blue-600 bg-blue-50/60 shadow-sm"
                          : "border-slate-200 bg-white hover:border-slate-300"
                      }`}
                    >
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-mono text-[10px] bg-slate-100 px-1.5 py-0.5 rounded text-slate-600">
                          {a.id}
                        </span>
                        <span
                          className={`rounded px-1.5 py-0.5 text-[10px] font-semibold ${
                            a.verified_at ? "bg-emerald-100 text-emerald-800" : "bg-amber-100 text-amber-800"
                          }`}
                        >
                          {a.verified_at ? "Verified" : "Unverified"}
                        </span>
                      </div>

                      <h4 className="mt-2 text-sm font-bold text-slate-900">{a.name}</h4>
                      <p className="mt-1 text-xs text-slate-500 line-clamp-2">{a.description}</p>

                      <div className="mt-2 flex items-center justify-between text-[11px] text-slate-400">
                        <span>Zone: {a.zone}</span>
                        <span className="capitalize">{a.category}</span>
                      </div>

                      {isAuthorized && (
                        <div className="mt-3 pt-2.5 border-t border-slate-100 flex gap-2 justify-end">
                          {!a.verified_at && (
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                verifyAsset(a.id);
                              }}
                              className="text-[11px] font-semibold text-emerald-700 hover:underline"
                            >
                              Verify
                            </button>
                          )}
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              deleteAsset(a.id);
                            }}
                            className="text-[11px] font-semibold text-rose-600 hover:underline"
                          >
                            Delete
                          </button>
                        </div>
                      )}
                    </div>
                  ))}
                </div>

                {/* Asset Registration Form */}
                {isAuthorized && (
                  <div className="mt-6 rounded-xl border border-slate-200 bg-slate-50 p-5 space-y-4">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700">
                      Register Verified Lab Equipment
                    </h4>

                    <div className="grid gap-3 sm:grid-cols-3 text-xs">
                      <input
                        className="input"
                        placeholder="Asset ID e.g. AIML-EQP-001"
                        value={newAssetId}
                        onChange={(e) => setNewAssetId(e.target.value)}
                      />
                      <input
                        className="input"
                        placeholder="Equipment Name"
                        value={newAssetName}
                        onChange={(e) => setNewAssetName(e.target.value)}
                      />
                      <input
                        className="input"
                        placeholder="Lab Zone e.g. Computing Bay"
                        value={newAssetZone}
                        onChange={(e) => setNewAssetZone(e.target.value)}
                      />
                      <input
                        className="input"
                        placeholder="Manufacturer e.g. NVIDIA"
                        value={newAssetMfg}
                        onChange={(e) => setNewAssetMfg(e.target.value)}
                      />
                      <input
                        className="input"
                        placeholder="Model e.g. DGX Station A100"
                        value={newAssetModel}
                        onChange={(e) => setNewAssetModel(e.target.value)}
                      />
                      <select
                        className="input"
                        value={newAssetCategory}
                        onChange={(e) => setNewAssetCategory(e.target.value)}
                      >
                        <option value="compute">Computing & GPU</option>
                        <option value="robotics">Robotics & Edge</option>
                        <option value="networking">Networking & Storage</option>
                        <option value="instrument">Instrumentation</option>
                      </select>
                    </div>

                    <textarea
                      className="input min-h-[60px] text-xs"
                      placeholder="Verified description and specifications..."
                      value={newAssetDesc}
                      onChange={(e) => setNewAssetDesc(e.target.value)}
                    />

                    <div className="flex justify-end">
                      <button
                        onClick={registerAsset}
                        disabled={busy || !newAssetId.trim() || !newAssetName.trim()}
                        className="btn btn-primary text-xs"
                      >
                        Register Asset Record
                      </button>
                    </div>
                  </div>
                )}
              </div>

              {/* Spatially Anchored Evidence Graph (SAEG - Innovation A) */}
              <div className="panel p-5 space-y-4">
                <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                  <div>
                    <h3 className="text-sm font-bold text-slate-800">
                      Spatially Anchored Evidence Graph (SAEG)
                    </h3>
                    <p className="text-xs text-slate-500">
                      Relational graph connecting Zone IDs ↔ Asset IDs ↔ Approved Documents ↔ Projects
                    </p>
                  </div>
                  {graphData && (
                    <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700">
                      {graphData.node_count} Nodes · {graphData.edge_count} Edges
                    </span>
                  )}
                </div>

                {isAuthorized && (
                  <div className="rounded-xl bg-slate-50 p-4 border border-slate-200 text-xs space-y-3">
                    <div className="font-bold text-slate-700">Link Equipment to Knowledge Document or Project</div>
                    <div className="grid gap-3 sm:grid-cols-4">
                      <select className="input" value={linkAssetId} onChange={(e) => setLinkAssetId(e.target.value)}>
                        <option value="">Select Equipment...</option>
                        {assets.map((a) => (
                          <option key={a.id} value={a.id}>
                            {a.name} ({a.id})
                          </option>
                        ))}
                      </select>

                      <select className="input" value={linkType} onChange={(e) => setLinkType(e.target.value)}>
                        <option value="manual">Manual Document</option>
                        <option value="sop">SOP Document</option>
                        <option value="spec_sheet">Spec Sheet</option>
                        <option value="project">Research Project</option>
                      </select>

                      <input
                        className="input"
                        placeholder="Target Doc ID or Project ID"
                        value={linkTargetId}
                        onChange={(e) => setLinkTargetId(e.target.value)}
                      />

                      <button onClick={createGraphLink} className="btn btn-primary text-xs">
                        Create SAEG Link
                      </button>
                    </div>
                  </div>
                )}

                {graphData && (
                  <div className="overflow-x-auto rounded-xl border border-slate-200">
                    <table className="min-w-full text-xs text-left">
                      <thead className="bg-slate-100 text-slate-700 font-semibold">
                        <tr>
                          <th className="p-3">Source Node</th>
                          <th className="p-3">Relationship</th>
                          <th className="p-3">Target Node</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 bg-white">
                        {graphData.edges.slice(0, 15).map((edge, i) => (
                          <tr key={i} className="hover:bg-slate-50">
                            <td className="p-3 font-mono font-medium text-slate-800">{edge.source}</td>
                            <td className="p-3">
                              <span className="rounded bg-blue-50 px-2 py-0.5 text-[10px] font-semibold text-blue-700">
                                {edge.relation}
                              </span>
                            </td>
                            <td className="p-3 font-mono text-slate-700">{edge.target}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 3: KNOWLEDGE & HYBRID RAG */}
          {section === "Knowledge" && (
            <div className="space-y-6">
              <div className="grid gap-6 xl:grid-cols-[0.8fr_1.2fr]">
                {/* Admin Auth & Upload Box */}
                <div className="space-y-6">
                  {/* Authentication Box */}
                  <div className="panel p-5 space-y-4">
                    <h3 className="text-sm font-bold text-slate-800">Administrator Access</h3>
                    <p className="text-xs text-slate-500">
                      Sign in with the configured administrator account to approve documents and manage records.
                    </p>

                    {authUser ? (
                      <div className="rounded-xl bg-emerald-50 p-4 border border-emerald-100 space-y-2">
                        <div className="flex items-center justify-between text-xs font-semibold text-emerald-800">
                          <span>Signed in as: {authUser.username}</span>
                          <span className="uppercase text-[10px] bg-emerald-200 px-2 py-0.5 rounded">
                            {authUser.role}
                          </span>
                        </div>
                        <button onClick={logout} className="text-xs font-semibold text-emerald-700 underline">
                          Sign out
                        </button>
                      </div>
                    ) : (
                      <div className="space-y-3 text-xs">
                        <div>
                          <label className="text-slate-600 font-medium">Username</label>
                          <input
                            className="input mt-1"
                            value={adminUsername}
                            onChange={(e) => setAdminUsername(e.target.value)}
                          />
                        </div>
                        <div>
                          <label className="text-slate-600 font-medium">Password</label>
                          <input
                            type="password"
                            className="input mt-1"
                            value={adminPassword}
                            onChange={(e) => setAdminPassword(e.target.value)}
                          />
                        </div>
                        <button
                          onClick={login}
                          disabled={authBusy || adminPassword.length < 8}
                          className="btn btn-primary w-full justify-center"
                        >
                          {authBusy ? "Authenticating..." : "Sign In with Credentials"}
                        </button>

                        <div className="border-t border-slate-100 pt-2 text-[11px] text-slate-500">
                          Or enter legacy API key:
                          <input
                            type="password"
                            placeholder="ADMIN_API_KEY"
                            className="input mt-1 text-xs"
                            value={adminKey}
                            onChange={(e) => setAdminKey(e.target.value)}
                          />
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Upload Knowledge Document */}
                  <div className="panel p-5 space-y-4">
                    <h3 className="text-sm font-bold text-slate-800">Add Authorized Knowledge</h3>
                    <p className="text-xs text-slate-500">
                      Upload manuals, SOPs, specifications, or research papers. Files enter pending review.
                    </p>

                    <div className="space-y-3 text-xs">
                      <div>
                        <label className="font-semibold text-slate-600">Document Category</label>
                        <select
                          className="input mt-1"
                          value={uploadCategory}
                          onChange={(e) => setUploadCategory(e.target.value)}
                        >
                          <option value="manual">Equipment Manual</option>
                          <option value="sop">Standard Operating Procedure (SOP)</option>
                          <option value="specification">Technical Specification</option>
                          <option value="research">Research Publication</option>
                          <option value="policy">Lab Policy & Safety</option>
                        </select>
                      </div>

                      <div className="grid grid-cols-2 gap-2">
                        <div>
                          <label className="font-semibold text-slate-600">Version</label>
                          <input
                            className="input mt-1"
                            placeholder="1.0"
                            value={uploadVersion}
                            onChange={(e) => setUploadVersion(e.target.value)}
                          />
                        </div>
                        <div>
                          <label className="font-semibold text-slate-600">Description</label>
                          <input
                            className="input mt-1"
                            placeholder="Brief summary..."
                            value={uploadDesc}
                            onChange={(e) => setUploadDesc(e.target.value)}
                          />
                        </div>
                      </div>

                      <label className="flex cursor-pointer flex-col items-center rounded-xl border border-dashed border-slate-300 bg-slate-50 p-6 text-center hover:bg-slate-100 transition">
                        <UploadCloud size={30} className="text-blue-700 mb-1" />
                        <span className="text-xs font-semibold text-slate-800">Choose File to Ingest</span>
                        <span className="text-[10px] text-slate-500">PDF, DOCX, TXT, MD (Max 25MB)</span>
                        <input
                          type="file"
                          accept=".pdf,.docx,.txt,.md"
                          className="hidden"
                          onChange={(e) => uploadDocument(e.target.files?.[0])}
                        />
                      </label>

                      {uploadBusy && (
                        <div className="text-center text-xs font-semibold text-blue-700 animate-pulse">
                          Extracting text, chunking, and computing embeddings...
                        </div>
                      )}

                      <button
                        onClick={rebuildIndex}
                        disabled={!isAuthorized || busy}
                        className="btn btn-secondary w-full justify-center text-xs"
                      >
                        Rebuild Semantic Vector Index
                      </button>

                      {reindexResult && (
                        <div className="rounded-lg bg-slate-100 p-2.5 text-[11px] text-slate-700">
                          {reindexResult.new_vectors_created} vectors indexed · {reindexResult.embedding_unavailable} unavailable
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* Document Registry Table */}
                <div className="panel p-5 space-y-4">
                  <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3">
                    <div>
                      <h3 className="text-sm font-bold text-slate-800">Knowledge Document Registry</h3>
                      <p className="text-xs text-slate-500">Approved records ground the RAG assistant</p>
                    </div>
                    <span className="text-xs text-slate-500">{docs.length} Documents</span>
                  </div>

                  <div className="space-y-3">
                    {docs.map((d) => (
                      <div
                        key={d.id}
                        className="flex flex-wrap items-center justify-between rounded-xl border border-slate-200 p-3.5 hover:bg-slate-50 transition"
                      >
                        <div className="min-w-0 pr-3 space-y-1">
                          <div className="font-semibold text-xs text-slate-900 truncate">{d.filename}</div>
                          <div className="flex items-center gap-2 text-[10px] text-slate-400">
                            <span className="font-mono">{d.id.slice(0, 8)}</span>
                            <span>·</span>
                            <span className="capitalize">{d.category}</span>
                            <span>·</span>
                            <span>v{d.version}</span>
                            <span>·</span>
                            <span>{new Date(d.uploaded_at).toLocaleDateString()}</span>
                          </div>
                        </div>

                        <div className="flex items-center gap-2">
                          <span
                            className={`rounded-full px-2.5 py-0.5 text-[10px] font-semibold ${
                              d.status === "approved"
                                ? "bg-emerald-100 text-emerald-800"
                                : "bg-amber-100 text-amber-800"
                            }`}
                          >
                            {d.status.replaceAll("_", " ")}
                          </span>

                          <button
                            onClick={() => inspectChunks(d.id)}
                            className="btn btn-secondary text-[11px] py-1 px-2.5"
                          >
                            <Eye size={12} /> Chunks
                          </button>

                          {isAuthorized && (
                            <>
                              {d.status === "pending_review" ? (
                                <button
                                  onClick={() => approveDoc(d.id)}
                                  className="text-[11px] font-semibold text-emerald-700 hover:underline"
                                >
                                  Approve
                                </button>
                              ) : (
                                <button
                                  onClick={() => unapproveDoc(d.id)}
                                  className="text-[11px] font-semibold text-amber-700 hover:underline"
                                >
                                  Revoke
                                </button>
                              )}
                              <button
                                onClick={() => deleteDoc(d.id)}
                                className="text-[11px] font-semibold text-rose-600 hover:underline"
                              >
                                <Trash2 size={13} />
                              </button>
                            </>
                          )}
                        </div>
                      </div>
                    ))}

                    {docs.length === 0 && (
                      <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50 p-8 text-center text-xs text-slate-400">
                        No documents uploaded yet. Upload institutional manuals or SOPs.
                      </div>
                    )}
                  </div>

                  {/* Offline Retrieval Evaluation */}
                  <div className="mt-6 pt-4 border-t border-slate-100 space-y-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="text-xs font-bold text-slate-800">RAG Retrieval Evaluation (Recall@K & MRR)</h4>
                        <p className="text-[11px] text-slate-500">Benchmark hybrid semantic + lexical retrieval performance</p>
                      </div>
                      <button
                        onClick={runOfflineEvaluation}
                        disabled={!isAuthorized || busy}
                        className="btn btn-secondary text-xs"
                      >
                        Run Benchmark
                      </button>
                    </div>

                    {evalResult && (
                      <div className="rounded-xl bg-slate-50 p-4 border border-slate-200 text-xs space-y-2">
                        <div className="grid grid-cols-3 gap-2 font-semibold">
                          <div>Evaluated Cases: <b>{evalResult.evaluated_cases}</b></div>
                          <div>Recall@{evalResult.k}: <b>{evalResult.recall_at_k ?? "N/A"}</b></div>
                          <div>MRR: <b>{evalResult.mrr ? Number(evalResult.mrr).toFixed(3) : "N/A"}</b></div>
                        </div>
                        <p className="text-[10px] text-slate-400">{evalResult.warning}</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Chunk Inspector Modal */}
              {inspectDoc && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm">
                  <div className="w-full max-w-2xl rounded-2xl bg-white p-6 shadow-xl space-y-4 max-h-[85vh] flex flex-col">
                    <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                      <div>
                        <h3 className="text-sm font-bold text-slate-900">{inspectDoc.filename}</h3>
                        <p className="text-xs text-slate-500">{inspectDoc.chunk_count} Chunks Indexed</p>
                      </div>
                      <button onClick={() => setInspectDoc(null)}><X size={18} /></button>
                    </div>

                    <div className="overflow-y-auto space-y-3 flex-1 pr-1">
                      {inspectDoc.chunks?.map((c: any) => (
                        <div key={c.id} className="rounded-lg border border-slate-100 bg-slate-50 p-3 text-xs space-y-1">
                          <div className="text-[10px] font-bold text-slate-400">
                            Chunk #{c.index} · Page {c.page ?? "N/A"}
                          </div>
                          <p className="text-slate-700 leading-relaxed">{c.text}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB 4: PROJECTS (Module 4) */}
          {section === "Projects" && (
            <div className="space-y-6">
              <div className="panel p-5 space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3">
                  <div>
                    <h3 className="text-sm font-bold text-slate-800">Student & Faculty Research Submissions</h3>
                    <p className="text-xs text-slate-500">
                      Review and publish project records to the visitor demonstrator gallery
                    </p>
                  </div>
                  <span className="text-xs text-slate-500">{projects.length} Total Submissions</span>
                </div>

                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {projects.map((p) => (
                    <div key={p.id} className="rounded-xl border border-slate-200 bg-white p-4 space-y-3 shadow-sm">
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-mono text-[10px] bg-slate-100 px-1.5 py-0.5 rounded text-slate-600">
                          {p.id}
                        </span>
                        <span
                          className={`rounded px-1.5 py-0.5 text-[10px] font-semibold ${
                            p.approved ? "bg-emerald-100 text-emerald-800" : "bg-amber-100 text-amber-800"
                          }`}
                        >
                          {p.approved ? "Approved" : "Pending Review"}
                        </span>
                      </div>

                      <h4 className="text-sm font-bold text-slate-900 leading-snug">{p.title}</h4>
                      <p className="text-xs text-slate-600 line-clamp-3">{p.problem}</p>

                      <div className="text-[11px] text-slate-500 space-y-1 border-t border-slate-100 pt-2">
                        <div>Author: <b className="text-slate-700">{p.author_name}</b> ({p.author_type})</div>
                        <div>Tech: <span className="font-medium text-blue-700">{p.technologies}</span></div>
                      </div>

                      <div className="flex items-center justify-between pt-2 border-t border-slate-100">
                        {p.demo_url ? (
                          <a
                            href={p.demo_url}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-flex items-center gap-1 text-xs text-blue-700 hover:underline"
                          >
                            Demo <ExternalLink size={12} />
                          </a>
                        ) : (
                          <span className="text-[10px] text-slate-400">No URL</span>
                        )}

                        {isAuthorized && !p.approved && (
                          <button
                            onClick={() => approveProject(p.id)}
                            className="btn btn-primary text-[11px] py-1 px-3"
                          >
                            Approve
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* TAB 5: ANALYTICS (Module 5) */}
          {section === "Analytics" && (
            <div className="space-y-6">
              <div className="panel p-5 space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3">
                  <div>
                    <h3 className="text-sm font-bold text-slate-800">Visitor Engagement & Analytics Overview</h3>
                    <p className="text-xs text-slate-500">
                      Consent-aware aggregation of visitor tours, hotspots inspected, and question topics
                    </p>
                  </div>
                  <a
                    href={`${API}/api/analytics/export`}
                    target="_blank"
                    className="btn btn-secondary text-xs"
                  >
                    <Download size={13} /> Export JSON
                  </a>
                </div>

                <div className="grid gap-4 sm:grid-cols-3">
                  <div className="rounded-xl bg-slate-50 p-4 border border-slate-100">
                    <span className="text-xs text-slate-500">Total Recorded Visits</span>
                    <div className="mt-1 text-2xl font-extrabold text-slate-900">{analytics?.total_sessions ?? 0}</div>
                  </div>
                  <div className="rounded-xl bg-slate-50 p-4 border border-slate-100">
                    <span className="text-xs text-slate-500">Consented Sessions</span>
                    <div className="mt-1 text-2xl font-extrabold text-emerald-700">{analytics?.consented_sessions ?? 0}</div>
                  </div>
                  <div className="rounded-xl bg-slate-50 p-4 border border-slate-100">
                    <span className="text-xs text-slate-500">Consent Rate</span>
                    <div className="mt-1 text-2xl font-extrabold text-blue-700">
                      {analytics?.consent_rate_percent ?? 0}%
                    </div>
                  </div>
                </div>

                {/* Frequently Asked Question Topics */}
                {analytics?.frequently_asked_topics && (
                  <div className="space-y-2 pt-3">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700">
                      Frequently Asked Question Topics
                    </h4>
                    <div className="divide-y divide-slate-100 rounded-xl border border-slate-200 bg-white">
                      {analytics.frequently_asked_topics.map((faq: any, i: number) => (
                        <div key={i} className="flex justify-between p-3 text-xs">
                          <span className="font-medium text-slate-800 capitalize">{faq.topic}</span>
                          <span className="font-bold text-blue-700">{faq.count} inquiries</span>
                        </div>
                      ))}
                      {analytics.frequently_asked_topics.length === 0 && (
                        <div className="p-4 text-center text-xs text-slate-400">No question topics clustered yet.</div>
                      )}
                    </div>
                  </div>
                )}

                {/* Event Breakdown */}
                <div className="space-y-2 pt-3">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700">Recorded Event Types</h4>
                  <div className="divide-y divide-slate-100 rounded-xl border border-slate-200 bg-white">
                    {analytics?.events?.map((e: any, i: number) => (
                      <div key={i} className="flex justify-between p-3 text-xs">
                        <span className="text-slate-700">
                          {e.type} · <span className="font-mono text-slate-500">{e.target || "general"}</span>
                        </span>
                        <span className="font-semibold text-slate-900">{e.count}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white py-6 text-center text-xs text-slate-400">
        <div className="mx-auto max-w-7xl px-4 sm:px-6">
          LabSPOC AI · SPARKX 3.0 Release 0.9.0 · AI & ML Laboratory, Oriental Institute of Science & Technology
        </div>
      </footer>
    </div>
  );
}
