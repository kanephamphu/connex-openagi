"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

interface Skill {
    name: string;
    description: string;
    category: string;
    version: string;
    enabled: boolean;
    is_configured: boolean;
}

export default function SkillsPage() {
    const [skills, setSkills] = useState<Skill[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState("");
    const [publishingSkill, setPublishingSkill] = useState<Skill | null>(null);
    const [scopedName, setScopedName] = useState("");
    const [isPublishing, setIsPublishing] = useState(false);

    const handlePublish = async () => {
        if (!publishingSkill || !scopedName) return;
        setIsPublishing(true);
        try {
            const res = await fetch("/api/registry/publish", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    name: publishingSkill.name,
                    type: "skill",
                    scoped_name: scopedName
                })
            });
            const data = await res.json();
            if (data.success) {
                alert(`Successfully published to ${scopedName}`);
                setPublishingSkill(null);
            } else {
                alert(`Publishing failed: ${data.detail || data.message}`);
            }
        } catch (err) {
            console.error("Failed to publish skill:", err);
            alert("Publishing failed.");
        } finally {
            setIsPublishing(false);
        }
    };

    const fetchSkills = () => {
        fetch("/api/skills")
            .then((res) => res.json())
            .then((data) => {
                setSkills(data.skills);
                setLoading(false);
            })
            .catch((err) => {
                console.error("Failed to fetch skills:", err);
                setLoading(false);
            });
    };

    useEffect(() => {
        fetchSkills();
    }, []);

    const filteredSkills = skills.filter(s =>
        s.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        s.description.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const toggleSkill = async (name: string, currentStatus: boolean) => {
        try {
            const res = await fetch(`/api/skills/${name}/toggle`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ enabled: !currentStatus })
            });
            if (res.ok) {
                // Optimistic update
                setSkills(skills.map(s => s.name === name ? { ...s, enabled: !currentStatus } : s));
            }
        } catch (err) {
            console.error("Failed to toggle skill:", err);
        }
    };

    return (
        <div className="max-w-5xl mx-auto">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
                <h1 className="text-3xl font-bold">Installed Skills</h1>

                <div className="relative group w-full md:w-64">
                    <input
                        type="text"
                        placeholder="Search skills..."
                        className="w-full bg-neutral-900/50 border border-neutral-800 rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-blue-500/50 transition-all pl-10"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                    />
                    <span className="absolute left-3 top-2.5 text-neutral-500">🔍</span>
                </div>
            </div>

            {loading ? (
                <div className="text-neutral-400">Loading skills...</div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {filteredSkills.map((skill) => (
                        <div
                            key={skill.name}
                            className={`border rounded-xl p-6 transition-all hover:shadow-lg ${skill.enabled
                                ? "bg-neutral-800/50 border-neutral-700/50 hover:border-blue-500/30 hover:shadow-blue-900/10"
                                : "bg-neutral-900/50 border-neutral-800 opacity-75 grayscale-[0.5]"
                                }`}
                        >
                            <div className="flex justify-between items-start mb-4">
                                <div>
                                    <Link href={`/skills/${encodeURIComponent(skill.name)}`}>
                                        <h3 className="text-xl font-semibold bg-gradient-to-br from-white to-neutral-400 bg-clip-text text-transparent hover:text-blue-400 transition-colors cursor-pointer">
                                            {skill.name}
                                        </h3>
                                    </Link>
                                    {!skill.is_configured && (
                                        <div className="flex items-center gap-1 text-amber-500 text-[10px] mt-1">
                                            <span>⚠️ Config Required</span>
                                        </div>
                                    )}
                                </div>
                                <div className="flex flex-col items-end gap-2">
                                    <span className="text-xs px-2 py-1 rounded-full bg-neutral-700 text-neutral-300">
                                        {skill.category}
                                    </span>
                                    <button
                                        onClick={() => toggleSkill(skill.name, skill.enabled)}
                                        className={`w-8 h-4 rounded-full relative transition-colors ${skill.enabled ? 'bg-green-500/80' : 'bg-neutral-600'}`}
                                    >
                                        <div className={`absolute top-0.5 w-3 h-3 bg-white rounded-full transition-all ${skill.enabled ? 'left-4.5 translate-x-0.5' : 'left-0.5'}`}></div>
                                    </button>
                                </div>
                            </div>

                            <p className="text-neutral-400 text-sm mb-4 line-clamp-3">
                                {skill.description}
                            </p>

                            <div className="flex items-center justify-between mt-auto pt-4 border-t border-neutral-700/30">
                                <span className="text-xs text-neutral-500">v{skill.version}</span>
                                <button className="text-xs text-blue-400 hover:text-blue-300">
                                    Configure
                                </button>
                                <button
                                    onClick={() => {
                                        setPublishingSkill(skill);
                                        setScopedName(`@user/${skill.name}`);
                                    }}
                                    className="text-xs text-green-400 hover:text-green-300"
                                >
                                    Publish
                                </button>
                            </div>
                        </div>
                    ))}

                    {/* Publish Modal */}
                    {publishingSkill && (
                        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                            <div className="bg-neutral-900 border border-neutral-800 rounded-2xl w-full max-w-md p-6 shadow-2xl">
                                <h2 className="text-2xl font-bold mb-4">Publish Skill</h2>
                                <p className="text-neutral-400 text-sm mb-6">
                                    Publish <strong>{publishingSkill.name}</strong> to the Connex Registry for others to use.
                                </p>

                                <div className="space-y-4 mb-8">
                                    <div>
                                        <label className="block text-xs font-semibold text-neutral-500 uppercase tracking-wider mb-2">Scoped Name</label>
                                        <input
                                            type="text"
                                            className="w-full bg-neutral-800 border border-neutral-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-500"
                                            placeholder="@username/skill-name"
                                            value={scopedName}
                                            onChange={(e) => setScopedName(e.target.value)}
                                        />
                                    </div>
                                </div>

                                <div className="flex gap-4">
                                    <button
                                        onClick={() => setPublishingSkill(null)}
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

                    {/* Add New Placehodler */}
                    <Link href="/registry" className="bg-neutral-800/20 border-2 border-dashed border-neutral-700/50 rounded-xl p-6 flex flex-col items-center justify-center text-neutral-500 hover:border-neutral-600 hover:text-neutral-400 cursor-pointer transition-all min-h-[200px]">
                        <span className="text-3xl mb-2">+</span>
                        <span>Install New Skill</span>
                    </Link>
                </div>
            )}
        </div>
    );
}
