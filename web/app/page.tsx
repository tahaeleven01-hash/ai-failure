import Link from "next/link";
import { getAllCases, getRegistryStats } from "@/lib/registry";
import { Terminal, Shield, Cpu, ArrowRight, CheckCircle2, AlertTriangle, Layers } from "lucide-react";

export default function HomePage() {
  const cases = getAllCases();
  const stats = getRegistryStats();

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-16">
      {/* Editorial Hero */}
      <section className="space-y-6 pt-4 sm:pt-10 max-w-4xl">
        <div className="inline-flex items-center space-x-2 px-2.5 py-1 rounded bg-surface border border-surface-border text-xs font-mono text-secondary">
          <span className="w-2 h-2 rounded-full bg-accent animate-pulse" />
          <span>AFM v0.1.0 — Open Source Registry</span>
        </div>

        <h1 className="text-3xl sm:text-5xl font-mono font-bold tracking-tight text-primary leading-tight">
          Turning AI coding agent mistakes into structured, reproducible benchmarks.
        </h1>

        <p className="text-base sm:text-lg text-secondary leading-relaxed font-sans">
          AI coding agents frequently invent non-existent APIs, wipe directories during refactoring,
          and comment out failing test assertions to claim false success. The AI Failure Museum transforms
          these real-world failures into machine-readable, sandboxed, and testable evaluation cases.
        </p>

        <div className="flex flex-wrap gap-3 pt-2">
          <Link
            href="/failures"
            className="inline-flex items-center space-x-2 px-5 py-2.5 rounded bg-accent hover:bg-accent-dim text-background font-mono font-semibold text-sm transition-colors"
          >
            <span>Explore Failures</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
          <Link
            href="/docs"
            className="inline-flex items-center space-x-2 px-5 py-2.5 rounded bg-surface hover:bg-surface-elevated text-primary border border-surface-border font-mono text-sm transition-colors"
          >
            <span>CLI Quickstart</span>
          </Link>
        </div>
      </section>

      {/* Verified Registry Statistics */}
      <section className="border-t border-b border-surface-border py-8 grid grid-cols-2 md:grid-cols-4 gap-6">
        <div>
          <div className="text-xs font-mono text-secondary uppercase tracking-wider">Total Cataloged</div>
          <div className="text-3xl font-mono font-bold text-primary mt-1">{stats.total_cases}</div>
          <div className="text-xs text-secondary mt-0.5">Verified definitions</div>
        </div>

        <div>
          <div className="text-xs font-mono text-secondary uppercase tracking-wider">Reproducible</div>
          <div className="text-3xl font-mono font-bold text-accent mt-1">{stats.reproducible_cases}</div>
          <div className="text-xs text-secondary mt-0.5">Executable in container</div>
        </div>

        <div>
          <div className="text-xs font-mono text-secondary uppercase tracking-wider">Synthetic Doubles</div>
          <div className="text-3xl font-mono font-bold text-primary mt-1">{stats.synthetic_cases}</div>
          <div className="text-xs text-secondary mt-0.5">Labeled framework tests</div>
        </div>

        <div>
          <div className="text-xs font-mono text-secondary uppercase tracking-wider">Real World</div>
          <div className="text-3xl font-mono font-bold text-primary mt-1">{stats.real_cases}</div>
          <div className="text-xs text-secondary mt-0.5">Community reported</div>
        </div>
      </section>

      {/* Search & Case Highlights */}
      <section className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-mono font-bold text-primary">Featured Failure Cases</h2>
            <p className="text-xs text-secondary mt-1">
              Deterministic, sandboxed reproductions included with the repository.
            </p>
          </div>
          <Link
            href="/failures"
            className="text-xs font-mono text-accent hover:underline flex items-center space-x-1"
          >
            <span>View All ({cases.length})</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {cases.map((caseItem) => (
            <Link
              key={caseItem.id}
              href={`/failures/${caseItem.id}`}
              className="group block p-5 rounded bg-surface border border-surface-border hover:border-accent/50 transition-colors"
            >
              <div className="flex items-center justify-between text-xs font-mono mb-2">
                <span className="text-accent font-semibold">{caseItem.id}</span>
                <span className="px-2 py-0.5 rounded bg-surface-elevated text-secondary border border-surface-border text-[11px]">
                  {caseItem.status}
                </span>
              </div>

              <h3 className="font-mono text-sm font-semibold text-primary group-hover:text-accent transition-colors line-clamp-2">
                {caseItem.title}
              </h3>

              <p className="text-xs text-secondary mt-2 line-clamp-2 leading-relaxed">
                {caseItem.description}
              </p>

              <div className="mt-4 pt-3 border-t border-surface-border flex items-center justify-between text-[11px] font-mono text-secondary">
                <span>{caseItem.agent.name}</span>
                <span className="text-secondary/70">{caseItem.categories[0]}</span>
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* Architectural Principles */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-6">
        <div className="p-6 rounded bg-surface border border-surface-border space-y-3">
          <div className="w-9 h-9 rounded bg-surface-elevated border border-surface-border flex items-center justify-center text-accent">
            <Shield className="w-4 h-4" />
          </div>
          <h3 className="font-mono text-sm font-semibold text-primary">Sandboxed Containment</h3>
          <p className="text-xs text-secondary leading-relaxed">
            Reproduction procedures run inside isolated Docker containers with non-root privileges,
            network disabled by default, and strict CPU & memory boundaries. Never run untrusted code on the host.
          </p>
        </div>

        <div className="p-6 rounded bg-surface border border-surface-border space-y-3">
          <div className="w-9 h-9 rounded bg-surface-elevated border border-surface-border flex items-center justify-center text-accent">
            <Cpu className="w-4 h-4" />
          </div>
          <h3 className="font-mono text-sm font-semibold text-primary">Pluggable Evaluation</h3>
          <p className="text-xs text-secondary leading-relaxed">
            Separate failure reproduction from agent evaluation. Test Claude Code, Codex, or Gemini CLI
            against the original failure prompt to verify whether a model or harness update resolves the issue.
          </p>
        </div>

        <div className="p-6 rounded bg-surface border border-surface-border space-y-3">
          <div className="w-9 h-9 rounded bg-surface-elevated border border-surface-border flex items-center justify-center text-accent">
            <Layers className="w-4 h-4" />
          </div>
          <h3 className="font-mono text-sm font-semibold text-primary">Community Maintained</h3>
          <p className="text-xs text-secondary leading-relaxed">
            Human-editable YAML case definitions validated with Pydantic v2 and JSON Schema.
            Contribute real agent failures via pull requests using the guided CLI wizard.
          </p>
        </div>
      </section>
    </div>
  );
}
