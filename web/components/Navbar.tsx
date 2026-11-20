import Link from "next/link";
import { AlertCircle, Terminal, FileText, GitPullRequest, Search } from "lucide-react";

export default function Navbar() {
  return (
    <header className="border-b border-surface-border bg-background/80 backdrop-blur sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center space-x-6">
          <Link href="/" className="flex items-center space-x-3 group">
            <span className="w-8 h-8 rounded bg-accent/10 border border-accent/30 flex items-center justify-center text-accent font-mono font-bold text-sm group-hover:border-accent transition-colors">
              AFM
            </span>
            <span className="font-mono text-sm tracking-wide font-semibold text-primary">
              AI Failure Museum
            </span>
          </Link>

          <nav className="hidden md:flex items-center space-x-1 text-sm font-medium">
            <Link
              href="/failures"
              className="px-3 py-1.5 rounded text-secondary hover:text-primary hover:bg-surface transition-colors flex items-center space-x-1.5"
            >
              <Search className="w-3.5 h-3.5" />
              <span>Explorer</span>
            </Link>
            <Link
              href="/docs"
              className="px-3 py-1.5 rounded text-secondary hover:text-primary hover:bg-surface transition-colors flex items-center space-x-1.5"
            >
              <FileText className="w-3.5 h-3.5" />
              <span>Docs</span>
            </Link>
            <Link
              href="/contribute"
              className="px-3 py-1.5 rounded text-secondary hover:text-primary hover:bg-surface transition-colors flex items-center space-x-1.5"
            >
              <GitPullRequest className="w-3.5 h-3.5" />
              <span>Contribute</span>
            </Link>
          </nav>
        </div>

        <div className="flex items-center space-x-3">
          <div className="hidden sm:flex items-center space-x-2 text-xs font-mono text-secondary bg-surface px-2.5 py-1.5 rounded border border-surface-border">
            <Terminal className="w-3.5 h-3.5 text-accent" />
            <span>pip install -e .</span>
          </div>
          <a
            href="https://github.com"
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs font-mono px-3 py-1.5 rounded bg-surface hover:bg-surface-elevated text-primary border border-surface-border transition-colors"
          >
            GitHub
          </a>
        </div>
      </div>
    </header>
  );
}
