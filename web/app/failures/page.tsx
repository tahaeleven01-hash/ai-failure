"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import { getAllCases, getAllCategories, getAllAgents, FailureCase } from "@/lib/registry";
import { Search, Filter, ArrowUpDown, ShieldAlert, Sparkles, CheckCircle2 } from "lucide-react";

export default function FailuresPage() {
  const allCases = getAllCases();
  const categories = getAllCategories();
  const agents = getAllAgents();

  const [search, setSearch] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [selectedAgent, setSelectedAgent] = useState<string>("all");
  const [selectedStatus, setSelectedStatus] = useState<string>("all");
  const [syntheticOnly, setSyntheticOnly] = useState<boolean>(false);
  const [sortBy, setSortBy] = useState<"id" | "title" | "date">("id");

  const filteredCases = useMemo(() => {
    return allCases.filter((item) => {
      // Synthetic filter
      if (syntheticOnly && !item.is_synthetic) return false;

      // Category filter
      if (selectedCategory !== "all" && !item.categories.includes(selectedCategory)) {
        return false;
      }

      // Agent filter
      if (selectedAgent !== "all" && item.agent.name !== selectedAgent) {
        return false;
      }

      // Status filter
      if (selectedStatus !== "all" && item.status !== selectedStatus) {
        return false;
      }

      // Search text query
      if (search.trim()) {
        const q = search.toLowerCase();
        const matchText = (
          `${item.id} ${item.title} ${item.description} ${item.agent.name} ${item.categories.join(" ")} ${item.tags.join(" ")}`
        ).toLowerCase();
        if (!matchText.includes(q)) return false;
      }

      return true;
    }).sort((a, b) => {
      if (sortBy === "id") return a.id.localeCompare(b.id);
      if (sortBy === "title") return a.title.localeCompare(b.title);
      if (sortBy === "date") return b.submission.date.localeCompare(a.submission.date);
      return 0;
    });
  }, [allCases, search, selectedCategory, selectedAgent, selectedStatus, syntheticOnly, sortBy]);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      {/* Header */}
      <div className="space-y-2">
        <h1 className="text-2xl sm:text-3xl font-mono font-bold text-primary">
          Failure Explorer
        </h1>
        <p className="text-sm text-secondary">
          Browse, filter, and inspect verified AI coding agent failure benchmarks.
        </p>
      </div>

      {/* Filter & Search Bar */}
      <div className="p-4 rounded bg-surface border border-surface-border space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          {/* Search Input */}
          <div className="md:col-span-2 relative">
            <Search className="w-4 h-4 text-secondary absolute left-3 top-3" />
            <input
              type="text"
              placeholder="Search by ID, keyword, agent, category..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-background border border-surface-border rounded pl-9 pr-4 py-2 text-xs font-mono text-primary placeholder-secondary/60 focus:outline-none focus:border-accent"
            />
          </div>

          {/* Category Select */}
          <div>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="w-full bg-background border border-surface-border rounded px-3 py-2 text-xs font-mono text-primary focus:outline-none focus:border-accent"
            >
              <option value="all">All Categories ({categories.length})</option>
              {categories.map((cat) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
            </select>
          </div>

          {/* Agent Select */}
          <div>
            <select
              value={selectedAgent}
              onChange={(e) => setSelectedAgent(e.target.value)}
              className="w-full bg-background border border-surface-border rounded px-3 py-2 text-xs font-mono text-primary focus:outline-none focus:border-accent"
            >
              <option value="all">All Agents ({agents.length})</option>
              {agents.map((ag) => (
                <option key={ag} value={ag}>
                  {ag}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Secondary Filters & Sort */}
        <div className="flex flex-wrap items-center justify-between gap-4 pt-2 border-t border-surface-border text-xs font-mono text-secondary">
          <div className="flex items-center space-x-4">
            <label className="flex items-center space-x-1.5 cursor-pointer">
              <input
                type="checkbox"
                checked={syntheticOnly}
                onChange={(e) => setSyntheticOnly(e.target.checked)}
                className="rounded border-surface-border text-accent focus:ring-0 bg-background"
              />
              <span>Synthetic only</span>
            </label>

            <div className="flex items-center space-x-1">
              <span>Status:</span>
              <select
                value={selectedStatus}
                onChange={(e) => setSelectedStatus(e.target.value)}
                className="bg-background border border-surface-border rounded px-2 py-1 text-xs font-mono text-primary"
              >
                <option value="all">All</option>
                <option value="reproducible">reproducible</option>
                <option value="validated">validated</option>
                <option value="submitted">submitted</option>
                <option value="non-reproducible">non-reproducible</option>
              </select>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <ArrowUpDown className="w-3.5 h-3.5" />
            <span>Sort:</span>
            <button
              onClick={() => setSortBy("id")}
              className={`px-2 py-0.5 rounded ${sortBy === "id" ? "bg-accent/20 text-accent font-semibold" : "hover:text-primary"}`}
            >
              ID
            </button>
            <button
              onClick={() => setSortBy("date")}
              className={`px-2 py-0.5 rounded ${sortBy === "date" ? "bg-accent/20 text-accent font-semibold" : "hover:text-primary"}`}
            >
              Date
            </button>
            <button
              onClick={() => setSortBy("title")}
              className={`px-2 py-0.5 rounded ${sortBy === "title" ? "bg-accent/20 text-accent font-semibold" : "hover:text-primary"}`}
            >
              Title
            </button>
          </div>
        </div>
      </div>

      {/* Case Grid */}
      {filteredCases.length === 0 ? (
        <div className="text-center py-16 p-6 rounded bg-surface border border-surface-border space-y-3">
          <ShieldAlert className="w-8 h-8 text-accent mx-auto" />
          <h3 className="font-mono text-base font-semibold text-primary">No Matching Cases Found</h3>
          <p className="text-xs text-secondary max-w-sm mx-auto">
            Try adjusting your query or resetting category and status filters.
          </p>
          <button
            onClick={() => {
              setSearch("");
              setSelectedCategory("all");
              setSelectedAgent("all");
              setSelectedStatus("all");
              setSyntheticOnly(false);
            }}
            className="text-xs font-mono text-accent hover:underline pt-2 inline-block"
          >
            Clear all filters
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredCases.map((item) => (
            <Link
              key={item.id}
              href={`/failures/${item.id}`}
              className="group block p-5 rounded bg-surface border border-surface-border hover:border-accent/60 transition-colors flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between text-xs font-mono mb-2.5">
                  <span className="font-bold text-accent">{item.id}</span>
                  <div className="flex items-center space-x-1.5">
                    {item.is_synthetic && (
                      <span className="px-1.5 py-0.5 rounded bg-surface-elevated text-[10px] text-secondary border border-surface-border">
                        Synthetic
                      </span>
                    )}
                    <span className="px-1.5 py-0.5 rounded bg-surface-elevated text-[10px] text-accent border border-accent/20 font-medium">
                      {item.status}
                    </span>
                  </div>
                </div>

                <h3 className="font-mono text-sm font-semibold text-primary group-hover:text-accent transition-colors line-clamp-2 leading-snug">
                  {item.title}
                </h3>

                <p className="text-xs text-secondary mt-2 line-clamp-3 leading-relaxed">
                  {item.description}
                </p>
              </div>

              <div className="mt-4 pt-3 border-t border-surface-border space-y-2">
                <div className="flex flex-wrap gap-1">
                  {item.categories.slice(0, 2).map((cat) => (
                    <span
                      key={cat}
                      className="px-1.5 py-0.5 rounded bg-background border border-surface-border text-[10px] font-mono text-secondary"
                    >
                      {cat}
                    </span>
                  ))}
                  {item.categories.length > 2 && (
                    <span className="text-[10px] font-mono text-secondary/70 self-center">
                      +{item.categories.length - 2}
                    </span>
                  )}
                </div>

                <div className="flex items-center justify-between text-[11px] font-mono text-secondary">
                  <span>{item.agent.name}</span>
                  <span>{item.submission.date}</span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
