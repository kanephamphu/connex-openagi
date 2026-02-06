"use client";

import { useEffect, useState } from "react";

interface RegistryItem {
    id: string;
    name: string;
    description: string;
    type: string;
    version: string;
    author: {
        username: string;
    };
    category: string;
}

export default function RegistryPage() {
    const [query, setQuery] = useState("");
    const [type, setType] = useState("skill");
    const [results, setResults] = useState<RegistryItem[]>([]);
    const [loading, setLoading] = useState(false);
    const [installing, setInstalling] = useState<string | null>(null);

    const handleSearch = async (e?: React.FormEvent) => {
        if (e) e.preventDefault();
        setLoading(true);
        try {
            const res = await fetch(`/api/registry/search?q=${encodeURIComponent(query)}&type=${type}`);
            const data = await res.json();
            setResults(data.results || []);
        } catch (err) {
            console.error("Search failed:", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        handleSearch();
    }, [type]);

    const handleInstall = async (name: string) => {
        setInstalling(name);
        try {
            const res = await fetch("/api/registry/install", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ name, type })
            });
            const data = await res.json();
            if (data.success) {
                alert(`Successfully installed ${name}`);
            } else {
                alert(`Failed to install: ${data.detail || data.message}`);
            }
        } catch (err) {
            console.error("Installation failed:", err);
            alert("Installation failed. See console for details.");
        } finally {
            setInstalling(null);
        }
    };

    return (
        <div className="max-w-6xl mx-auto p-6">
            <header className="mb-10 text-center">
                <h1 className="text-4xl font-extrabold mb-4 bg-gradient-to-r from-blue-400 via-purple-500 to-pink-500 bg-clip-text text-transparent">
                    Connex Registry
                </h1>
                <p className="text-neutral-400 max-w-2xl mx-auto">
                    Global repository for AGI capabilities. Download and use community-built
                    Skills, Reflexes, and Perceptions.
                </p>
            </header>

            <div className="flex flex-col md:flex-row gap-8">
                {/* Sidebar / Filters */}
                <aside className="w-full md:w-64 space-y-6">
                    <div>
                        <h3 className="text-sm font-semibold uppercase tracking-wider text-neutral-500 mb-4">Component Type</h3>
                        <div className="space-y-2">
                            {["skill", "reflex", "perception"].map((t) => (
                                <button
                                    key={t}
                                    onClick={() => setType(t)}
                                    className={`w-full text-left px-4 py-2 rounded-lg capitalize transition-all ${type === t
                                            ? "bg-blue-600/20 text-blue-400 border border-blue-500/30"
                                            : "text-neutral-500 hover:bg-neutral-800"
                                        }`}
                                >
                                    {t}s
                                </button>
                            ))}
                        </div>
                    </div>
                </aside>

                {/* Main Content */}
                <main className="flex-1">
                    <form onSubmit={handleSearch} className="relative mb-8 group">
                        <input
                            type="text"
                            placeholder={`Search community ${type}s...`}
                            className="w-full bg-neutral-900 border border-neutral-800 rounded-2xl px-6 py-4 text-lg focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all shadow-2xl"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                        />
                        <button
                            type="submit"
                            className="absolute right-4 top-3.5 bg-blue-600 hover:bg-blue-500 text-white px-6 py-1.5 rounded-xl transition-colors font-medium"
                        >
                            {loading ? "..." : "Search"}
                        </button>
                    </form>

                    {loading ? (
                        <div className="flex justify-center p-20">
                            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            {results.length > 0 ? (
                                results.map((item) => (
                                    <div key={item.id} className="bg-neutral-900/50 border border-neutral-800 rounded-2xl p-6 hover:border-neutral-700 transition-all flex flex-col group relative overflow-hidden">
                                        <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-100 transition-opacity">
                                            <span className="text-2xl">🌍</span>
                                        </div>

                                        <div className="flex justify-between items-start mb-4">
                                            <div>
                                                <h3 className="text-xl font-bold text-white mb-1 group-hover:text-blue-400 transition-colors">
                                                    {item.name}
                                                </h3>
                                                <div className="flex items-center gap-2 text-xs text-neutral-500">
                                                    <span className="bg-neutral-800 px-2 py-0.5 rounded text-neutral-400">@{item.author.username}</span>
                                                    <span>•</span>
                                                    <span>v{item.version}</span>
                                                </div>
                                            </div>
                                        </div>

                                        <p className="text-neutral-400 text-sm mb-6 flex-1 line-clamp-3">
                                            {item.description}
                                        </p>

                                        <div className="flex items-center justify-between">
                                            <div className="flex gap-2">
                                                <span className="text-[10px] uppercase tracking-tighter bg-neutral-800 text-neutral-500 px-2 py-1 rounded">
                                                    {item.category}
                                                </span>
                                            </div>
                                            <button
                                                onClick={() => handleInstall(item.name)}
                                                disabled={installing === item.name}
                                                className="bg-white hover:bg-neutral-200 text-black px-4 py-2 rounded-xl text-sm font-bold transition-all disabled:opacity-50"
                                            >
                                                {installing === item.name ? "Installing..." : "Install"}
                                            </button>
                                        </div>
                                    </div>
                                ))
                            ) : (
                                <div className="col-span-full py-20 text-center bg-neutral-900/20 border border-dashed border-neutral-800 rounded-3xl">
                                    <span className="text-4xl mb-4 block">🔎</span>
                                    <p className="text-neutral-500">No results found in the registry.</p>
                                </div>
                            )}
                        </div>
                    )}
                </main>
            </div>
        </div>
    );
}
