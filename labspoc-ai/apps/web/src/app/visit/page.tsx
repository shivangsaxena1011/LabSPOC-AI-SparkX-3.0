"use client";

import { useEffect, useState, useRef } from "react";
import Link from "next/link";
import dynamic from "next/dynamic";
import {
  ArrowLeft,
  ArrowRight,
  Bot,
  Building2,
  CheckCircle2,
  Clock3,
  ExternalLink,
  FileCheck2,
  FileQuestion,
  FlaskConical,
  Globe2,
  Image as ImageIcon,
  Layers,
  MapPin,
  Mic,
  MicOff,
  PlusCircle,
  RotateCcw,
  Send,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  User,
  Volume2,
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
  diagram_url: string;
  linked_assets?: { id: string; name: string; zone: string }[];
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

type ChatMessage = {
  id: string;
  sender: "visitor" | "assistant";
  text: string;
  timestamp: string;
  citations?: { document_id: string; filename: string; page: number | null }[];
  evidence_gate?: {
    verified_grounding: boolean;
    abstention_triggered: boolean;
    gate_reason: string;
    citations_validated?: number[];
  };
  status?: string;
  asset?: Asset | null;
};

type SpeechRecognitionLike = {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  onresult: ((event: any) => void) | null;
  onerror: ((event: any) => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
};

declare global {
  interface Window {
    SpeechRecognition?: new () => SpeechRecognitionLike;
    webkitSpeechRecognition?: new () => SpeechRecognitionLike;
  }
}

const languages = [
  { code: "en", label: "English", speech: "en-IN" },
  { code: "hi", label: "हिन्दी (Hindi)", speech: "hi-IN" },
  { code: "bn", label: "বাংলা (Bengali)", speech: "bn-IN" },
  { code: "ta", label: "தமிழ் (Tamil)", speech: "ta-IN" },
  { code: "te", label: "తెలుగు (Telugu)", speech: "te-IN" },
  { code: "mr", label: "मराठी (Marathi)", speech: "mr-IN" }
];

export default function VisitorExperience() {
  const [persona, setPersona] = useState("Undergraduate student");
  const [agenda, setAgenda] = useState("Explore AI & ML laboratory workstations, compute clusters, and student projects");
  const [duration, setDuration] = useState(5);
  const [language, setLanguage] = useState("en");
  const [consent, setConsent] = useState(true);
  const [session, setSession] = useState<string | null>(null);

  const [assets, setAssets] = useState<Asset[]>([]);
  const [spatialZones, setSpatialZones] = useState<SpatialZone[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedAssetId, setSelectedAssetId] = useState<string>("");
  const [tour, setTour] = useState<any>(null);

  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [busy, setBusy] = useState(false);
  const [listening, setListening] = useState(false);
  const [summary, setSummary] = useState<any>(null);
  const [error, setError] = useState("");
  const [projectModalOpen, setProjectModalOpen] = useState(false);

  // New project submission form
  const [subTitle, setSubTitle] = useState("");
  const [subProblem, setSubProblem] = useState("");
  const [subMethod, setSubMethod] = useState("");
  const [subTech, setSubTech] = useState("");
  const [subOutcomes, setSubOutcomes] = useState("");
  const [subDemo, setSubDemo] = useState("");
  const [subAuthor, setSubAuthor] = useState("");
  const [subAuthorType, setSubAuthorType] = useState("student");
  const [subMessage, setSubMessage] = useState("");

  const chatBottomRef = useRef<HTMLDivElement>(null);
  const langConfig = languages.find((x) => x.code === language) || languages[0];

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function loadData() {
    try {
      const [assetsData, projectsData, sceneData] = await Promise.all([
        api<Asset[]>("/api/assets"),
        api<Project[]>("/api/projects"),
        api<any>("/api/spatial/scene")
      ]);
      setAssets(assetsData);
      setProjects(projectsData);
      setSpatialZones(sceneData.zones || []);
    } catch (e: any) {
      setError(e.message);
    }
  }

  async function recordEvent(type: string, target = "") {
    if (!session) return;
    try {
      await api(`/api/visits/${session}/events`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ event_type: type, target_id: target })
      });
    } catch {}
  }

  async function startVisit() {
    setBusy(true);
    setError("");
    try {
      const v: any = await api("/api/visits", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          persona,
          agenda,
          duration_minutes: duration,
          consent_analytics: consent
        })
      });
      setSession(v.id);
      setSummary(null);
      setMessages([
        {
          id: "welcome-1",
          sender: "assistant",
          text: `Welcome to the AI & ML Laboratory at Oriental Institute of Science & Technology (OIST), Bhopal. I am LabSPOC, your virtual lab ambassador. I have initialized a ${duration}-minute visit itinerary configured for your profile (${persona}). You can explore the 3D digital twin below or ask any question about laboratory equipment, safety procedures, or research projects!`,
          timestamp: new Date().toLocaleTimeString()
        }
      ]);
      await generateTour(v.id);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  async function generateTour(sessionId = session) {
    if (!sessionId) return;
    setBusy(true);
    try {
      const r: any = await api("/api/tours/plan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          persona,
          agenda,
          duration_minutes: duration,
          interests: [],
          session_id: sessionId
        })
      });
      setTour(r);
      if (r.status === "planned") {
        await recordEvent("tour_started", persona);
      }
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  async function sendQuery() {
    if (!question.trim()) return;
    const currentQ = question;
    setQuestion("");
    setBusy(true);

    const userMsg: ChatMessage = {
      id: `u-${Date.now()}`,
      sender: "visitor",
      text: currentQ,
      timestamp: new Date().toLocaleTimeString()
    };
    setMessages((prev) => [...prev, userMsg]);

    try {
      const r: any = await api("/api/assistant/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: currentQ,
          session_id: session,
          hotspot_id: selectedAssetId || null,
          language
        })
      });

      const assistantMsg: ChatMessage = {
        id: `a-${Date.now()}`,
        sender: "assistant",
        text: r.answer,
        timestamp: new Date().toLocaleTimeString(),
        citations: r.citations,
        evidence_gate: r.evidence_gate,
        status: r.status,
        asset: r.asset
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  function handleVoiceInput() {
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Recognition) {
      setError("Speech recognition is not supported in this browser. Please try Google Chrome or Microsoft Edge.");
      return;
    }
    const rec = new Recognition();
    rec.lang = langConfig.speech;
    rec.continuous = false;
    rec.interimResults = false;
    rec.onresult = (e) => {
      const text = e.results?.[0]?.[0]?.transcript || "";
      setQuestion(text);
    };
    rec.onerror = () => {
      setError("Microphone input was unavailable. Please grant microphone access.");
      setListening(false);
    };
    rec.onend = () => setListening(false);
    setListening(true);
    rec.start();
  }

  function handleSpeak(text: string) {
    if (!text || !("speechSynthesis" in window)) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = langConfig.speech;
    window.speechSynthesis.speak(utterance);
  }

  async function finishVisit() {
    if (!session) return;
    setBusy(true);
    try {
      await recordEvent("tour_completed", persona);
      const s = await api(`/api/visits/${session}/summary`);
      setSummary(s);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  async function submitProject(e: React.FormEvent) {
    e.preventDefault();
    if (!subTitle.trim() || !subProblem.trim()) return;
    setBusy(true);
    setSubMessage("");
    try {
      const res: any = await api("/api/projects/submit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: subTitle,
          problem: subProblem,
          methodology: subMethod,
          technologies: subTech,
          outcomes: subOutcomes,
          demo_url: subDemo,
          author_name: subAuthor,
          author_type: subAuthorType
        })
      });
      setSubMessage(res.message);
      setSubTitle("");
      setSubProblem("");
      setSubMethod("");
      setSubTech("");
      setSubOutcomes("");
      setSubDemo("");
      setSubAuthor("");
      setTimeout(() => {
        setProjectModalOpen(false);
        setSubMessage("");
      }, 2500);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  const activeAsset = assets.find((a) => a.id === selectedAssetId);

  return (
    <main className="min-h-screen bg-slate-50 text-slate-900">
      {/* Top Navigation */}
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
                Virtual Lab Ambassador · AI & ML Laboratory, OIST Bhopal
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="hidden sm:flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs text-slate-600">
              <span className="h-2 w-2 rounded-full bg-emerald-500" />
              <span>SPARKX 3.0 Live Ambassador</span>
            </div>
            <Link
              href="/"
              className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50 hover:text-blue-700"
            >
              <ArrowLeft size={14} /> Operations Workspace
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Banner */}
      <div className="border-b border-slate-200 bg-gradient-to-br from-slate-900 via-blue-950 to-indigo-950 px-4 py-8 text-white sm:px-6">
        <div className="mx-auto max-w-7xl">
          <div className="max-w-3xl space-y-3">
            <div className="inline-flex items-center gap-2 rounded-full border border-blue-400/30 bg-blue-500/10 px-3 py-1 text-xs font-medium text-blue-300">
              <Sparkles size={14} /> SPARKX 3.0 INTERNATIONAL INNOVATION CHALLENGE
            </div>
            <h1 className="text-3xl font-extrabold tracking-tight sm:text-4xl">
              Spatially Grounded <span className="text-blue-400">Virtual Lab Ambassador</span>
            </h1>
            <p className="text-sm leading-relaxed text-slate-300">
              Explore the Artificial Intelligence & Machine Learning Laboratory at Oriental Institute of
              Science & Technology. Tour the 3D digital twin, inspect verified equipment hotspots, and ask
              questions strictly grounded in approved institutional evidence.
            </p>
          </div>
        </div>
      </div>

      {error && (
        <div className="mx-auto max-w-7xl px-4 pt-4 sm:px-6">
          <div className="flex items-center justify-between rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">
            <span>{error}</span>
            <button onClick={() => setError("")} className="text-rose-600 hover:text-rose-800">
              <X size={16} />
            </button>
          </div>
        </div>
      )}

      {/* Main Container */}
      <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 space-y-8">
        {/* Onboarding & Personalization Row */}
        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-4">
            <div className="flex items-center gap-2">
              <User className="text-blue-700" size={18} />
              <h2 className="text-sm font-bold text-slate-800">Personalize Your Visit</h2>
            </div>
            {session && (
              <div className="flex items-center gap-1.5 rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700">
                <CheckCircle2 size={14} /> Session Active: {session.slice(0, 8)}
              </div>
            )}
          </div>

          <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div>
              <label className="text-xs font-semibold text-slate-600">Visitor Profile</label>
              <select
                className="input mt-1"
                value={persona}
                onChange={(e) => setPersona(e.target.value)}
              >
                <option>Undergraduate student</option>
                <option>Academic visitor</option>
                <option>Industry executive</option>
                <option>Research scientist</option>
                <option>Accreditation reviewer</option>
              </select>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-600">Preferred Language</label>
              <select
                className="input mt-1"
                value={language}
                onChange={(e) => {
                  setLanguage(e.target.value);
                  if (session) recordEvent("language_changed", e.target.value);
                }}
              >
                {languages.map((l) => (
                  <option key={l.code} value={l.code}>
                    {l.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-600">Available Time</label>
              <select
                className="input mt-1"
                value={duration}
                onChange={(e) => setDuration(Number(e.target.value))}
              >
                <option value={2}>2-minute quick introduction</option>
                <option value={5}>5-minute guided tour</option>
                <option value={15}>15-minute deep dive</option>
              </select>
            </div>

            <div className="flex flex-col justify-end">
              <button
                onClick={startVisit}
                disabled={busy}
                className="btn btn-primary h-[38px] w-full justify-center"
              >
                {session ? <RotateCcw size={14} /> : <ArrowRight size={14} />}
                {session ? "Update Visit Profile" : "Start Guided Visit"}
              </button>
            </div>
          </div>

          <div className="mt-3 flex items-center justify-between text-xs text-slate-500">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={consent}
                onChange={(e) => setConsent(e.target.checked)}
                className="rounded border-slate-300 text-blue-600"
              />
              <span>Consent to anonymous visit analytics for experience optimization</span>
            </label>
            <span className="text-[11px] text-slate-400">OIST AI & ML Laboratory Profile</span>
          </div>
        </section>

        {/* 3D Digital Twin & Equipment Inspector */}
        <section className="grid gap-6 lg:grid-cols-[1.4fr_0.9fr]">
          <div className="space-y-4">
            <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3">
                <div className="flex items-center gap-2">
                  <Building2 size={18} className="text-blue-700" />
                  <h2 className="text-sm font-bold text-slate-800">Interactive 3D Laboratory Scene</h2>
                </div>
                <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-[11px] text-slate-600 font-medium">
                  {assets.length} Assets Registered
                </span>
              </div>

              <div className="mt-4">
                <LabScene
                  onSelect={(id, isZone) => {
                    setSelectedAssetId(id);
                    recordEvent(isZone ? "zone_view" : "hotspot_select", id);
                  }}
                  zones={spatialZones}
                  selectedId={selectedAssetId}
                  height="440px"
                />
              </div>

              <div className="mt-3 flex flex-wrap items-center justify-between text-xs text-slate-500">
                <span>Click any zone block or equipment sphere to inspect details. Drag to orbit, scroll to zoom.</span>
                <span className="font-medium text-blue-700">OIST Bhopal AI Lab</span>
              </div>
            </div>

            {/* Generated Tour Itinerary */}
            {tour && tour.stops && tour.stops.length > 0 && (
              <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                  <div className="flex items-center gap-2">
                    <Clock3 className="text-blue-700" size={17} />
                    <h3 className="text-sm font-bold text-slate-800">
                      Agenda-to-Tour Itinerary · {tour.allocated_minutes} min allocated
                    </h3>
                  </div>
                  <span className="text-xs text-slate-500 font-medium">{persona}</span>
                </div>

                <div className="mt-4 grid gap-3 sm:grid-cols-2 md:grid-cols-3">
                  {tour.stops.map((stop: any, idx: number) => (
                    <div
                      key={stop.id}
                      onClick={() => {
                        setSelectedAssetId(stop.id);
                        recordEvent("hotspot_select", stop.id);
                      }}
                      className={`cursor-pointer rounded-xl border p-3.5 transition-all hover:border-blue-300 hover:shadow-sm ${
                        selectedAssetId === stop.id
                          ? "border-blue-600 bg-blue-50/70"
                          : "border-slate-200 bg-white"
                      }`}
                    >
                      <div className="flex items-center justify-between text-xs">
                        <span className="flex h-5 w-5 items-center justify-center rounded-full bg-blue-100 font-bold text-blue-800 text-[10px]">
                          {idx + 1}
                        </span>
                        <span className="font-semibold text-slate-600">{stop.allocated_minutes} min</span>
                      </div>
                      <div className="mt-2 text-xs font-bold text-slate-800 line-clamp-1">{stop.title}</div>
                      <div className="mt-1 flex items-center justify-between text-[11px] text-slate-500">
                        <span>{stop.zone || "Showcase"}</span>
                        <span className="capitalize">{stop.type}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Equipment Detail Panel */}
          <div className="space-y-4">
            <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div className="flex items-center gap-2">
                  <Layers size={18} className="text-blue-700" />
                  <h3 className="text-sm font-bold text-slate-800">Equipment & Hotspot Details</h3>
                </div>
                {activeAsset && (
                  <span
                    className={`rounded-full px-2.5 py-0.5 text-[10px] font-semibold ${
                      activeAsset.verified_at
                        ? "bg-emerald-100 text-emerald-800"
                        : "bg-amber-100 text-amber-800"
                    }`}
                  >
                    {activeAsset.verified_at ? "Verified Record" : "Awaiting Lab Verification"}
                  </span>
                )}
              </div>

              {activeAsset ? (
                <div className="mt-4 space-y-4">
                  <div>
                    <h4 className="text-base font-bold text-slate-900">{activeAsset.name}</h4>
                    <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-slate-500">
                      <span className="font-mono bg-slate-100 px-1.5 py-0.5 rounded text-[11px]">
                        {activeAsset.id}
                      </span>
                      <span>·</span>
                      <span className="flex items-center gap-1">
                        <MapPin size={12} /> {activeAsset.zone}
                      </span>
                      <span>·</span>
                      <span className="capitalize">{activeAsset.category}</span>
                    </div>
                  </div>

                  <p className="text-xs leading-relaxed text-slate-600">{activeAsset.description}</p>

                  {(activeAsset.manufacturer || activeAsset.model_number) && (
                    <div className="grid grid-cols-2 gap-2 rounded-xl bg-slate-50 p-3 text-xs">
                      <div>
                        <span className="text-slate-400">Manufacturer</span>
                        <div className="font-semibold text-slate-800">
                          {activeAsset.manufacturer || "Unspecified"}
                        </div>
                      </div>
                      <div>
                        <span className="text-slate-400">Model</span>
                        <div className="font-semibold text-slate-800">
                          {activeAsset.model_number || "Unspecified"}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Specifications */}
                  {activeAsset.specifications && Object.keys(activeAsset.specifications).length > 0 && (
                    <div>
                      <div className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1.5">
                        Technical Specifications
                      </div>
                      <div className="space-y-1 rounded-xl border border-slate-100 p-2 text-xs">
                        {Object.entries(activeAsset.specifications).map(([k, v]) => (
                          <div key={k} className="flex justify-between py-1 border-b border-slate-50 last:border-0">
                            <span className="text-slate-500">{k}</span>
                            <span className="font-medium text-slate-800">{String(v)}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Photos */}
                  {activeAsset.photos && activeAsset.photos.length > 0 && (
                    <div>
                      <div className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
                        Laboratory Visual Evidence ({activeAsset.photos.length})
                      </div>
                      <div className="grid grid-cols-2 gap-2">
                        {activeAsset.photos.map((p) => (
                          <div key={p.id} className="group relative overflow-hidden rounded-lg border border-slate-200">
                            <img src={p.url} alt={p.caption} className="h-24 w-full object-cover" />
                            {p.caption && (
                              <div className="absolute inset-x-0 bottom-0 bg-black/60 p-1 text-[10px] text-white truncate">
                                {p.caption}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Source Reference */}
                  {activeAsset.source_reference && (
                    <div className="rounded-lg bg-blue-50/60 p-2.5 text-[11px] text-blue-900">
                      <span className="font-semibold">Source Authority:</span> {activeAsset.source_reference}
                    </div>
                  )}

                  <button
                    onClick={() => {
                      setQuestion(`Tell me about the specifications, safety procedures, and usage of ${activeAsset.name}`);
                    }}
                    className="btn btn-secondary w-full justify-center text-xs"
                  >
                    <Bot size={14} className="text-blue-700" />
                    Ask LabSPOC about this asset
                  </button>
                </div>
              ) : (
                <div className="mt-8 flex flex-col items-center justify-center p-6 text-center text-slate-400">
                  <Building2 size={36} className="mb-2 text-slate-300" />
                  <p className="text-xs font-semibold text-slate-600">No Hotspot Selected</p>
                  <p className="mt-1 text-[11px] text-slate-400 max-w-xs">
                    Select a zone or equipment sphere in the 3D scene or pick from the tour stops to inspect its verified specs.
                  </p>
                </div>
              )}
            </div>

            {/* Visit Summary Box */}
            <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-sm font-bold text-slate-800">
                  <ShieldCheck size={18} className="text-emerald-700" />
                  <span>Visit Summary & Report</span>
                </div>
                <button
                  onClick={finishVisit}
                  disabled={!session || busy}
                  className="rounded-lg border border-slate-300 px-3 py-1 text-xs font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-40"
                >
                  Generate Summary
                </button>
              </div>

              {summary ? (
                <div className="mt-3 rounded-xl bg-slate-50 p-3.5 text-xs space-y-2">
                  <div className="grid grid-cols-2 gap-2 text-slate-700">
                    <div>Persona: <b>{summary.persona}</b></div>
                    <div>Duration: <b>{summary.duration_minutes} min</b></div>
                    <div>Recorded Events: <b>{summary.event_count}</b></div>
                    <div>Questions Answered: <b>{summary.question_count || 0}</b></div>
                  </div>
                  <p className="text-[11px] text-slate-500 pt-1 border-t border-slate-200">
                    {summary.privacy_note}
                  </p>
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(
                        `LabSPOC AI Visit Summary\nSession: ${summary.session_id}\nPersona: ${summary.persona}\nDuration: ${summary.duration_minutes} min\nEvents: ${summary.event_count}\nQuestions: ${summary.question_count || 0}`
                      );
                      alert("Visit summary copied to clipboard!");
                    }}
                    className="text-xs font-semibold text-blue-700 hover:underline"
                  >
                    Copy summary to clipboard
                  </button>
                </div>
              ) : (
                <p className="mt-2 text-xs text-slate-500">
                  Conclude your session anytime to compile your customized institutional visit summary.
                </p>
              )}
            </div>
          </div>
        </section>

        {/* Conversational Assistant & Knowledge System */}
        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3">
            <div className="flex items-center gap-2">
              <Bot size={20} className="text-blue-700" />
              <div>
                <h2 className="text-sm font-bold text-slate-800">Conversational Lab Assistant</h2>
                <p className="text-xs text-slate-500">
                  Multilingual Gemini-grounded dialogue protected by Evidence Gate verification.
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2 text-xs text-slate-500">
              <span className="rounded-full bg-emerald-100 px-2.5 py-0.5 text-[11px] font-semibold text-emerald-800">
                Evidence Gate Active
              </span>
              <span>{langConfig.label}</span>
            </div>
          </div>

          {/* Chat Messages Thread */}
          <div className="mt-4 h-80 overflow-y-auto rounded-xl border border-slate-200 bg-slate-50/60 p-4 space-y-4">
            {messages.length === 0 ? (
              <div className="flex h-full flex-col items-center justify-center text-center text-slate-400">
                <Bot size={40} className="mb-2 text-slate-300" />
                <p className="text-sm font-semibold text-slate-600">LabSPOC is Ready</p>
                <p className="mt-1 text-xs text-slate-500 max-w-md">
                  Ask about GPU compute specs, SOP safety protocols, faculty research, or student projects.
                  All responses cite approved laboratory records.
                </p>
                <div className="mt-3 flex flex-wrap gap-2">
                  <button
                    onClick={() => setQuestion("What GPU workstations are available in the AI & ML lab?")}
                    className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs text-slate-700 hover:border-blue-300"
                  >
                    "What GPU workstations are available?"
                  </button>
                  <button
                    onClick={() => setQuestion("How do students reserve lab compute resources?")}
                    className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs text-slate-700 hover:border-blue-300"
                  >
                    "How to reserve compute resources?"
                  </button>
                </div>
              </div>
            ) : (
              messages.map((m) => (
                <div
                  key={m.id}
                  className={`flex flex-col ${m.sender === "visitor" ? "items-end" : "items-start"}`}
                >
                  <div className="text-[10px] text-slate-400 mb-1 px-1">
                    {m.sender === "visitor" ? "You" : "LabSPOC AI"} · {m.timestamp}
                  </div>
                  <div
                    className={`max-w-2xl rounded-2xl p-4 text-xs leading-relaxed shadow-sm ${
                      m.sender === "visitor"
                        ? "bg-blue-700 text-white rounded-br-none"
                        : "bg-white text-slate-800 border border-slate-200 rounded-bl-none"
                    }`}
                  >
                    <p className="whitespace-pre-wrap">{m.text}</p>

                    {m.sender === "assistant" && (
                      <div className="mt-3 pt-2.5 border-t border-slate-100 space-y-2">
                        {/* Evidence Gate Pill */}
                        {m.evidence_gate && (
                          <div className="flex items-center gap-1.5 text-[10px]">
                            {m.evidence_gate.verified_grounding ? (
                              <span className="flex items-center gap-1 font-semibold text-emerald-700">
                                <ShieldCheck size={13} /> Verified Evidence Grounding
                              </span>
                            ) : (
                              <span className="flex items-center gap-1 font-semibold text-amber-700">
                                <ShieldAlert size={13} /> Insufficient Evidence (Honest Abstention)
                              </span>
                            )}
                          </div>
                        )}

                        {/* Citations */}
                        {m.citations && m.citations.length > 0 && (
                          <div className="space-y-1">
                            <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                              Approved Citations
                            </div>
                            {m.citations.map((c, i) => (
                              <div key={i} className="text-[11px] font-medium text-blue-800">
                                [{i + 1}] {c.filename} {c.page ? `(page ${c.page})` : ""} · Doc ID: {c.document_id.slice(0, 8)}
                              </div>
                            ))}
                          </div>
                        )}

                        {/* Read Aloud Button */}
                        <div className="flex justify-end pt-1">
                          <button
                            onClick={() => handleSpeak(m.text)}
                            className="flex items-center gap-1 text-[11px] font-semibold text-blue-700 hover:underline"
                          >
                            <Volume2 size={13} /> Read Aloud
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
            <div ref={chatBottomRef} />
          </div>

          {/* Chat Input Bar */}
          <div className="mt-4 flex gap-2">
            <textarea
              className="input min-h-[48px] flex-1 resize-none py-2.5 text-xs"
              placeholder={`Ask LabSPOC in ${langConfig.label} or English...`}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  sendQuery();
                }
              }}
            />

            <button
              onClick={handleVoiceInput}
              title="Speak question via microphone"
              className={`flex h-[48px] w-[48px] items-center justify-center rounded-xl border transition ${
                listening
                  ? "border-rose-400 bg-rose-50 text-rose-700 animate-pulse"
                  : "border-slate-300 bg-white text-slate-700 hover:bg-slate-50"
              }`}
            >
              {listening ? <MicOff size={18} /> : <Mic size={18} />}
            </button>

            <button
              onClick={sendQuery}
              disabled={busy || !question.trim()}
              className="btn btn-primary h-[48px] px-5 disabled:opacity-40"
            >
              <Send size={15} />
            </button>
          </div>
        </section>

        {/* AI Project Demonstrator (Module 4) */}
        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-4">
            <div>
              <div className="flex items-center gap-2">
                <FlaskConical size={18} className="text-blue-700" />
                <h2 className="text-sm font-bold text-slate-800">AI Project Demonstrator</h2>
              </div>
              <p className="text-xs text-slate-500">
                Institutional innovation gallery: reviewed student and faculty research projects.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
                {projects.length} Published
              </span>
              <button
                onClick={() => setProjectModalOpen(true)}
                className="btn btn-primary text-xs"
              >
                <PlusCircle size={14} /> Submit New Project
              </button>
            </div>
          </div>

          <div className="mt-5 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {projects.length > 0 ? (
              projects.map((p) => (
                <div
                  key={p.id}
                  onClick={() => recordEvent("project_view", p.id)}
                  className="flex flex-col justify-between rounded-xl border border-slate-200 bg-white p-4 shadow-sm hover:border-blue-300 transition"
                >
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-xs">
                      <span className="rounded bg-blue-50 px-2 py-0.5 text-[10px] font-bold text-blue-700 uppercase">
                        {p.author_type} project
                      </span>
                      <span className="text-[11px] text-slate-400 font-mono">{p.id}</span>
                    </div>

                    <h4 className="text-sm font-bold text-slate-900 leading-snug">{p.title}</h4>
                    <p className="text-xs text-slate-600 line-clamp-3 leading-relaxed">{p.problem}</p>

                    {p.methodology && (
                      <div className="text-[11px] text-slate-500">
                        <span className="font-semibold text-slate-700">Methodology:</span> {p.methodology}
                      </div>
                    )}

                    {p.technologies && (
                      <div className="flex flex-wrap gap-1 pt-1">
                        {p.technologies.split(",").map((tech, i) => (
                          <span
                            key={i}
                            className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] text-slate-700 font-medium"
                          >
                            {tech.trim()}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between">
                    <div className="text-[11px] text-slate-500 font-medium">
                      By {p.author_name || "OIST Researcher"}
                    </div>
                    {p.demo_url && (
                      <a
                        href={p.demo_url}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1 text-xs font-semibold text-blue-700 hover:underline"
                      >
                        Demo <ExternalLink size={12} />
                      </a>
                    )}
                  </div>
                </div>
              ))
            ) : (
              <div className="col-span-full rounded-xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center">
                <FileQuestion size={36} className="mx-auto mb-2 text-slate-400" />
                <p className="text-sm font-semibold text-slate-700">No Approved Projects Published Yet</p>
                <p className="mt-1 text-xs text-slate-500 max-w-md mx-auto">
                  Student and faculty innovations appear here after review. Submit your research or capstone project using the button above.
                </p>
              </div>
            )}
          </div>
        </section>
      </div>

      {/* Project Submission Modal */}
      {projectModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm">
          <div className="w-full max-w-xl rounded-2xl bg-white p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-base font-bold text-slate-900">Submit Project for Showcase</h3>
              <button
                onClick={() => setProjectModalOpen(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X size={18} />
              </button>
            </div>

            {subMessage && (
              <div className="rounded-lg bg-emerald-50 p-3 text-xs font-semibold text-emerald-800">
                {subMessage}
              </div>
            )}

            <form onSubmit={submitProject} className="space-y-3 text-xs">
              <div>
                <label className="font-semibold text-slate-700">Project Title *</label>
                <input
                  className="input mt-1"
                  required
                  placeholder="e.g. Edge AI Object Detection for Drone Navigation"
                  value={subTitle}
                  onChange={(e) => setSubTitle(e.target.value)}
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-semibold text-slate-700">Author Name(s) *</label>
                  <input
                    className="input mt-1"
                    required
                    placeholder="e.g. Rahul Verma & Team"
                    value={subAuthor}
                    onChange={(e) => setSubAuthor(e.target.value)}
                  />
                </div>
                <div>
                  <label className="font-semibold text-slate-700">Contributor Type</label>
                  <select
                    className="input mt-1"
                    value={subAuthorType}
                    onChange={(e) => setSubAuthorType(e.target.value)}
                  >
                    <option value="student">Student Innovator</option>
                    <option value="faculty">Faculty Researcher</option>
                    <option value="researcher">Research Scholar</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="font-semibold text-slate-700">Problem Statement *</label>
                <textarea
                  className="input mt-1 min-h-[64px]"
                  required
                  placeholder="What societal or technical challenge does this address?"
                  value={subProblem}
                  onChange={(e) => setSubProblem(e.target.value)}
                />
              </div>

              <div>
                <label className="font-semibold text-slate-700">Methodology & Algorithms</label>
                <input
                  className="input mt-1"
                  placeholder="e.g. YOLOv8 fine-tuned on custom industrial dataset with TensorRT quantization"
                  value={subMethod}
                  onChange={(e) => setSubMethod(e.target.value)}
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-semibold text-slate-700">Tech Stack</label>
                  <input
                    className="input mt-1"
                    placeholder="e.g. PyTorch, CUDA, FastAPI, Docker"
                    value={subTech}
                    onChange={(e) => setSubTech(e.target.value)}
                  />
                </div>
                <div>
                  <label className="font-semibold text-slate-700">Demo URL</label>
                  <input
                    className="input mt-1"
                    placeholder="https://github.com/..."
                    value={subDemo}
                    onChange={(e) => setSubDemo(e.target.value)}
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setProjectModalOpen(false)}
                  className="btn btn-secondary"
                >
                  Cancel
                </button>
                <button type="submit" disabled={busy} className="btn btn-primary">
                  {busy ? "Submitting..." : "Submit for Faculty Review"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white py-6 text-center text-xs text-slate-400">
        <div className="mx-auto max-w-7xl px-4 sm:px-6">
          LabSPOC AI · SPARKX 3.0 International Innovation Challenge · OIST Bhopal AI & ML Laboratory.
          <br />
          Room geometry and zone markers are illustrative pending full institutional photogrammetric survey.
        </div>
      </footer>
    </main>
  );
}
