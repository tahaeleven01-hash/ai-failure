import { notFound } from "next/navigation";
import Link from "next/link";
import { getCaseById, getAllCases } from "@/lib/registry";
import { ArrowLeft, Terminal, Shield, FileText, CheckCircle2, AlertCircle, Copy } from "lucide-react";

export function generateStaticParams() {
  const cases = getAllCases();
  return cases.map((c) => ({ id: c.id }));
}

export default function FailureDetailPage({
  params,
}: {
  params: { id: string };
}) {
  const caseItem = getCaseById(params.id);

  if (!caseItem) {
    notFound();
  }

  const relatedCases = getAllCases()
    .filter((c) => c.id !== caseItem.id && c.categories.some((cat) => caseItem.categories.includes(cat)))
    .slice(0, 3);

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-10">
      {/* Navigation Breadcrumb */}
      <div>
        <Link
          href="/failures"
          className="inline-flex items-center space-x-1.5 text-xs font-mono text-secondary hover:text-accent transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Explorer</span>
        </Link>
      </div>

      {/* Header Info */}
      <div className="space-y-4 pb-6 border-b border-surface-border">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm font-mono font-bold text-accent px-2 py-0.5 rounded bg-accent/10 border border-accent/30">
            {caseItem.id}
          </span>
          <span className="text-xs font-mono px-2 py-0.5 rounded bg-surface border border-surface-border text-secondary">
            Status: <strong className="text-primary">{caseItem.status}</strong>
          </span>
          {caseItem.is_synthetic && (
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-surface border border-surface-border text-secondary">
              Synthetic Test Case
            </span>
          )}
          <span className="text-xs font-mono text-secondary ml-auto">
            Submitted {caseItem.submission.date} by @{caseItem.submission.submitted_by}
          </span>
        </div>

        <h1 className="text-2xl sm:text-3xl font-mono font-bold text-primary leading-tight">
          {caseItem.title}
        </h1>

        <div className="flex flex-wrap gap-1.5 pt-1">
          {caseItem.categories.map((cat) => (
            <span
              key={cat}
              className="px-2 py-0.5 rounded bg-surface border border-surface-border text-xs font-mono text-secondary"
            >
              {cat}
            </span>
          ))}
        </div>
      </div>

      {/* Summary */}
      <section className="space-y-3">
        <h2 className="text-xs font-mono uppercase tracking-wider text-secondary">
          Summary & Diagnostic Impact
        </h2>
        <div className="p-4 rounded bg-surface border border-surface-border text-sm text-secondary leading-relaxed">
          {caseItem.description}
        </div>
      </section>

      {/* Original Task & Prompt */}
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-xs font-mono uppercase tracking-wider text-secondary">
            Original Task & Prompt
          </h2>
          <span className="text-xs font-mono text-secondary">
            Target Agent: <strong className="text-primary">{caseItem.agent.name}</strong>
          </span>
        </div>

        <div className="p-4 rounded bg-surface border border-surface-border font-mono text-xs text-primary space-y-3">
          <div className="text-secondary text-[11px] uppercase tracking-wider">User Instruction:</div>
          <pre className="p-3 rounded bg-background border border-surface-border whitespace-pre-wrap">
            {caseItem.task.prompt}
          </pre>

          {caseItem.task.context && (
            <div className="pt-2">
              <div className="text-secondary text-[11px] uppercase tracking-wider">Context & Environment:</div>
              <p className="mt-1 text-secondary font-sans text-xs">{caseItem.task.context}</p>
            </div>
          )}

          {caseItem.task.target_files && caseItem.task.target_files.length > 0 && (
            <div className="pt-2">
              <div className="text-secondary text-[11px] uppercase tracking-wider">Target Files:</div>
              <ul className="mt-1 list-disc list-inside text-secondary text-xs">
                {caseItem.task.target_files.map((f) => (
                  <li key={f} className="text-primary">{f}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </section>

      {/* Behavior Contrast Grid */}
      <section className="space-y-3">
        <h2 className="text-xs font-mono uppercase tracking-wider text-secondary">
          Behavior Contrast Analysis
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 rounded bg-surface border border-surface-border space-y-2">
            <div className="flex items-center space-x-2 text-xs font-mono font-semibold text-green-400">
              <CheckCircle2 className="w-4 h-4" />
              <span>Expected Behavior</span>
            </div>
            <p className="text-xs text-secondary leading-relaxed font-sans">
              {caseItem.behavior.expected}
            </p>
          </div>

          <div className="p-4 rounded bg-surface border border-surface-border space-y-2">
            <div className="flex items-center space-x-2 text-xs font-mono font-semibold text-accent">
              <AlertCircle className="w-4 h-4" />
              <span>Observed Flawed Behavior</span>
            </div>
            <p className="text-xs text-secondary leading-relaxed font-sans">
              {caseItem.behavior.observed}
            </p>
          </div>
        </div>
      </section>

      {/* Reproduction Sandbox & Assertions */}
      <section className="space-y-3">
        <h2 className="text-xs font-mono uppercase tracking-wider text-secondary">
          Container Reproduction Specification
        </h2>

        <div className="p-5 rounded bg-surface border border-surface-border space-y-4 font-mono text-xs">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pb-4 border-b border-surface-border text-secondary">
            <div>
              <div className="text-[10px] uppercase">Engine</div>
              <div className="text-primary font-semibold mt-0.5">{caseItem.reproduction.type}</div>
            </div>
            <div>
              <div className="text-[10px] uppercase">Docker Image</div>
              <div className="text-primary font-semibold mt-0.5">{caseItem.environment.docker_image || "default"}</div>
            </div>
            <div>
              <div className="text-[10px] uppercase">Timeout</div>
              <div className="text-primary font-semibold mt-0.5">{caseItem.reproduction.timeout_seconds}s</div>
            </div>
            <div>
              <div className="text-[10px] uppercase">Network</div>
              <div className="text-primary font-semibold mt-0.5">
                {caseItem.reproduction.requires_network ? "Enabled" : "Isolated (none)"}
              </div>
            </div>
          </div>

          <div className="space-y-1">
            <div className="text-secondary text-[11px] uppercase">CLI Reproduction Command:</div>
            <div className="p-2.5 rounded bg-background border border-surface-border text-accent flex items-center justify-between">
              <span>afm reproduce {caseItem.id}</span>
            </div>
          </div>

          {caseItem.reproduction_code && (
            <div className="space-y-1.5 pt-2">
              <div className="text-secondary text-[11px] uppercase">
                Reproduction Script ({caseItem.reproduction.entrypoint || "repro.py"}):
              </div>
              <pre className="p-3 rounded bg-background border border-surface-border text-xs text-primary overflow-x-auto max-h-60 leading-relaxed font-mono">
                {caseItem.reproduction_code}
              </pre>
            </div>
          )}

          {caseItem.reproduction.assertions && caseItem.reproduction.assertions.length > 0 && (
            <div className="space-y-2 pt-2">
              <div className="text-secondary text-[11px] uppercase">Automated Verification Assertions:</div>
              <div className="space-y-2">
                {caseItem.reproduction.assertions.map((rule, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded bg-background border border-surface-border flex flex-col sm:flex-row sm:items-center justify-between text-xs gap-2"
                  >
                    <div>
                      <span className="font-semibold text-primary">{rule.type}</span>
                      <span className="text-secondary ml-2 font-mono">value: &quot;{rule.value}&quot;</span>
                    </div>
                    {rule.description && (
                      <span className="text-secondary text-[11px] font-sans">{rule.description}</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </section>

      {/* Verification & Evidence */}
      <section className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="p-5 rounded bg-surface border border-surface-border space-y-3">
          <h2 className="text-xs font-mono uppercase tracking-wider text-secondary">
            Verification Methodology
          </h2>
          <div className="text-xs space-y-2 text-secondary font-sans">
            <div>
              <span className="font-mono text-primary font-semibold">Method: </span>
              <span>{caseItem.verification.method_type}</span>
            </div>
            {caseItem.verification.test_runner && (
              <div>
                <span className="font-mono text-primary font-semibold">Runner: </span>
                <code className="text-accent">{caseItem.verification.test_runner}</code>
              </div>
            )}
            <div>
              <span className="font-mono text-primary font-semibold">Failure Criteria: </span>
              <p className="mt-1 text-secondary leading-relaxed">{caseItem.verification.failure_criteria}</p>
            </div>
          </div>
        </div>

        <div className="p-5 rounded bg-surface border border-surface-border space-y-3">
          <h2 className="text-xs font-mono uppercase tracking-wider text-secondary">
            Attached Evidence ({caseItem.evidence.length})
          </h2>
          <div className="space-y-3 text-xs font-mono">
            {caseItem.evidence.length === 0 ? (
              <span className="text-secondary font-sans">No external evidence files attached.</span>
            ) : (
              caseItem.evidence.map((ev, idx) => (
                <div
                  key={idx}
                  className="p-3 rounded bg-background border border-surface-border space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <span className="text-[10px] uppercase px-1.5 py-0.5 rounded bg-surface-elevated text-secondary border border-surface-border">
                        {ev.type}
                      </span>
                      <span className="text-primary truncate max-w-[200px] font-medium">{ev.path_or_url}</span>
                    </div>
                    {ev.description && (
                      <span className="text-secondary text-[11px] font-sans truncate max-w-[150px]">
                        {ev.description}
                      </span>
                    )}
                  </div>
                  {ev.content && (
                    <pre className="p-2.5 rounded bg-surface text-[11px] text-secondary font-mono overflow-x-auto max-h-40 whitespace-pre-wrap border border-surface-border/50">
                      {ev.content}
                    </pre>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </section>

      {/* Related Failure Cases */}
      {relatedCases.length > 0 && (
        <section className="space-y-4 pt-6 border-t border-surface-border">
          <h2 className="text-sm font-mono font-bold text-primary">Related Failure Cases</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {relatedCases.map((rc) => (
              <Link
                key={rc.id}
                href={`/failures/${rc.id}`}
                className="p-4 rounded bg-surface border border-surface-border hover:border-accent/40 transition-colors block"
              >
                <div className="text-xs font-mono text-accent font-semibold">{rc.id}</div>
                <div className="text-xs font-mono text-primary mt-1 line-clamp-1">{rc.title}</div>
                <div className="text-[11px] text-secondary mt-1">{rc.agent.name}</div>
              </Link>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
