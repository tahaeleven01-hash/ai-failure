import Link from "next/link";

export default function Footer() {
  return (
    <footer className="border-t border-surface-border bg-surface mt-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div className="space-y-3 md:col-span-2">
            <div className="flex items-center space-x-2">
              <span className="w-5 h-5 rounded bg-accent/20 border border-accent/40 flex items-center justify-center text-accent font-mono text-xs font-bold">
                A
              </span>
              <span className="font-mono text-sm font-semibold text-primary">
                AI Failure Museum
              </span>
            </div>
            <p className="text-xs text-secondary leading-relaxed max-w-md">
              A community-maintained benchmark registry of reproducible AI coding agent failures.
              Built for researchers, model developers, and tool maintainers.
            </p>
            <p className="text-xs font-mono text-secondary">
              Licensed under Apache-2.0. No paid APIs required.
            </p>
          </div>

          <div>
            <h4 className="text-xs font-mono font-semibold text-primary uppercase tracking-wider mb-3">
              Explore
            </h4>
            <ul className="space-y-2 text-xs text-secondary">
              <li>
                <Link href="/failures" className="hover:text-primary transition-colors">
                  All Failure Cases
                </Link>
              </li>
              <li>
                <Link href="/failures?category=hallucinated-api" className="hover:text-primary transition-colors">
                  Hallucinated APIs
                </Link>
              </li>
              <li>
                <Link href="/failures?category=destructive-file-operation" className="hover:text-primary transition-colors">
                  Destructive Operations
                </Link>
              </li>
              <li>
                <Link href="/failures?category=false-success-claim" className="hover:text-primary transition-colors">
                  False Success Claims
                </Link>
              </li>
            </ul>
          </div>

          <div>
            <h4 className="text-xs font-mono font-semibold text-primary uppercase tracking-wider mb-3">
              Resources
            </h4>
            <ul className="space-y-2 text-xs text-secondary">
              <li>
                <Link href="/docs" className="hover:text-primary transition-colors">
                  CLI Reference
                </Link>
              </li>
              <li>
                <Link href="/docs#security" className="hover:text-primary transition-colors">
                  Security Sandbox Rules
                </Link>
              </li>
              <li>
                <Link href="/contribute" className="hover:text-primary transition-colors">
                  Submit a Failure Case
                </Link>
              </li>
            </ul>
          </div>
        </div>

        <div className="border-t border-surface-border mt-8 pt-6 flex flex-col sm:flex-row items-center justify-between text-xs text-secondary font-mono">
          <span>&copy; {new Date().getFullYear()} AI Failure Museum Contributors.</span>
          <span className="mt-2 sm:mt-0 text-secondary">
            Never fabricate reports. Test under containment.
          </span>
        </div>
      </div>
    </footer>
  );
}
