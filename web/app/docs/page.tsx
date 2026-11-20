import { Terminal, Shield, BookOpen, Layers, Code } from "lucide-react";

export default function DocsPage() {
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-12">
      {/* Header */}
      <div className="space-y-3">
        <div className="inline-flex items-center space-x-2 text-xs font-mono text-accent">
          <BookOpen className="w-4 h-4" />
          <span>Technical Documentation</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-mono font-bold text-primary">
          AI Failure Museum Documentation
        </h1>
        <p className="text-sm text-secondary leading-relaxed">
          Comprehensive guides covering local installation, CLI tool commands, security isolation
          boundaries, JSON schema specifications, and evaluation adapters.
        </p>
      </div>

      {/* Quick Navigation */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
        <a href="#installation" className="p-3 rounded bg-surface border border-surface-border hover:border-accent transition-colors block text-center text-primary">
          # Installation
        </a>
        <a href="#cli" className="p-3 rounded bg-surface border border-surface-border hover:border-accent transition-colors block text-center text-primary">
          # CLI Reference
        </a>
        <a href="#security" className="p-3 rounded bg-surface border border-surface-border hover:border-accent transition-colors block text-center text-primary">
          # Security & Sandbox
        </a>
        <a href="#schema" className="p-3 rounded bg-surface border border-surface-border hover:border-accent transition-colors block text-center text-primary">
          # Schema & Taxonomy
        </a>
      </div>

      {/* Section 1: Installation */}
      <section id="installation" className="space-y-4 pt-6 border-t border-surface-border">
        <h2 className="text-xl font-mono font-bold text-primary flex items-center space-x-2">
          <Terminal className="w-5 h-5 text-accent" />
          <span>1. Installation & Environment</span>
        </h2>
        <p className="text-xs text-secondary leading-relaxed">
          AFM is built with Python 3.11+. It runs completely on local hardware without cloud accounts or paid tokens.
        </p>
        <div className="p-4 rounded bg-surface border border-surface-border font-mono text-xs text-primary space-y-2">
          <div className="text-secondary"># Clone repository</div>
          <div>git clone https://github.com/your-org/ai-failure-museum.git</div>
          <div>cd ai-failure-museum</div>
          <div className="pt-2 text-secondary"># Install package in editable mode</div>
          <div>pip install -e .</div>
          <div className="pt-2 text-secondary"># Check environment diagnostics</div>
          <div className="text-accent">afm doctor</div>
        </div>
      </section>

      {/* Section 2: CLI Reference */}
      <section id="cli" className="space-y-4 pt-6 border-t border-surface-border">
        <h2 className="text-xl font-mono font-bold text-primary flex items-center space-x-2">
          <Code className="w-5 h-5 text-accent" />
          <span>2. CLI Command Reference</span>
        </h2>
        <div className="space-y-3 text-xs">
          <div className="p-4 rounded bg-surface border border-surface-border space-y-2">
            <div className="font-mono text-primary font-bold">afm list</div>
            <p className="text-secondary">
              Lists registered failure cases. Supports filtering via <code>--category</code>, <code>--status</code>, <code>--agent</code>, and output via <code>--format json</code>.
            </p>
          </div>

          <div className="p-4 rounded bg-surface border border-surface-border space-y-2">
            <div className="font-mono text-primary font-bold">afm show &lt;case-id&gt;</div>
            <p className="text-secondary">
              Renders full technical details, behavior comparison, environment requirements, and reproduction procedure.
            </p>
          </div>

          <div className="p-4 rounded bg-surface border border-surface-border space-y-2">
            <div className="font-mono text-primary font-bold">afm validate [case-id]</div>
            <p className="text-secondary">
              Validates YAML case definitions against the JSON Schema, checks referenced evidence paths, and flags any unredacted secrets.
            </p>
          </div>

          <div className="p-4 rounded bg-surface border border-surface-border space-y-2">
            <div className="font-mono text-primary font-bold">afm reproduce &lt;case-id&gt;</div>
            <p className="text-secondary">
              Executes the reproduction procedure inside an isolated Docker container with strict CPU, memory, and network boundaries.
            </p>
          </div>

          <div className="p-4 rounded bg-surface border border-surface-border space-y-2">
            <div className="font-mono text-primary font-bold">afm evaluate &lt;case-id&gt; --adapter &lt;name&gt;</div>
            <p className="text-secondary">
              Evaluates whether an agent adapter can solve the original task. Captures file changes, diffs, and verification test outputs.
            </p>
          </div>

          <div className="p-4 rounded bg-surface border border-surface-border space-y-2">
            <div className="font-mono text-primary font-bold">afm doctor</div>
            <p className="text-secondary">
              Inspects local runtime environment: Python version, Docker availability, schema integrity, and registry health.
            </p>
          </div>

          <div className="p-4 rounded bg-surface border border-surface-border space-y-2">
            <div className="font-mono text-primary font-bold">afm new</div>
            <p className="text-secondary">
              Interactive wizard guiding contributors through authoring a new compliant failure case.
            </p>
          </div>
        </div>
      </section>

      {/* Section 3: Security */}
      <section id="security" className="space-y-4 pt-6 border-t border-surface-border">
        <h2 className="text-xl font-mono font-bold text-primary flex items-center space-x-2">
          <Shield className="w-5 h-5 text-accent" />
          <span>3. Security Isolation Model</span>
        </h2>
        <div className="p-5 rounded bg-surface border border-surface-border space-y-3 text-xs text-secondary leading-relaxed">
          <p>
            Executing reproduction code from untrusted sources presents severe security risks. AFM enforces multi-layered defense policies:
          </p>
          <ul className="list-disc list-inside space-y-1.5 text-primary">
            <li><strong>Docker Requirement:</strong> If Docker is unavailable, AFM will refuse to execute reproduction scripts on the host. Direct execution is strictly prohibited.</li>
            <li><strong>Network Isolation:</strong> Containers default to <code>--network=none</code>.</li>
            <li><strong>Filesystem Containment:</strong> The case directory is mounted read-only (<code>:ro</code>). Sensitive paths like <code>/var/run/docker.sock</code>, <code>~/.ssh</code>, and host credentials are permanently blocked.</li>
            <li><strong>Resource Quotas:</strong> Strict 512MB RAM and 1.0 CPU limits with hard execution timeouts.</li>
            <li><strong>Automated Secret Redaction:</strong> Built-in sanitization removes OpenAI, Anthropic, AWS, GitHub tokens, and private SSH keys from all captured logs.</li>
          </ul>
        </div>
      </section>

      {/* Section 4: Schema & Taxonomy */}
      <section id="schema" className="space-y-4 pt-6 border-t border-surface-border">
        <h2 className="text-xl font-mono font-bold text-primary flex items-center space-x-2">
          <Layers className="w-5 h-5 text-accent" />
          <span>4. Failure Taxonomy</span>
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
          <div className="p-3 rounded bg-surface border border-surface-border">
            <span className="font-mono font-semibold text-accent">hallucinated-api</span>
            <p className="text-secondary mt-1">Invoking non-existent methods or library signatures.</p>
          </div>
          <div className="p-3 rounded bg-surface border border-surface-border">
            <span className="font-mono font-semibold text-accent">destructive-file-operation</span>
            <p className="text-secondary mt-1">Accidental deletion, truncation, or directory wipe.</p>
          </div>
          <div className="p-3 rounded bg-surface border border-surface-border">
            <span className="font-mono font-semibold text-accent">false-success-claim</span>
            <p className="text-secondary mt-1">Claiming tests pass by silencing or modifying assertions.</p>
          </div>
          <div className="p-3 rounded bg-surface border border-surface-border">
            <span className="font-mono font-semibold text-accent">failed-bug-fix</span>
            <p className="text-secondary mt-1">Attempting a bug repair that leaves the defect unresolved.</p>
          </div>
          <div className="p-3 rounded bg-surface border border-surface-border">
            <span className="font-mono font-semibold text-accent">security-regression</span>
            <p className="text-secondary mt-1">Introducing a security flaw or vulnerability during refactoring.</p>
          </div>
          <div className="p-3 rounded bg-surface border border-surface-border">
            <span className="font-mono font-semibold text-accent">instruction-following-failure</span>
            <p className="text-secondary mt-1">Violating explicit constraints given in user prompt.</p>
          </div>
        </div>
      </section>
    </div>
  );
}
