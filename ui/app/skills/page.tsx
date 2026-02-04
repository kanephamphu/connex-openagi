"use client";

import { useEffect, useState } from "react";

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
                                    <h3 className="text-xl font-semibold bg-gradient-to-br from-white to-neutral-400 bg-clip-text text-transparent">
                                        {skill.name}
                                    </h3>
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
                            </div>
                        </div>
                    ))}

                    {/* Add New Placehodler */}
                    <div className="bg-neutral-800/20 border-2 border-dashed border-neutral-700/50 rounded-xl p-6 flex flex-col items-center justify-center text-neutral-500 hover:border-neutral-600 hover:text-neutral-400 cursor-pointer transition-all min-h-[200px]">
                        <span className="text-3xl mb-2">+</span>
                        <span>Install New Skill</span>
                    </div>
                </div>
            )}
        </div>
    );
}
