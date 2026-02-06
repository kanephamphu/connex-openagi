"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

interface PerceptionModule {
    name: string;
    description: string;
    type: string;
    version: string;
    signals: string[];
}

export default function PerceptionPage() {
    const [modules, setModules] = useState<PerceptionModule[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState("");
    const [publishingModule, setPublishingModule] = useState<PerceptionModule | null>(null);
    const [scopedName, setScopedName] = useState("");
    const [isPublishing, setIsPublishing] = useState(false);

    const fetchModules = () => {
        fetch("/api/perception")
            .then((res) => res.json())
            .then((data) => {
                setModules(data.modules || []);
                setLoading(false);
            })
            .catch((err) => {
                console.error("Failed to fetch perception modules:", err);
                setLoading(false);
            });
    };

    useEffect(() => {
        fetchModules();
    }, []);

    const filteredModules = modules.filter(m =>
        m.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        m.description.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const handlePublish = async () => {
        if (!publishingModule || !scopedName) return;
        setIsPublishing(true);
        try {
            const res = await fetch("/api/registry/publish", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    name: publishingModule.name,
                    type: "perception",
                    scoped_name: scopedName
                })
            });
            const data = await res.json();
            if (data.success) {
                alert(`Successfully published to ${scopedName}`);
                setPublishingModule(null);
            } else {
                alert(`Publishing failed: ${data.detail || data.message}`);
            }
        } catch (err) {
            console.error("Failed to publish perception module:", err);
            alert("Publishing failed.");
        } finally {
            setIsPublishing(false);
        }
    };

    return (
        <div className="max-w-5xl mx-auto">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
                <h1 className="text-3xl font-bold">Perception Modules</h1>

                <div className="relative group w-full md:w-64">
                    <input
                        type="text"
                        placeholder="Search modules..."
                        className="w-full bg-neutral-900/50 border border-neutral-800 rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-blue-500/50 transition-all pl-10"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                    />
                    <span className="absolute left-3 top-2.5 text-neutral-500">🔍</span>
                </div>
            </div>

            {loading ? (
                <div className="text-neutral-400">Loading perception modules...</div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {filteredModules.map((module) => (
                        <div
                            key={module.name}
                            className={`border rounded-xl p-6 transition-all hover:shadow-lg bg-neutral-800/50 border-neutral-700/50 hover:border-blue-500/30 hover:shadow-blue-900/10`}
                        >
                            <div className="flex justify-between items-start mb-4">
                                <div>
                                    <h3 className="text-xl font-semibold bg-gradient-to-br from-white to-neutral-400 bg-clip-text text-transparent">
                                        {module.name}
                                    </h3>
                                </div>
                                <div className="flex flex-col items-end gap-2">
                                    <span className="text-xs px-2 py-1 rounded-full bg-neutral-700 text-neutral-300">
                                        Perception
                                    </span>
                                </div>
                            </div>

                            <p className="text-neutral-400 text-sm mb-4 line-clamp-3">
                                {module.description}
                            </p>

                            <div className="flex flex-wrap gap-1 mb-4">
                                {module.signals.map(s => (
                                    <span key={s} className="text-[10px] bg-blue-900/30 text-blue-400 border border-blue-500/20 px-1.5 py-0.5 rounded">
                                        {s}
                                    </span>
                                ))}
                            </div>

                            <div className="flex items-center justify-between mt-auto pt-4 border-t border-neutral-700/30">
                                <span className="text-xs text-neutral-500">v{module.version}</span>
                                <button
                                    onClick={() => {
                                        setPublishingModule(module);
                                        setScopedName(`@user/${module.name}`);
                                    }}
                                    className="text-xs text-green-400 hover:text-green-300"
                                >
                                    Publish
                                </button>
                            </div>
                        </div>
                    ))}

                    <Link href="/registry" className="bg-neutral-800/20 border-2 border-dashed border-neutral-700/50 rounded-xl p-6 flex flex-col items-center justify-center text-neutral-500 hover:border-neutral-600 hover:text-neutral-400 cursor-pointer transition-all min-h-[200px]">
                        <span className="text-3xl mb-2">+</span>
                        <span>Find in Registry</span>
                    </Link>
                </div>
            )}

            {/* Publish Modal */}
            {publishingModule && (
                <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                    <div className="bg-neutral-900 border border-neutral-800 rounded-2xl w-full max-w-md p-6 shadow-2xl">
                        <h2 className="text-2xl font-bold mb-4">Publish Perception Module</h2>
                        <p className="text-neutral-400 text-sm mb-6">
                            Publish <strong>{publishingModule.name}</strong> to the Connex Registry.
                        </p>

                        <div className="space-y-4 mb-8">
                            <div>
                                <label className="block text-xs font-semibold text-neutral-500 uppercase tracking-wider mb-2">Scoped Name</label>
                                <input
                                    type="text"
                                    className="w-full bg-neutral-800 border border-neutral-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-500"
                                    placeholder="@username/module-name"
                                    value={scopedName}
                                    onChange={(e) => setScopedName(e.target.value)}
                                />
                            </div>
                        </div>

                        <div className="flex gap-4">
                            <button
                                onClick={() => setPublishingModule(null)}
                                className="flex-1 px-4 py-2 rounded-xl border border-neutral-700 hover:bg-neutral-800 transition-colors"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handlePublish}
                                disabled={isPublishing || !scopedName}
                                className="flex-1 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold transition-all disabled:opacity-50"
                            >
                                {isPublishing ? "Publishing..." : "Confirm Publish"}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
