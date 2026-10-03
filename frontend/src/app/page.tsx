import {
  CheckCircle2,
  Clock,
  Database,
  FileCode2,
  Server,
  Layers,
} from "lucide-react";

export default function HomePage() {
  const components = [
    {
      title: "FastAPI Backend",
      icon: Server,
      status: "Ready",
      details: "FastAPI + Pydantic v2 + Uvicorn. Health check at /api/v1/health.",
      tech: "Python 3.12",
    },
    {
      title: "Database Layer",
      icon: Database,
      status: "Ready",
      details: "SQLAlchemy 2.x with PostgreSQL JSONB and SQLite fallback.",
      tech: "PortableJSON",
    },
    {
      title: "Schema Migrations",
      icon: Layers,
      status: "Ready",
      details: "Alembic 001_initial migration creating datasets and posts tables.",
      tech: "Alembic 1.20",
    },
    {
      title: "Frontend Application",
      icon: FileCode2,
      status: "Ready",
      details: "Next.js 15 App Router with TypeScript strict mode and Tailwind CSS.",
      tech: "React 19",
    },
  ];

  const phaseRoadmap = [
    { num: 1, name: "Project Foundation", status: "completed", desc: "FastAPI backend, DB schema, Alembic, Next.js shell" },
    { num: 2, name: "Dataset Ingestion", status: "planned", desc: "CSV parsing, column mapping, UTC normalization, validation" },
    { num: 3, name: "NLP Preprocessing", status: "planned", desc: "Text cleaner, canonical versioning, sentiment-ready & NER text" },
    { num: 4, name: "Sentiment Analysis", status: "planned", desc: "CardiffNLP Twitter-RoBERTa (CC-BY-4.0), batch inference" },
    { num: 5, name: "Topic Discovery", status: "planned", desc: "Sentence Transformers + UMAP + HDBSCAN + BERTopic" },
    { num: 6, name: "Keywords & Entities", status: "planned", desc: "c-TF-IDF keyword extraction, spaCy NER on case-preserved text" },
    { num: 7, name: "Trend Detection Engine", status: "planned", desc: "UTC temporal aggregation, centered logistic normalization, recency" },
    { num: 8, name: "Analytics APIs", status: "planned", desc: "Summary, topics, timelines, sentiment, search REST endpoints" },
    { num: 9, name: "Analytics Dashboard", status: "planned", desc: "Interactive charts, trend tables, detail pages, data explorer" },
    { num: 10, name: "End-to-End Verification", status: "planned", desc: "Full pipeline smoke test, integration testing, benchmarks" },
  ];

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div>
        <h2 className="text-xl font-bold tracking-tight text-zinc-900">
          Social Trend Analyzer — Phase 1 Foundation
        </h2>
        <p className="mt-1 text-sm text-zinc-500 max-w-3xl">
          The foundational architecture and operational shell have been established.
          Subsequent phases will incrementally implement dataset ingestion, local NLP model execution,
          temporal trend detection, and interactive dashboard analytics.
        </p>
      </div>

      {/* Component Status Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {components.map((c) => {
          const Icon = c.icon;
          return (
            <div
              key={c.title}
              className="bg-white border border-zinc-200 rounded-lg p-5 flex flex-col justify-between shadow-xs"
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="w-8 h-8 rounded-md bg-zinc-100 flex items-center justify-center text-zinc-700">
                    <Icon className="w-4 h-4" />
                  </div>
                  <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                    <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                    {c.status}
                  </span>
                </div>
                <h3 className="text-sm font-semibold text-zinc-900">{c.title}</h3>
                <p className="mt-1 text-xs text-zinc-600 leading-relaxed">{c.details}</p>
              </div>
              <div className="mt-4 pt-3 border-t border-zinc-100 flex justify-between items-center text-[11px] text-zinc-400 font-mono">
                <span>Stack</span>
                <span className="text-zinc-600 font-medium">{c.tech}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Roadmap & Architecture Progress */}
      <div className="bg-white border border-zinc-200 rounded-lg p-6 shadow-xs">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-semibold text-zinc-900">Implementation Roadmap</h3>
            <p className="text-xs text-zinc-500">
              Structured 10-phase plan defined in IMPLEMENTATION_ROADMAP.md.
            </p>
          </div>
          <span className="text-xs font-mono bg-zinc-100 px-2.5 py-1 rounded text-zinc-600">
            Phase 1 of 10 Complete
          </span>
        </div>

        <div className="divide-y divide-zinc-100">
          {phaseRoadmap.map((p) => (
            <div
              key={p.num}
              className="py-3 flex items-center justify-between text-xs"
            >
              <div className="flex items-center gap-3">
                <span className="font-mono text-zinc-400 w-5 text-right font-medium">
                  {p.num.toString().padStart(2, "0")}
                </span>
                <div>
                  <span className={`font-medium ${p.status === "completed" ? "text-zinc-900 font-semibold" : "text-zinc-700"}`}>
                    {p.name}
                  </span>
                  <span className="text-zinc-400 ml-2 hidden sm:inline">— {p.desc}</span>
                </div>
              </div>
              <div>
                {p.status === "completed" ? (
                  <span className="inline-flex items-center gap-1 text-[11px] text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded font-medium border border-emerald-200">
                    <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                    Verified
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 text-[11px] text-zinc-500 bg-zinc-50 px-2 py-0.5 rounded font-medium border border-zinc-200">
                    <Clock className="w-3 h-3 text-zinc-400" />
                    Planned
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Specifications & Architectural Constraints */}
      <div className="bg-zinc-50 border border-zinc-200 rounded-lg p-5">
        <h3 className="text-xs font-semibold text-zinc-800 uppercase tracking-wider mb-2">
          Phase 1 Architectural Bounds
        </h3>
        <ul className="text-xs text-zinc-600 space-y-1 list-disc list-inside">
          <li>Local CPU-only execution without remote API inference dependencies.</li>
          <li>Committed lockfiles: <code className="font-mono bg-zinc-200/60 px-1 py-0.5 rounded text-[11px]">backend/requirements.lock</code> and <code className="font-mono bg-zinc-200/60 px-1 py-0.5 rounded text-[11px]">frontend/package-lock.json</code>.</li>
          <li>Strict UTC timestamp storage and normalized time-window aggregation boundaries.</li>
          <li>Canonical dataset-level text preprocessing immutability per <code className="font-mono bg-zinc-200/60 px-1 py-0.5 rounded text-[11px]">{'preprocessing_version="1.0.0"'}</code>.</li>
        </ul>
      </div>
    </div>
  );
}
