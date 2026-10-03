"use client";

import React, { useEffect, useState } from "react";
import {
  Brain,
  CheckCircle2,
  Cpu,
  Database,
  Loader2,
  Lock,
  RefreshCw,
  Scale,
  Sparkles,
} from "lucide-react";
import { api, PipelineMetadata } from "@/lib/api";

export default function PipelinePage() {
  const [meta, setMeta] = useState<PipelineMetadata | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchMeta = async () => {
    try {
      setLoading(true);
      const res = await api.getPipelineMetadata();
      setMeta(res);
    } catch (err) {
      console.error("Failed to fetch pipeline metadata:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMeta();
  }, []);

  const pipelineStages = [
    {
      step: "01",
      name: "Data Ingestion & UTC Normalization",
      tech: "Python CSV Parser + Dateutil",
      desc: "Robust auto-detection of text, timestamp, and engagement columns. Strict conversion to UTC calendar boundaries; invalid rows safely quarantined.",
      invariant: "Original unmodified raw text is canonically preserved in storage.",
    },
    {
      step: "02",
      name: "Preprocessing & Representation Derivation",
      tech: "Regex + Unidecode (v1.0.0)",
      desc: "Produces three immutable textual representations: cleaned_text for topic modeling/search, sentiment_ready_text with @user tokens, and runtime case-preserved text for spaCy NER.",
      invariant: "Canonical version 1.0.0 is immutable across subsequent runs.",
    },
    {
      step: "03",
      name: "Transformer Sentiment Inference",
      tech: "CardiffNLP Twitter-RoBERTa (CC-BY-4.0)",
      desc: "3-class classification (Negative, Neutral, Positive) trained on ~124M tweets. Evaluates ground truth accuracy and Macro F1 when annotations are present.",
      invariant: "Batched CPU inference with memory-efficient torch no_grad.",
    },
    {
      step: "04",
      name: "Unsupervised Topic Discovery",
      tech: "BERTopic + all-MiniLM-L6-v2 + UMAP + HDBSCAN",
      desc: "Encodes 384-dimensional dense semantic embeddings (Sentence-Transformers). UMAP projects embeddings into low-dimensional manifold; HDBSCAN discovers clusters without predefined K.",
      invariant: "nr_topics=None preserves micro-clusters; outlier cluster -1 is explicitly retained.",
    },
    {
      step: "05",
      name: "NLP Enrichment (NER & Keywords)",
      tech: "spaCy en_core_web_sm + c-TF-IDF",
      desc: "Extracts Named Entities (PERSON, ORG, GPE, PRODUCT, EVENT) strictly on case-preserved text. Computes class-based TF-IDF keyword weights and hashtag velocity deltas.",
      invariant: "Case-preserved text is mandatory to prevent lowercase spaCy degradation.",
    },
    {
      step: "06",
      name: "Trend Detection & Recency Modulation",
      tech: "Centered 4-Signal Momentum Model",
      desc: "Combines Volume Growth (0.35), Engagement Growth (0.25), Velocity (0.20), and Burstiness z-score (0.20) via centered logistic normalization. Modulated by exponential recency decay R.",
      invariant: "Mathematical Guarantee: Zero growth strictly produces neutral TrendScore = 0.50.",
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold tracking-tight text-slate-900 font-sans">
              Pipeline Architecture & Model Verification
            </h1>
            <span className="font-mono text-xs px-2 py-0.5 rounded-xs bg-slate-100 text-slate-700 border border-slate-200">
              Technical Specification
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1 font-sans">
            Transparent algorithmic ledger documenting model weights, licenses, mathematical formulations, and runtime state.
          </p>
        </div>

        <button
          onClick={fetchMeta}
          disabled={loading}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xs border border-slate-200 bg-white text-xs font-medium text-slate-700 hover:bg-slate-50 transition-colors shadow-2xs cursor-pointer self-start sm:self-auto"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          Refresh Status
        </button>
      </div>

      {/* System Parameter Ledger Tiles */}
      {loading ? (
        <div className="py-12 text-center text-xs font-mono text-slate-500 flex items-center justify-center gap-2">
          <Loader2 className="w-4 h-4 animate-spin text-slate-600" />
          Querying system metadata...
        </div>
      ) : meta ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {/* Sentiment Model */}
          <div className="bg-white border border-slate-200 rounded-xs p-4 shadow-2xs space-y-1.5">
            <div className="text-[10px] font-mono text-slate-400 uppercase tracking-wider flex items-center justify-between">
              <span>Sentiment Model</span>
              <Brain className="w-3.5 h-3.5 text-slate-400" />
            </div>
            <div className="font-semibold text-xs text-slate-900 font-mono truncate" title={meta.sentiment_model}>
              {meta.sentiment_model.split("/").pop()}
            </div>
            <div className="text-[10px] font-mono text-emerald-700 font-medium">
              License: {meta.sentiment_license}
            </div>
          </div>

          {/* Embeddings */}
          <div className="bg-white border border-slate-200 rounded-xs p-4 shadow-2xs space-y-1.5">
            <div className="text-[10px] font-mono text-slate-400 uppercase tracking-wider flex items-center justify-between">
              <span>Embeddings</span>
              <Cpu className="w-3.5 h-3.5 text-slate-400" />
            </div>
            <div className="font-semibold text-xs text-slate-900 font-mono">
              {meta.embedding_model}
            </div>
            <div className="text-[10px] font-mono text-slate-500">
              {meta.embedding_dimensions} dense dimensions (L2-norm)
            </div>
          </div>

          {/* NER Model */}
          <div className="bg-white border border-slate-200 rounded-xs p-4 shadow-2xs space-y-1.5">
            <div className="text-[10px] font-mono text-slate-400 uppercase tracking-wider flex items-center justify-between">
              <span>Named Entity Recognition</span>
              <Sparkles className="w-3.5 h-3.5 text-slate-400" />
            </div>
            <div className="font-semibold text-xs text-slate-900 font-mono">
              spaCy {meta.ner_model}
            </div>
            <div className="text-[10px] font-mono text-slate-500">
              Case-preserved text execution
            </div>
          </div>

          {/* Database & Concurrency */}
          <div className="bg-white border border-slate-200 rounded-xs p-4 shadow-2xs space-y-1.5">
            <div className="text-[10px] font-mono text-slate-400 uppercase tracking-wider flex items-center justify-between">
              <span>Database Engine</span>
              <Database className="w-3.5 h-3.5 text-slate-400" />
            </div>
            <div className="font-semibold text-xs text-slate-900 font-mono uppercase">
              {meta.database_backend}
            </div>
            <div className="text-[10px] font-mono text-slate-500 flex items-center gap-1">
              <Lock className="w-3 h-3 text-slate-400" />
              Concurrency: 1 active run guard
            </div>
          </div>
        </div>
      ) : null}

      {/* Trend Formula Specification Box */}
      {meta && (
        <div className="bg-white border border-slate-200 rounded-xs p-5 shadow-2xs space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-slate-900 font-sans flex items-center gap-1.5">
              <Scale className="w-4 h-4 text-sky-600" />
              Mathematical Trend Scoring Engine Formulation
            </h2>
            <span className="font-mono text-[10px] px-2 py-0.5 rounded-xs bg-slate-100 text-slate-600 border border-slate-200">
              S(0) = 0.50 (Centered Neutrality)
            </span>
          </div>

          <p className="text-xs text-slate-600 font-sans leading-relaxed">
            Trend momentum M_base combines four centered logistic normalized signals S(x) = 1 / (1 + e^-kx) where zero growth strictly evaluates to 0.50. Recency factor R = e^(-&lambda;&Delta;t) acts as a multiplicative relevance modulation on deviation from neutral, ensuring dead topics never appear emerging.
          </p>

          <div className="bg-slate-50 p-3 rounded-xs border border-slate-200 font-mono text-xs text-slate-800 space-y-1.5 overflow-x-auto">
            <div className="text-sky-900 font-semibold">
              TrendScore = 0.50 + (M_base - 0.50) &times; R
            </div>
            <div className="text-slate-600 text-[11px]">
              M_base = ({meta.trend_weights.volume} &times; S_vol) + ({meta.trend_weights.engagement} &times; S_eng) + ({meta.trend_weights.velocity} &times; S_vel) + ({meta.trend_weights.burstiness} &times; S_burst)
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2 text-xs font-mono">
            <div className="bg-amber-50/70 border border-amber-200 p-2.5 rounded-xs">
              <span className="text-[10px] text-amber-800 uppercase block font-semibold">Emerging Surge</span>
              <span className="text-amber-900 font-bold">&ge; {meta.trend_thresholds.emerging.toFixed(2)}</span>
              <span className="text-[10px] text-amber-700 block mt-0.5">age &lt; 2 windows or V_prev = 0</span>
            </div>
            <div className="bg-teal-50/70 border border-teal-200 p-2.5 rounded-xs">
              <span className="text-[10px] text-teal-800 uppercase block font-semibold">Rising Trend</span>
              <span className="text-teal-900 font-bold">&ge; {meta.trend_thresholds.rising.toFixed(2)}</span>
              <span className="text-[10px] text-teal-700 block mt-0.5">sustained multi-window momentum</span>
            </div>
            <div className="bg-slate-100/70 border border-slate-200 p-2.5 rounded-xs">
              <span className="text-[10px] text-slate-700 uppercase block font-semibold">Stable Baseline</span>
              <span className="text-slate-900 font-bold">[{meta.trend_thresholds.stable.toFixed(2)}, {meta.trend_thresholds.rising.toFixed(2)})</span>
              <span className="text-[10px] text-slate-600 block mt-0.5">consistent with historical norms</span>
            </div>
            <div className="bg-rose-50/70 border border-rose-200 p-2.5 rounded-xs">
              <span className="text-[10px] text-rose-800 uppercase block font-semibold">Declining Momentum</span>
              <span className="text-rose-900 font-bold">&lt; {meta.trend_thresholds.stable.toFixed(2)}</span>
              <span className="text-[10px] text-rose-700 block mt-0.5">negative growth or deceleration</span>
            </div>
          </div>
        </div>
      )}

      {/* 6-Stage End-to-End Computational Pipeline */}
      <div className="bg-white border border-slate-200 rounded-xs shadow-2xs overflow-hidden">
        <div className="p-4 border-b border-slate-200">
          <h2 className="text-sm font-semibold text-slate-900 font-sans">
            End-to-End NLP Execution Pipeline Stages
          </h2>
          <p className="text-[11px] text-slate-500 font-sans">
            Sequential stages executed in isolated, reproducible Python modules.
          </p>
        </div>

        <div className="divide-y divide-slate-100">
          {pipelineStages.map((stage) => (
            <div key={stage.step} className="p-4 hover:bg-slate-50/60 transition-colors flex flex-col md:flex-row md:items-start justify-between gap-4">
              <div className="flex items-start gap-3">
                <span className="font-mono text-sm font-bold text-slate-400 shrink-0 mt-0.5">
                  {stage.step}
                </span>
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-slate-900 font-sans">
                      {stage.name}
                    </span>
                    <span className="font-mono text-[10px] px-1.5 py-0.5 rounded-xs bg-slate-100 text-slate-600 border border-slate-200">
                      {stage.tech}
                    </span>
                  </div>
                  <p className="text-xs text-slate-600 font-sans leading-relaxed max-w-3xl">
                    {stage.desc}
                  </p>
                </div>
              </div>

              <div className="md:text-right shrink-0">
                <span className="inline-flex items-center gap-1 text-[11px] font-mono text-slate-600 bg-slate-50 px-2 py-1 rounded-xs border border-slate-200">
                  <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                  {stage.invariant}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
