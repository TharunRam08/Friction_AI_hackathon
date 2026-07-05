// frontend/src/App.jsx
import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import {
  Check, Play, Plus, Loader2, MoreHorizontal, Sparkles,
  ArrowUpRight, TrendingUp, BarChart2, Users, Clock,
  X, ChevronRight, Database, RefreshCw, AlertCircle,
  FileText, Zap, Shield, Eye, Brain, GitBranch,
  AlertTriangle, Target, ChevronDown, ChevronUp,
  Package, Archive, HelpCircle, Truck, CreditCard, Activity
} from 'lucide-react';

const API = 'http://localhost:8000';

// ── Icon resolver ────────────────────────────────────────────────────────────
function SrcIcon({ name, className }) {
  const p = { className: className || 'w-4 h-4' };
  if (name === 'users')        return <Users {...p} />;
  if (name === 'trending-up')  return <TrendingUp {...p} />;
  if (name === 'bar-chart')    return <BarChart2 {...p} />;
  if (name === 'people')       return <Users {...p} />;
  if (name === 'clock')        return <Clock {...p} />;
  if (name === 'package')      return <Package {...p} />;
  if (name === 'archive')      return <Archive {...p} />;
  if (name === 'target')       return <Target {...p} />;
  if (name === 'help-circle')  return <HelpCircle {...p} />;
  if (name === 'truck')        return <Truck {...p} />;
  if (name === 'credit-card')  return <CreditCard {...p} />;
  if (name === 'activity')     return <Activity {...p} />;
  if (name === 'file-text')    return <FileText {...p} />;
  return <Database {...p} />;
}

// ── Badge colour helper ──────────────────────────────────────────────────────
function badgeCls(val) {
  if (!val) return 'bg-zinc-800 text-zinc-400';
  const v = String(val).toLowerCase();
  if (['success','closed-won','active','low','ok','yes'].some(x => v.includes(x)))
    return 'bg-emerald-900/60 text-emerald-300';
  if (['failed','closed-lost','churned','high','violated','no'].some(x => v.includes(x)))
    return 'bg-red-900/50 text-red-300';
  return 'bg-amber-900/50 text-amber-300';
}

// ── Trend icon ───────────────────────────────────────────────────────────────
function TrendIcon({ trend }) {
  if (trend === 'up')      return <span className="text-emerald-400 text-xs">▲</span>;
  if (trend === 'down')    return <span className="text-red-400 text-xs">▼</span>;
  if (trend === 'warning') return <AlertTriangle className="w-3 h-3 text-amber-400 inline" />;
  return <span className="text-zinc-600 text-xs">─</span>;
}

// ══════════════════════════════════════════════════════════════════════════════
//  DATA VIEWER MODAL (fixed overlay — avoids all flex/z-index issues)
// ══════════════════════════════════════════════════════════════════════════════
function DataViewer({ source, onClose }) {
  const [data, setData]     = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]   = useState(null);

  useEffect(() => {
    if (!source) return;
    setLoading(true); setError(null); setData(null);
    axios.get(`${API}/data-sources/${source.id}?limit=100`)
      .then(r => { setData(r.data); setLoading(false); })
      .catch(e => { setError('Could not reach backend. Is it running?'); setLoading(false); });
  }, [source?.id]);

  if (!source) return null;

  const BADGE_COLS    = new Set(['outcome','status','churn_risk','stage','impact','stance']);
  const CURRENCY_COLS = new Set(['ltv','value','revenue','cost_of_goods','operating_cost','profit',
                                  'budget','salary','financial_impact']);
  const PCT_COLS      = new Set(['probability','confidence_at_time']);
  const RATING_COLS   = new Set(['performance']);

  function fmtCell(col, val) {
    if (val === null || val === undefined) return <span className="text-zinc-700">—</span>;
    if (BADGE_COLS.has(col))
      return <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wide ${badgeCls(val)}`}>{val}</span>;
    if (CURRENCY_COLS.has(col) && typeof val === 'number')
      return <span className="font-mono text-emerald-400 text-[11px]">${Number(val).toLocaleString()}</span>;
    if (PCT_COLS.has(col))
      return <span className="font-mono text-blue-400 text-[11px]">{val}%</span>;
    if (RATING_COLS.has(col))
      return <span className="font-mono text-purple-400 text-[11px]">{val}/5</span>;
    const s = String(val);
    return <span className="text-zinc-300 text-[11px] max-w-[180px] truncate block" title={s}>{s}</span>;
  }

  return (
    <div className="fixed inset-0 z-[100] flex flex-col bg-[#0a0a0b]">
      {/* Header */}
      <div className="h-14 border-b border-[#1c1c1f] px-6 flex items-center justify-between flex-shrink-0 bg-[#111113]">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-blue-600/20 border border-blue-600/30 flex items-center justify-center">
            <SrcIcon name={source.icon} className="w-4 h-4 text-blue-400" />
          </div>
          <div>
            <div className="text-[13px] font-bold text-white">{source.label}</div>
            {data && <div className="text-[10px] text-zinc-500">{data.total} rows · {data.columns?.length} columns</div>}
          </div>
          {source.tags?.map(t => (
            <span key={t} className="px-2 py-0.5 bg-[#1d1d21] border border-[#2a2a2f] text-zinc-500 text-[9px] font-bold rounded-full uppercase tracking-wider">{t}</span>
          ))}
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full shadow-[0_0_6px_#10b981]" />
            <span className="text-[11px] text-zinc-500 font-medium">{source.summary}</span>
          </div>
          <button onClick={onClose}
            className="w-8 h-8 rounded-lg bg-[#181819] border border-[#2a2a2f] flex items-center justify-center hover:bg-zinc-800 hover:border-zinc-600 transition">
            <X className="w-4 h-4 text-zinc-400" />
          </button>
        </div>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-auto p-6">
        {loading && (
          <div className="flex flex-col items-center justify-center h-full gap-4">
            <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
            <p className="text-sm text-zinc-500">Loading {source.label} dataset…</p>
          </div>
        )}
        {error && (
          <div className="flex flex-col items-center justify-center h-full gap-4">
            <AlertCircle className="w-8 h-8 text-red-400" />
            <p className="text-sm text-zinc-400">{error}</p>
            <button onClick={() => { setLoading(true); setError(null);
              axios.get(`${API}/data-sources/${source.id}`)
                .then(r => { setData(r.data); setLoading(false); })
                .catch(() => { setError('Still unreachable.'); setLoading(false); }); }}
              className="px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-xs text-zinc-300 hover:bg-zinc-700 transition">
              Retry
            </button>
          </div>
        )}
        {!loading && !error && (!data?.rows || data.rows.length === 0) && (
          <div className="flex items-center justify-center h-full">
            <p className="text-sm text-zinc-500">No data found in this table.</p>
          </div>
        )}
        {!loading && !error && data?.rows?.length > 0 && (
          <div className="rounded-xl border border-[#1e1e22] overflow-auto">
            <table className="w-full text-[11.5px] border-collapse min-w-max">
              <thead className="sticky top-0 z-10">
                <tr className="bg-[#111113] border-b border-[#1e1e22]">
                  {data.columns.map(col => (
                    <th key={col} className="px-4 py-3 text-left font-bold text-zinc-500 uppercase tracking-widest text-[9px] whitespace-nowrap border-r border-[#1a1a1e] last:border-r-0">
                      {col.replace(/_/g, ' ')}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.rows.map((row, ri) => (
                  <tr key={ri} className="border-b border-[#161619] hover:bg-[#131316] transition-colors">
                    {data.columns.map(col => (
                      <td key={col} className="px-4 py-2.5 border-r border-[#161619] last:border-r-0 align-middle">
                        {fmtCell(col, row[col])}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════════════
//  RICH OUTPUT CARD — Renders the executive briefing from the pipeline
// ══════════════════════════════════════════════════════════════════════════════
function RichOutputCard({ output, frictionLevel, pipelineExecuted }) {
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [showScenarios, setShowScenarios] = useState(true);
  const [showDevils, setShowDevils] = useState(false);
  const [showSelfReview, setShowSelfReview] = useState(false);

  if (!output) return null;

  const frictionColor = {
    LOW:    'text-emerald-400 bg-emerald-900/20 border-emerald-800/40',
    MEDIUM: 'text-amber-400 bg-amber-900/20 border-amber-800/40',
    HIGH:   'text-red-400 bg-red-900/20 border-red-800/40',
  }[frictionLevel] || 'text-zinc-400 bg-zinc-900/20 border-zinc-700';

  const verdictText = output.verdict || '';
  const contextExplanation = output.context_explanation || output.narrative || '';
  const statsExplanation = output.stats_explanation || '';
  const keyStats    = output.key_stats || [];
  const scenarios   = output.scenarios || [];
  const devils      = output.devils_advocate || [];
  const actionPlan  = output.action_plan || [];
  const ifIgnored   = output.if_ignored || [];
  const departments = output.departments || [];
  const confidence  = output.confidence || 0;
  const breakdown   = output.confidence_breakdown || {};
  const evidenceScore = output.evidence_score || 0;
  const constraints   = output.constraints_check || [];
  const selfReview    = output.self_review || '';
  const rootCause     = output.root_cause_summary || '';
  const regret        = output.regret_choice || '';
  const mistakeCtx    = output.mistake_context;
  const patternMatch  = output.pattern_match;

  return (
    <div className="space-y-6 self-stretch">

      {/* ── Friction Badge + Pipeline Trace ── */}
      <div className="flex items-center gap-3 flex-wrap">
        <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-widest border ${frictionColor}`}>
          {frictionLevel} FRICTION
        </span>
        {(pipelineExecuted || []).map((step, i) => (
          <span key={i} className="text-[10px] text-zinc-600 font-semibold tracking-wide">
            {i > 0 && <span className="mr-1 text-zinc-700">›</span>}
            {step}
          </span>
        ))}
      </div>

      {/* ── 1. CONTEXT EXPLANATION ── */}
      {contextExplanation && (
        <div className="bg-[#111213] border border-[#1e1e22] p-6 rounded-xl space-y-4">
          <div className="text-[10px] font-bold text-zinc-500 tracking-widest uppercase">Business Context Snapshot</div>
          <div className="text-[14px] text-zinc-300 leading-relaxed space-y-3 font-medium">
            {contextExplanation.split('\n').filter(Boolean).map((para, i) => (
              <p key={i}>{para}</p>
            ))}
          </div>
        </div>
      )}

      {/* ── 2. KEY STATS STRIP ── */}
      {keyStats.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
          {keyStats.map((stat, i) => (
            <div key={i} className="bg-[#111213] border border-[#1e1e22] rounded-xl p-4 flex flex-col justify-between">
              <div className="text-[10px] text-zinc-500 font-semibold uppercase tracking-wider mb-1.5">{stat.label}</div>
              <div className="flex items-center justify-between">
                <span className="text-[16px] font-bold text-white font-mono">{stat.value}</span>
                <TrendIcon trend={stat.trend} />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ── 3. STATS EXPLANATION ── */}
      {statsExplanation && (
        <div className="bg-[#111213] border border-[#1e1e22] p-6 rounded-xl space-y-4">
          <div className="text-[10px] font-bold text-zinc-500 tracking-widest uppercase">Statistical & Decision Logic</div>
          <div className="text-[14px] text-zinc-300 leading-relaxed font-medium">
            <p>{statsExplanation}</p>
          </div>
        </div>
      )}

      {/* ── 4. DECISION VERDICT ── */}
      <div className="bg-gradient-to-r from-blue-950/40 to-indigo-950/30 border border-blue-900/40 p-6 rounded-xl flex flex-col gap-3">
        <div>
          <div className="text-[10px] font-bold text-blue-400 tracking-widest uppercase mb-1.5">Decision Verdict</div>
          <div className="text-[18px] font-bold text-white leading-snug">{verdictText}</div>
        </div>
        {confidence > 0 && (
          <div className="flex items-center gap-3">
            <div className="flex-1 h-1.5 bg-[#1d1d2a] rounded-full overflow-hidden max-w-[200px]">
              <div className="h-full bg-blue-500 rounded-full" style={{ width: `${confidence}%` }} />
            </div>
            <span className="text-[11.5px] font-bold text-blue-400">{confidence}% confidence score</span>
          </div>
        )}
      </div>

      {/* ── 5. SPACIUS ACTION PLAN ── */}
      {actionPlan.length > 0 && (
        <div className="bg-[#111213] border border-blue-900/30 p-6 rounded-xl space-y-4">
          <div className="text-[10px] font-bold text-zinc-500 tracking-widest uppercase">Immediate Action Steps</div>
          <div className="space-y-4">
            {actionPlan.map((a, i) => (
              <div key={i} className="flex items-start gap-4 border-b border-[#1b1b1e] last:border-0 pb-4 last:pb-0">
                <div className="w-6 h-6 rounded-full bg-blue-600/20 border border-blue-600/30 text-blue-400 text-[11px] font-bold flex items-center justify-center flex-shrink-0 mt-0.5 font-mono">
                  {i + 1}
                </div>
                <div className="flex-1 space-y-1">
                  {a.title ? (
                    <>
                      <div className="text-[14px] text-zinc-200 font-bold leading-snug">{a.title}</div>
                      <div className="text-[13px] text-zinc-400 leading-relaxed font-medium">{a.step}</div>
                    </>
                  ) : (
                    <div className="text-[13.5px] text-zinc-300 leading-relaxed font-medium">{a.step}</div>
                  )}
                  <div className="text-[10.5px] text-zinc-500 font-mono pt-0.5">⏱ Timeframe: {a.timeframe}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── 6. COLLAPSIBLE DEEP AUDIT PANEL (De-congests the UI) ── */}
      <div className="border border-[#1e1e22] rounded-xl overflow-hidden bg-[#0d0d0e]">
        <button onClick={() => setShowAdvanced(s => !s)}
          className="w-full flex items-center justify-between px-5 py-4 bg-[#111213] hover:bg-[#161619] transition-all text-left">
          <div>
            <span className="text-[12px] font-bold text-zinc-400 uppercase tracking-wide">Friction Cognitive Pipeline Audit (16 Modules)</span>
            <div className="text-[10px] text-zinc-600 mt-0.5">Inspect root causes, department stances, risk metrics, and simulation details</div>
          </div>
          {showAdvanced ? <ChevronUp className="w-4 h-4 text-zinc-500" /> : <ChevronDown className="w-4 h-4 text-zinc-500" />}
        </button>

        {showAdvanced && (
          <div className="p-5 border-t border-[#1e1e22] space-y-5 bg-[#0a0a0b]">

            {/* Root Cause */}
            {rootCause && (
              <div className="bg-[#111213] border border-amber-900/30 p-4 rounded-xl flex items-start gap-3">
                <div className="w-6 h-6 rounded-lg bg-amber-900/30 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <GitBranch className="w-3.5 h-3.5 text-amber-400" />
                </div>
                <div>
                  <div className="text-[10px] font-bold text-amber-400 tracking-widest uppercase mb-1">Root Cause Analysis</div>
                  <div className="text-[12.5px] text-zinc-300">{rootCause}</div>
                </div>
              </div>
            )}

            {/* Department Analysis */}
            {departments.length > 0 && (
              <div className="space-y-2">
                <div className="text-[10px] font-bold text-zinc-500 tracking-widest uppercase pl-1">Department Alignment Debates</div>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  {departments.map((dept, i) => {
                    const isYes  = dept.status === 'yes';
                    const isNo   = dept.status === 'no';
                    const border = isYes ? 'border-emerald-900/40' : isNo ? 'border-red-900/30' : 'border-[#1e1e22]';
                    const badge  = isYes ? 'bg-emerald-900/50 text-emerald-400' : isNo ? 'bg-red-900/40 text-red-400' : 'bg-zinc-800 text-zinc-400';
                    return (
                      <div key={i} className={`bg-[#111213] border ${border} p-4 rounded-xl flex flex-col gap-2`}>
                        <div className="flex items-center justify-between">
                          <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-wide">{dept.name}</span>
                          <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded uppercase tracking-wide ${badge}`}>
                            {dept.status === 'yes' ? 'Support' : dept.status === 'no' ? 'Against' : 'Neutral'}
                          </span>
                        </div>
                        <div className="text-[12px] text-zinc-300 leading-snug">{dept.reason}</div>
                        {dept.score !== undefined && (
                          <div className="w-full h-1 bg-[#1d1d1f] rounded-full overflow-hidden mt-1">
                            <div className={`h-full rounded-full ${isYes ? 'bg-emerald-500' : isNo ? 'bg-red-500' : 'bg-zinc-500'}`}
                              style={{ width: `${dept.score}%` }} />
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Scenario Simulations */}
            {scenarios.length > 0 && (
              <div className="space-y-2">
                <button onClick={() => setShowScenarios(s => !s)}
                  className="w-full flex items-center justify-between text-[10px] font-bold text-zinc-500 tracking-widest uppercase pl-1 hover:text-zinc-300 transition">
                  <span>Scenario Simulation paths</span>
                  {showScenarios ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                </button>
                {showScenarios && (
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    {scenarios.map((sc, i) => {
                      const isRec = sc.recommended;
                      return (
                        <div key={i} className={`bg-[#111213] border rounded-xl p-4 space-y-2 relative
                          ${isRec ? 'border-blue-800/50 shadow-[0_0_12px_rgba(37,99,235,0.1)]' : 'border-[#1e1e22]'}`}>
                          {isRec && (
                            <div className="absolute -top-2 left-4 px-2 py-0.5 bg-blue-600 text-[9px] font-bold text-white rounded-full uppercase tracking-wide">
                              Recommended Option
                            </div>
                          )}
                          <div className="text-[11.5px] font-bold text-zinc-200 pt-1">{sc.name}</div>
                          {sc.description && <div className="text-[11px] text-zinc-500 leading-relaxed">{sc.description}</div>}
                          <div className="flex items-center justify-between text-[10px] pt-1">
                            <span className={`font-mono font-bold ${sc.revenue_impact?.startsWith('+') ? 'text-emerald-400' : 'text-red-400'}`}>
                              {sc.revenue_impact}
                            </span>
                            <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold uppercase ${badgeCls(sc.risk)}`}>
                              {sc.risk} Risk
                            </span>
                          </div>
                          {sc.breaking_assumption && (
                            <div className="text-[10px] text-zinc-600 italic border-t border-[#1e1e22] pt-2 mt-1">
                              Assumption break: {sc.breaking_assumption}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            )}

            {/* Regret Analysis */}
            {regret && (
              <div className="bg-[#111213] border border-[#1e1e22] p-4 rounded-xl flex items-start gap-3">
                <div className="w-6 h-6 rounded-lg bg-indigo-900/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <Target className="w-3.5 h-3.5 text-indigo-400" />
                </div>
                <div>
                  <div className="text-[10px] font-bold text-indigo-400 tracking-widest uppercase mb-1">Regret Simulation & Least-Regret Stance</div>
                  <div className="text-[12.5px] text-zinc-300">{regret}</div>
                </div>
              </div>
            )}

            {/* Devil's Advocate */}
            {devils.length > 0 && (
              <div className="space-y-1.5">
                <button onClick={() => setShowDevils(s => !s)}
                  className="w-full flex items-center justify-between text-[10px] font-bold text-zinc-500 tracking-widest uppercase pl-1 hover:text-zinc-300 transition">
                  <span>Devil's Advocate Counterarguments</span>
                  {showDevils ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                </button>
                {showDevils && (
                  <div className="bg-[#111213] border border-red-900/20 rounded-xl p-4 space-y-2">
                    {devils.map((d, i) => (
                      <div key={i} className="flex items-start gap-2.5 text-[12.5px] text-zinc-300">
                        <span className="text-red-400 font-bold mt-0.5 flex-shrink-0">?</span>
                        <span>{d}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Risk & Confidence Engine */}
            <div className="bg-[#111213] border border-[#1e1e22] p-5 rounded-xl space-y-4">
              <div className="flex items-center justify-between">
                <div className="text-[10px] font-bold text-zinc-500 tracking-widest uppercase">Confidence Weighting Breakdown</div>
                <span className="text-white text-[13px] font-mono font-bold">{confidence}% weight score</span>
              </div>
              <div className="grid grid-cols-2 gap-3.5">
                {[
                  { label: 'Department Agreement', val: breakdown.agreement || 0 },
                  { label: 'Memory Match score',   val: breakdown.memory_match || 0 },
                  { label: 'Evidence ground-truth', val: breakdown.evidence || evidenceScore || 0 },
                  { label: 'Scenario Stability',   val: breakdown.scenario_stability || 0 },
                ].map((bar, i) => (
                  <div key={i}>
                    <div className="flex items-center justify-between text-[10px] mb-1">
                      <span className="text-zinc-500 font-semibold">{bar.label}</span>
                      <span className="text-zinc-400 font-mono font-bold">{bar.val}%</span>
                    </div>
                    <div className="h-1 bg-[#1d1d1f] rounded-full overflow-hidden">
                      <div className="h-full bg-blue-500 rounded-full transition-all duration-700"
                        style={{ width: `${bar.val}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Constraints Validator */}
            {constraints.length > 0 && (
              <div className="bg-[#111213] border border-[#1e1e22] p-4 rounded-xl space-y-2.5">
                <div className="text-[10px] font-bold text-zinc-500 tracking-widest uppercase pl-1">Constraints Validator check</div>
                {constraints.map((c, i) => (
                  <div key={i} className="flex items-center gap-3 text-[12px] border-b border-[#161619] last:border-b-0 pb-1.5 last:pb-0">
                    <span className={`px-2 py-0.5 rounded text-[9px] font-bold uppercase ${badgeCls(c.status)}`}>{c.status}</span>
                    <span className="text-zinc-400 font-semibold">{c.name}</span>
                    <span className="text-zinc-500 flex-1 text-right">{c.detail}</span>
                  </div>
                ))}
              </div>
            )}

            {/* Risk If Ignored */}
            {ifIgnored.length > 0 && (
              <div className="bg-[#111213] border border-red-900/20 p-4 rounded-xl space-y-2">
                <div className="text-[10px] font-bold text-red-500 tracking-widest uppercase">Risk If Ignored (Unmitigated Consequences)</div>
                {ifIgnored.map((risk, i) => (
                  <div key={i} className="flex items-start gap-2 text-[12.5px] text-zinc-400">
                    <AlertTriangle className="w-3.5 h-3.5 text-red-500 flex-shrink-0 mt-0.5" />
                    <span>{risk}</span>
                  </div>
                ))}
              </div>
            )}

            {/* Memory / Patterns */}
            {(mistakeCtx || patternMatch) && (
              <div className="bg-[#111213] border border-purple-900/30 p-4 rounded-xl flex items-start gap-3">
                <div className="w-6 h-6 rounded-lg bg-purple-900/30 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <Brain className="w-3.5 h-3.5 text-purple-400" />
                </div>
                <div className="space-y-1">
                  <div className="text-[10px] font-bold text-purple-400 tracking-widest uppercase">Cerebra Business Memory</div>
                  {mistakeCtx && <div className="text-[12px] text-zinc-300">{mistakeCtx}</div>}
                  {patternMatch && <div className="text-[11px] text-purple-300 font-semibold mt-1">Cross-case Pattern: {patternMatch}</div>}
                </div>
              </div>
            )}

            {/* Self Review */}
            {selfReview && (
              <div className="space-y-1.5">
                <button onClick={() => setShowSelfReview(s => !s)}
                  className="w-full flex items-center justify-between text-[10px] font-bold text-zinc-500 tracking-widest uppercase pl-1 hover:text-zinc-400 transition">
                  <span>Reflective Self Review & Self Critique</span>
                  {showSelfReview ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                </button>
                {showSelfReview && (
                  <div className="bg-[#111213] border border-[#1e1e22] p-4 rounded-xl">
                    <p className="text-[12px] text-zinc-500 italic leading-relaxed">{selfReview}</p>
                  </div>
                )}
              </div>
            )}

          </div>
        )}
      </div>

    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════════════
//  PIPELINE STEP CONFIG (16 modules from the PDF)
// ══════════════════════════════════════════════════════════════════════════════
const ALL_PIPELINE_STEPS = [
  { label: 'Intent',         group: 'Understand', icon: Brain },
  { label: 'Friction',       group: 'Understand', icon: Zap },
  { label: 'Context',        group: 'Understand', icon: Database },
  { label: 'Memory',         group: 'Understand', icon: Clock },
  { label: 'Root Cause',     group: 'Analyze',    icon: GitBranch },
  { label: 'Debate',         group: 'Analyze',    icon: Users },
  { label: 'Evidence',       group: 'Analyze',    icon: Shield },
  { label: 'Scenarios',      group: 'Reason',     icon: BarChart2 },
  { label: "Devil's Advocate", group: 'Reason',   icon: AlertTriangle },
  { label: 'Regret',         group: 'Reason',     icon: Target },
  { label: 'Confidence',     group: 'Verify',     icon: Eye },
  { label: 'Constraints',    group: 'Verify',     icon: FileText },
  { label: 'Self Review',    group: 'Verify',     icon: Brain },
  { label: 'Synthesis',      group: 'Decide',     icon: Sparkles },
  { label: 'Explainability', group: 'Decide',     icon: FileText },
  { label: 'Learning',       group: 'Decide',     icon: TrendingUp },
];

const PHASE_COLORS = {
  Understand: 'text-blue-400',
  Analyze:    'text-amber-400',
  Reason:     'text-purple-400',
  Verify:     'text-emerald-400',
  Decide:     'text-rose-400',
};

// ══════════════════════════════════════════════════════════════════════════════
//  MAIN APP
// ══════════════════════════════════════════════════════════════════════════════
function App() {
  const [question, setQuestion]         = useState('');
  const [messages, setMessages]         = useState([]);
  const [loadingStepIdx, setLoadingIdx] = useState(null);
  const [isSidebarOpen, setSidebar]     = useState(true);
  const [dataSources, setDataSources]   = useState([]);
  const [sourcesLoading, setSrcLoading] = useState(true);
  const [activeSource, setActiveSource] = useState(null);
  const messagesEndRef = useRef(null);

  // Fetch data sources on mount
  useEffect(() => {
    axios.get(`${API}/data-sources`)
      .then(r => { setDataSources(r.data.sources || []); setSrcLoading(false); })
      .catch(() => {
        setDataSources([
          { id:'customers',  label:'Customers',     icon:'users',       row_count:30, status:'connected', summary:'Avg LTV $203,733 • 7 high-risk accounts', tags:['CRM', 'Retention'] },
          { id:'deals',      label:'Deals Pipeline',icon:'trending-up', row_count:40, status:'connected', summary:'Open pipeline $876,000 • 19 active deals', tags:['Sales', 'Pipeline'] },
          { id:'financials', label:'Financials',    icon:'bar-chart',   row_count:18, status:'connected', summary:'Latest revenue $1,375,000 • 28.9% avg margin', tags:['Finance', 'P&L'] },
          { id:'team',       label:'Team',          icon:'people',      row_count:15, status:'connected', summary:'15 employees • $1,262,000 annual payroll', tags:['HR', 'Talent'] },
          { id:'decisions',  label:'Past Decisions',icon:'clock',       row_count:25, status:'connected', summary:'18 successes • 7 failures', tags:['Memory', 'History'] },
          { id:'products',   label:'Products & SKUs',icon:'package',    row_count:20, status:'connected', summary:'YTD Product Rev $524,000 • Avg Margin 72%', tags:['Inventory', 'Margin'] },
          { id:'inventory',  label:'Inventory',     icon:'archive',     row_count:15, status:'connected', summary:'2 critical items need reorder • Avg Supply 26 days', tags:['Logistics', 'Warehouse'] },
          { id:'campaigns',  label:'Campaigns',     icon:'target',      row_count:15, status:'connected', summary:'Spent $298,000 • Overall ROI 620%', tags:['Marketing', 'ROI'] },
          { id:'support_tickets', label:'Support Tickets',icon:'help-circle',row_count:50, status:'connected', summary:'Avg CSAT 4.2/5 • 4 critical open tickets', tags:['Support', 'CSAT'] },
          { id:'suppliers',  label:'Suppliers',     icon:'truck',       row_count:10, status:'connected', summary:'Avg Reliability 89/100 • 1 high-risk supplier', tags:['Vendor', 'Operations'] },
          { id:'expenses',   label:'Expenses',      icon:'credit-card', row_count:18, status:'connected', summary:'Latest Monthly Expense $312,000', tags:['Finance', 'Expenses'] },
          { id:'kpis',       label:'KPIs',          icon:'activity',    row_count:6,  status:'connected', summary:'MRR $1,341,000 • NPS 52 • Churn 2.0%', tags:['KPIs', 'SaaS'] },
          { id:'contracts',  label:'Contracts & ARR',icon:'file-text',  row_count:15, status:'connected', summary:'Total ARR $5,640,000 • At-Risk ARR $1,260,000', tags:['Contracts', 'ARR'] },
        ]);
        setSrcLoading(false);
      });
  }, []);

  // Auto-scroll
  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages, loadingStepIdx]);

  // Animate pipeline steps while loading
  useEffect(() => {
    const loading = messages.find(m => m.loading);
    if (!loading) { setLoadingIdx(null); return; }
    setLoadingIdx(0);
    const iv = setInterval(() => {
      setLoadingIdx(prev => {
        if (prev === null) return 0;
        return prev < ALL_PIPELINE_STEPS.length - 1 ? prev + 1 : prev;
      });
    }, 500);
    return () => clearInterval(iv);
  }, [messages]);

  const handleSubmit = async (text) => {
    const q = text || question;
    if (!q.trim()) return;
    const id = Date.now();
    setMessages(prev => [...prev, { id, question: q, result: null, loading: true }]);
    setQuestion('');
    try {
      const r = await axios.post(`${API}/reason`, { question: q });
      setMessages(prev => prev.map(m => m.id === id ? { ...m, result: r.data, loading: false } : m));
    } catch {
      // Fallback
      setTimeout(() => {
        setMessages(prev => prev.map(m => m.id === id ? {
          ...m, loading: false, result: {
            friction_level: 'MEDIUM',
            pipeline_executed: ['Intent', 'Friction', 'Context', 'Memory'],
            intent: { goal: 'strategic analysis', constraints: [] },
            past_memory: 'Backend offline — running in simulation mode.',
            past_memory_score: 0,
            output: {
              verdict: 'Unable to reach backend. Run the backend server.',
              narrative: 'The Friction backend is not responding. Please start the backend server with: python main.py',
              key_stats: [],
              departments: [],
              confidence: 0,
              confidence_breakdown: {},
              action_plan: [{ step: 'Start the backend server', timeframe: 'now' }],
              if_ignored: [],
              scenarios: [],
              devils_advocate: [],
              regret_choice: '',
              constraints_check: [],
              self_review: '',
              root_cause_summary: '',
              evidence_score: 0,
            },
            confidence: { confidence: 0, agreement_score: 0, memory_match: 0 }
          }
        } : m));
      }, 2000);
    }
  };

  const currentLoading = messages.find(m => m.loading);

  return (
    <div className="flex h-screen bg-[#0d0d0e] text-[#e4e4e7] overflow-hidden font-sans">

      {/* ═══════ DATA VIEWER MODAL ═══════ */}
      {activeSource && <DataViewer source={activeSource} onClose={() => setActiveSource(null)} />}

      {/* ═══════ SIDEBAR ═══════ */}
      {isSidebarOpen && (
        <div className="w-[268px] bg-[#111112] border-r border-[#1c1c1f] flex flex-col flex-shrink-0 select-none">
          <div className="flex-1 overflow-y-auto p-5 space-y-7">
            {/* Logo */}
            <div className="flex items-center gap-3 pt-1">
              <div className="w-6 h-6 bg-white rounded-md flex-shrink-0 shadow-[0_0_10px_rgba(255,255,255,0.12)]" />
              <span className="text-[17px] font-bold text-white tracking-wide">Friction</span>
            </div>

            {/* ── DATA SOURCES ── */}
            <div className="space-y-2.5">
              <div className="flex items-center justify-between">
                <span className="text-[9.5px] font-bold text-zinc-500 tracking-widest uppercase">Data Sources</span>
                {sourcesLoading
                  ? <Loader2 className="w-3 h-3 text-zinc-600 animate-spin" />
                  : <span className="text-[10px] text-zinc-700 font-semibold">{dataSources.length} connected</span>
                }
              </div>
              <ul className="space-y-1">
                {dataSources.map(src => (
                  <li key={src.id}>
                    <button onClick={() => setActiveSource(src)}
                      className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl border border-transparent hover:bg-[#161618] hover:border-[#222224] transition-all group text-left">
                      <div className="w-7 h-7 rounded-lg bg-[#1a1a1c] group-hover:bg-[#1e1e21] flex items-center justify-center flex-shrink-0 transition">
                        <SrcIcon name={src.icon} className="w-3.5 h-3.5 text-zinc-500 group-hover:text-blue-400 transition" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <span className="text-[12px] font-semibold text-zinc-400 group-hover:text-white transition">{src.label}</span>
                          <div className="flex items-center gap-1.5">
                            <span className="text-[10px] font-mono text-zinc-600">{src.row_count}</span>
                            <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full shadow-[0_0_5px_#10b981]" />
                          </div>
                        </div>
                        <div className="text-[10px] text-zinc-700 truncate mt-0.5">{src.summary}</div>
                      </div>
                    </button>
                  </li>
                ))}
              </ul>
              <button className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-transparent border border-[#1e1e21] hover:border-zinc-700 hover:bg-[#161618] text-zinc-600 hover:text-zinc-300 rounded-xl text-[11px] font-semibold tracking-wide transition">
                <Plus className="w-3.5 h-3.5" />Connect source
              </button>
            </div>

            {/* ── PIPELINE ── */}
            <div className="space-y-2">
              <div className="text-[9.5px] font-bold text-zinc-500 tracking-widest uppercase">Cognitive Pipeline</div>
              {['Understand','Analyze','Reason','Verify','Decide'].map(phase => (
                <div key={phase} className="space-y-1">
                  <div className={`text-[9px] font-bold uppercase tracking-widest pl-1 ${PHASE_COLORS[phase]}`}>{phase}</div>
                  {ALL_PIPELINE_STEPS.filter(s => s.group === phase).map((step, si) => {
                    const globalIdx = ALL_PIPELINE_STEPS.findIndex(x => x.label === step.label);
                    let icon, textClass = 'text-zinc-600';
                    const lastResult = messages.filter(m => !m.loading && m.result).slice(-1)[0];
                    const executed = lastResult?.result?.pipeline_executed || [];
                    const wasExecuted = executed.some(e =>
                      e.toLowerCase().replace(/[' ]/g,'') === step.label.toLowerCase().replace(/[' ]/g,'')
                    );

                    if (currentLoading) {
                      if (globalIdx < loadingStepIdx) {
                        icon = <Check className="w-3.5 h-3.5 text-emerald-500 stroke-[3]" />;
                        textClass = 'text-zinc-400';
                      } else if (globalIdx === loadingStepIdx) {
                        icon = <Loader2 className="w-3.5 h-3.5 text-blue-400 animate-spin" />;
                        textClass = `${PHASE_COLORS[phase]} font-semibold animate-pulse`;
                      } else {
                        icon = <div className="w-1.5 h-1.5 bg-zinc-800 rounded-full mx-1" />;
                      }
                    } else if (wasExecuted) {
                      icon = <Check className="w-3.5 h-3.5 text-emerald-500 stroke-[3]" />;
                      textClass = 'text-zinc-400';
                    } else if (messages.length > 0) {
                      icon = <div className="w-1.5 h-1.5 bg-zinc-800 rounded-full mx-1" />;
                      textClass = 'text-zinc-700';
                    } else {
                      icon = <div className="w-1.5 h-1.5 bg-zinc-800 rounded-full mx-1" />;
                    }

                    return (
                      <div key={step.label} className="flex items-center gap-2.5 pl-2">
                        <div className="w-4 h-4 flex items-center justify-center flex-shrink-0">{icon}</div>
                        <span className={`text-[11px] leading-none ${textClass}`}>{step.label}</span>
                      </div>
                    );
                  })}
                </div>
              ))}
            </div>
          </div>

          {/* Footer */}
          <div className="px-5 py-3.5 border-t border-[#1a1a1c] flex items-center justify-between">
            <span className="text-[10px] text-zinc-700 font-medium">v2.0 · 16 Modules</span>
            <button onClick={() => { setSrcLoading(true);
              axios.get(`${API}/data-sources`)
                .then(r => { setDataSources(r.data.sources||[]); setSrcLoading(false); })
                .catch(() => setSrcLoading(false)); }}
              className="text-zinc-600 hover:text-zinc-400 transition" title="Refresh">
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}

      {/* ═══════ MAIN CONTENT ═══════ */}
      <div className="flex-1 flex flex-col h-screen overflow-hidden bg-[#0d0d0e]">
        {/* Header */}
        <div className="h-14 border-b border-[#1a1a1c] px-6 flex items-center justify-between flex-shrink-0">
          <div className="flex items-center gap-2">
            {!isSidebarOpen && (
              <button onClick={() => setSidebar(true)}
                className="w-8 h-8 rounded-lg bg-[#161617] border border-[#232325] flex items-center justify-center hover:bg-zinc-800 transition">
                <ChevronRight className="w-4 h-4 text-zinc-400" />
              </button>
            )}
            <span className="text-xs font-bold text-zinc-600 uppercase tracking-widest">
              {messages.length > 0 ? 'Active Session' : 'New Reasoning Session'}
            </span>
          </div>
          {isSidebarOpen && (
            <button onClick={() => setSidebar(false)}
              className="text-zinc-600 hover:text-zinc-300 text-xs font-medium px-2.5 py-1 rounded bg-[#161617] border border-[#232325] transition">
              Hide
            </button>
          )}
        </div>

        {/* Chat area */}
        <div className="flex-1 overflow-y-auto px-8 py-6 space-y-8 max-w-4xl w-full mx-auto flex flex-col">

          {messages.length === 0 ? (
            <div className="flex-1 flex flex-col items-center justify-center text-center py-16 space-y-6">
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-blue-600 to-indigo-700 flex items-center justify-center shadow-lg shadow-blue-500/10">
                <Sparkles className="w-6 h-6 text-white" />
              </div>
              <div className="space-y-2">
                <h2 className="text-xl font-bold text-white tracking-tight">Friction Decision Engine</h2>
                <p className="text-zinc-500 text-sm max-w-md">
                  A 16-module cognitive pipeline: Intent → Friction Routing → Context → Memory → Root Cause → Debate → Evidence → Scenarios → Synthesis.
                  Grounded in your real CRM data.
                </p>
              </div>
              {/* Dataset quick-view pills */}
              {dataSources.length > 0 && (
                <div className="flex gap-2 flex-wrap justify-center pt-2">
                  {dataSources.map(src => (
                    <button key={src.id} onClick={() => setActiveSource(src)}
                      className="flex items-center gap-1.5 px-3 py-1.5 bg-[#131314] border border-[#1e1e21] hover:border-zinc-700 rounded-lg text-[11px] font-semibold text-zinc-500 hover:text-zinc-200 transition group">
                      <SrcIcon name={src.icon} className="w-3 h-3 text-blue-500" />
                      {src.row_count} {src.label}
                      <ArrowUpRight className="w-2.5 h-2.5 text-zinc-700 group-hover:text-zinc-400" />
                    </button>
                  ))}
                </div>
              )}
              {/* Starter queries */}
              <div className="w-full max-w-xl grid grid-cols-2 gap-2.5 pt-2">
                {[
                  { q: 'Should we hire more sales reps?',     desc: 'Team capacity & pipeline analysis' },
                  { q: 'Should we open another branch?',       desc: 'Expansion risk & past cases' },
                  { q: 'What is our biggest customer risk?',   desc: 'Churn & retention deep-dive' },
                  { q: 'Should we delay the product launch?',  desc: 'Tech readiness & market timing' },
                ].map((s, i) => (
                  <button key={i} onClick={() => handleSubmit(s.q)}
                    className="flex flex-col items-start text-left p-4 bg-[#121213] border border-[#212123] rounded-xl hover:border-zinc-700 hover:bg-[#18181a] transition group">
                    <div className="flex items-center justify-between w-full">
                      <span className="text-[12.5px] font-semibold text-zinc-300 group-hover:text-white transition">{s.q}</span>
                      <ArrowUpRight className="w-3 h-3 text-zinc-600 group-hover:text-zinc-300 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-all" />
                    </div>
                    <span className="text-[11px] text-zinc-600 mt-1">{s.desc}</span>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map(msg => (
              <div key={msg.id} className="space-y-4 flex flex-col">
                {/* User bubble */}
                <div className="flex items-center justify-between self-end bg-[#161617] border border-[#232325] rounded-xl px-4 py-2.5 max-w-lg">
                  <span className="text-[13px] font-medium text-zinc-100 pr-3">{msg.question}</span>
                  <MoreHorizontal className="w-4 h-4 text-zinc-600 flex-shrink-0" />
                </div>

                {msg.loading ? (
                  <div className="bg-[#111213] border border-[#1e1e22] rounded-xl p-8 flex flex-col items-center space-y-4">
                    <Loader2 className="w-7 h-7 text-blue-500 animate-spin" />
                    <div className="text-center">
                      <div className="text-[11px] font-bold text-zinc-400 uppercase tracking-widest animate-pulse">
                        Module {(loadingStepIdx || 0) + 1} of {ALL_PIPELINE_STEPS.length}
                      </div>
                      <div className={`text-[14px] font-bold mt-1 ${PHASE_COLORS[ALL_PIPELINE_STEPS[loadingStepIdx||0]?.group]}`}>
                        {ALL_PIPELINE_STEPS[loadingStepIdx || 0]?.group} Phase
                      </div>
                      <div className="text-[12px] text-zinc-500 mt-0.5">
                        {ALL_PIPELINE_STEPS[loadingStepIdx || 0]?.label}
                      </div>
                    </div>
                  </div>
                ) : (
                  msg.result && (
                    <RichOutputCard
                      output={msg.result.output}
                      frictionLevel={msg.result.friction_level}
                      pipelineExecuted={msg.result.pipeline_executed}
                    />
                  )
                )}
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input bar */}
        <div className="p-6 bg-[#0d0d0e] border-t border-[#1a1a1c] flex-shrink-0 flex justify-center">
          <div className="max-w-4xl w-full flex gap-3">
            <input
              className="flex-1 bg-[#161617] border border-[#232325] text-zinc-200 text-[13.5px] rounded-xl px-4 py-3.5 placeholder-zinc-600 focus:outline-none focus:border-zinc-600 transition"
              placeholder="Ask a strategic business question…"
              value={question}
              onChange={e => setQuestion(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && !currentLoading && handleSubmit()}
              disabled={!!currentLoading}
            />
            <button
              onClick={() => handleSubmit()}
              disabled={!!currentLoading || !question.trim()}
              className="bg-[#161617] border border-[#232325] hover:bg-zinc-800 text-zinc-300 hover:text-white p-3.5 rounded-xl transition flex items-center justify-center disabled:opacity-40">
              <Play className="w-4 h-4 fill-current stroke-none" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
