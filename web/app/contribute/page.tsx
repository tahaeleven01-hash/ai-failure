import Link from "next/link";
import { GitPullRequest, Terminal, CheckCircle2, AlertTriangle, ShieldCheck, FileCode } from "lucide-react";

export default function ContributePage() {
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-12">
      {/* Header */}
      <div className="space-y-3">
        <div className="inline-flex items-center space-x-2 text-xs font-mono text-accent">
          <GitPullRequest className="w-4 h-4" />
          <span>Open Source Contribution Guide</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-mono font-bold text-primary">
          Contributing AI Agent Failure Cases
        </h1>
        <p className="text-sm text-secondary leading-relaxed">
          AI Failure Museum relies on real-world failure reports from developers and researchers.
          Follow this guide to document and submit failures via GitHub pull requests.
        </p>
      </div>

      {/* Non-Negotiable Rules Alert */}
      <div className="p-5 rounded bg-surface border-l-4 border-accent space-y-3">
        <div className="flex items-center space-x-2 text-sm font-mono font-semibold text-accent">
          <AlertTriangle className="w-4 h-4" />
          <span>Non-Negotiable Submission Standards</span>
        </div>
        <ul className="text-xs text-secondary space-y-1.5 list-disc list-inside">
          <li><strong>Never fabricate failure reports:</strong> All cases must originate from actual agent executions or be labeled synthetic test cases.</li>
          <li><strong>Never expose secrets or API keys:</strong> Scrub prompts, context, logs, and evidence of any OpenAI/Anthropic/AWS credentials or proprietary tokens.</li>
          <li><strong>Safe reproduction only:</strong> Do not include malicious code or procedures that attempt to break host containment.</li>
          <li><strong>Deterministic assertions:</strong> Provide automated assertions so reproduction can be verified without manual guesswork.</li>
        </ul>
      </div>

      {/* Step by Step Workflow */}
      <section className="space-y-6">
        <h2 className="text-lg font-mono font-bold text-primary">Submission Workflow</h2>

        <div className="space-y-6">
          {/* Step 1 */}
          <div className="p-5 rounded bg-surface border border-surface-border space-y-3">
            <div className="flex items-center space-x-3">
              <span className="w-6 h-6 rounded bg-accent/20 text-accent font-mono text-xs font-bold flex items-center justify-center">
                1
              </span>
              <h3 className="font-mono text-sm font-semibold text-primary">Scaffold Case with AFM CLI</h3>
            </div>
            <p className="text-xs text-secondary leading-relaxed">
              Use the built-in interactive wizard to generate a compliant case definition and folder structure:
            </p>
            <div className="p-3 rounded bg-background border border-surface-border font-mono text-xs text-accent">
              afm new --id AFM-0002 --title &quot;Agent Hallucinates Non-Existent API&quot;
            </div>
          </div>

          {/* Step 2 */}
          <div className="p-5 rounded bg-surface border border-surface-border space-y-3">
            <div className="flex items-center space-x-3">
              <span className="w-6 h-6 rounded bg-accent/20 text-accent font-mono text-xs font-bold flex items-center justify-center">
                2
              </span>
              <h3 className="font-mono text-sm font-semibold text-primary">Document Metadata & Evidence</h3>
            </div>
            <p className="text-xs text-secondary leading-relaxed">
              Edit the generated <code>case.yaml</code> file. Provide the exact user prompt, expected vs. observed behavior,
              and attach any terminal logs or diffs into the <code>evidence/</code> folder.
            </p>
          </div>

          {/* Step 3 */}
          <div className="p-5 rounded bg-surface border border-surface-border space-y-3">
            <div className="flex items-center space-x-3">
              <span className="w-6 h-6 rounded bg-accent/20 text-accent font-mono text-xs font-bold flex items-center justify-center">
                3
              </span>
              <h3 className="font-mono text-sm font-semibold text-primary">Validate and Test Locally</h3>
            </div>
            <p className="text-xs text-secondary leading-relaxed">
              Verify that your submission strictly adheres to the schema and passes automated checks:
            </p>
            <div className="space-y-2">
              <div className="p-2.5 rounded bg-background border border-surface-border font-mono text-xs text-primary">
                afm validate AFM-0002
              </div>
              <div className="p-2.5 rounded bg-background border border-surface-border font-mono text-xs text-primary">
                pytest tests/
              </div>
            </div>
          </div>

          {/* Step 4 */}
          <div className="p-5 rounded bg-surface border border-surface-border space-y-3">
            <div className="flex items-center space-x-3">
              <span className="w-6 h-6 rounded bg-accent/20 text-accent font-mono text-xs font-bold flex items-center justify-center">
                4
              </span>
              <h3 className="font-mono text-sm font-semibold text-primary">Submit Pull Request</h3>
            </div>
            <p className="text-xs text-secondary leading-relaxed">
              Commit your changes to a feature branch (e.g. <code>case/afm-0002</code>) and open a pull request on GitHub.
              Continuous Integration will automatically execute static schema and secret validation.
            </p>
          </div>
        </div>
      </section>

      {/* Review Process */}
      <section className="p-6 rounded bg-surface border border-surface-border space-y-4">
        <h2 className="text-sm font-mono font-bold text-primary">Review & Verification Lifecycle</h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs font-mono">
          <div className="p-3 rounded bg-background border border-surface-border space-y-1">
            <span className="text-secondary font-bold">1. Submitted</span>
            <p className="text-secondary/80 font-sans text-[11px]">
              Initial PR submission with static schema validation.
            </p>
          </div>
          <div className="p-3 rounded bg-background border border-surface-border space-y-1">
            <span className="text-yellow-400 font-bold">2. Validated</span>
            <p className="text-secondary/80 font-sans text-[11px]">
              Maintainer audit confirms integrity, no secrets, clear task.
            </p>
          </div>
          <div className="p-3 rounded bg-background border border-surface-border space-y-1">
            <span className="text-green-400 font-bold">3. Reproducible</span>
            <p className="text-secondary/80 font-sans text-[11px]">
              Reproduction procedure confirmed inside isolated container.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
