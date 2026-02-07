"use client";

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';

interface LogEntry {
    id: number;
    skill_name: string;
    status: string;
    input: any;
    output: any;
    error: string | null;
    duration: number;
    created_at: string;
}

interface SkillStats {
    total_runs: number;
    success_rate: number;
    avg_duration: number;
    last_run: string | null;
}

interface SkillMetadata {
    name: string;
    description: string;
    version: string;
    [key: string]: any;
}

interface SkillDetails {
    metadata: SkillMetadata;
    stats: SkillStats;
    logs: LogEntry[];
}

export default function SkillDetailPage() {
    const params = useParams();
    const router = useRouter();
    const skillName = decodeURIComponent(params.name as string);

    const [data, setData] = useState<SkillDetails | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!skillName) return;
        fetchData();
    }, [skillName]);

    const fetchData = async () => {
        try {
            setLoading(true);
            // Use the API endpoint we just created
            const res = await fetch(`http://localhost:8001/api/skills/${encodeURIComponent(skillName)}`);
            if (!res.ok) throw new Error("Failed to fetch skill details");
            const json = await res.json();
            setData(json);
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    if (loading) return (
        <div className="min-h-screen bg-black text-white p-8 font-sans flex items-center justify-center">
            <div className="animate-pulse text-xl text-neutral-400">Loading Skill Details...</div>
        </div>
    );

    if (error || !data) return (
        <div className="min-h-screen bg-black text-white p-8 font-sans flex flex-col items-center justify-center">
            <h1 className="text-2xl text-red-500 mb-4">Error</h1>
            <p className="text-neutral-400 mb-6">{error || "Skill not found"}</p>
            <Link href="/" className="px-4 py-2 bg-neutral-800 rounded hover:bg-neutral-700 transition">
                &larr; Back to Dashboard
            </Link>
        </div>
    );

    const { metadata, stats, logs } = data;

    return (
        <div className="min-h-screen bg-black text-white font-sans selection:bg-neutral-700">
            {/* Navbar Placeholder / Back Button */}
            <div className="p-6 border-b border-neutral-800 flex items-center gap-4">
                <Link href="/" className="text-neutral-400 hover:text-white transition">
                    &larr; Dashboard
                </Link>
                <h1 className="text-xl font-bold tracking-tight">{metadata.name}</h1>
                <span className="text-xs px-2 py-0.5 rounded bg-neutral-800 text-neutral-400 font-mono">v{metadata.version}</span>
            </div>

            <div className="max-w-7xl mx-auto p-6 space-y-8">

                {/* Header Section */}
                <div className="space-y-2">
                    <h2 className="text-3xl font-light text-neutral-200">{metadata.description}</h2>
                    <div className="flex gap-2 text-sm text-neutral-500">
                        {/* Check for other metadata fields to display tags if any */}
                        {/* For example author, license, etc if available in metadata */}
                    </div>
                </div>

                {/* Stats Grid */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <StatCard label="Success Rate" value={`${stats.success_rate.toFixed(1)}%`} color={stats.success_rate > 90 ? "text-green-400" : stats.success_rate > 50 ? "text-yellow-400" : "text-red-400"} />
                    <StatCard label="Total Runs" value={stats.total_runs.toLocaleString()} />
                    <StatCard label="Avg Duration" value={`${stats.avg_duration.toFixed(0)} ms`} />
                    <StatCard label="Last Run" value={stats.last_run ? new Date(stats.last_run).toLocaleString() : "Never"} isDate />
                </div>

                {/* Action Bar */}
                <div className="flex justify-end gap-2">
                    <button
                        onClick={fetchData}
                        className="px-4 py-2 bg-neutral-800 rounded hover:bg-neutral-700 transition text-sm flex items-center gap-2"
                    >
                        <span>↻</span> Refresh
                    </button>
                    {/* Future: Add 'Run Manually' button? */}
                </div>

                {/* Logs Table */}
                <div className="border border-neutral-800 rounded-lg overflow-hidden bg-neutral-900/20 backdrop-blur-sm">
                    <div className="p-4 border-b border-neutral-800 bg-neutral-900/40">
                        <h3 className="font-semibold text-neutral-200">Execution Logs</h3>
                    </div>
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm text-left">
                            <thead className="bg-neutral-900/50 text-neutral-400 border-b border-neutral-800 font-mono uppercase text-xs">
                                <tr>
                                    <th className="px-6 py-3">Status</th>
                                    <th className="px-6 py-3">Time</th>
                                    <th className="px-6 py-3">Duration</th>
                                    <th className="px-6 py-3">Input</th>
                                    <th className="px-6 py-3">Output / Error</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-neutral-800">
                                {logs.length === 0 ? (
                                    <tr>
                                        <td colSpan={5} className="px-6 py-8 text-center text-neutral-500 italic">
                                            No logs found.
                                        </td>
                                    </tr>
                                ) : (
                                    logs.map((log) => (
                                        <LogRow key={log.id} log={log} />
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>

            </div>
        </div>
    );
}

function StatCard({ label, value, color, isDate }: { label: string, value: string, color?: string, isDate?: boolean }) {
    return (
        <div className="p-4 rounded-lg bg-neutral-900/30 border border-neutral-800 backdrop-blur-sm">
            <div className="text-xs text-neutral-500 uppercase tracking-wider mb-1">{label}</div>
            <div className={`text-2xl font-mono ${color || 'text-white'} ${isDate ? 'text-lg' : ''}`}>
                {value}
            </div>
        </div>
    );
}

function LogRow({ log }: { log: LogEntry }) {
    const isSuccess = log.status === 'success';
    const [expanded, setExpanded] = useState(false);

    return (
        <>
            <tr className="hover:bg-neutral-800/30 transition cursor-pointer" onClick={() => setExpanded(!expanded)}>
                <td className="px-6 py-4">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${isSuccess ? 'bg-green-900/30 text-green-400 border border-green-900' : 'bg-red-900/30 text-red-400 border border-red-900'
                        }`}>
                        {isSuccess ? 'SUCCESS' : 'FAILED'}
                    </span>
                </td>
                <td className="px-6 py-4 text-neutral-300 font-mono text-xs">
                    {new Date(log.created_at).toLocaleString()}
                </td>
                <td className="px-6 py-4 text-neutral-400 font-mono text-xs">
                    {(log.duration * 1000).toFixed(0)}ms
                </td>
                <td className="px-6 py-4 text-neutral-400 font-mono text-xs max-w-xs truncate">
                    {JSON.stringify(log.input)}
                </td>
                <td className="px-6 py-4 text-neutral-400 font-mono text-xs max-w-xs truncate">
                    {log.error ? <span className="text-red-400">{log.error}</span> : JSON.stringify(log.output)}
                </td>
            </tr>
            {expanded && (
                <tr className="bg-neutral-900/50">
                    <td colSpan={5} className="px-6 py-4">
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <h4 className="text-xs uppercase text-neutral-500 mb-2">Input</h4>
                                <pre className="text-xs font-mono text-neutral-300 bg-black/50 p-4 rounded overflow-auto border border-neutral-800 max-h-60">
                                    {JSON.stringify(log.input, null, 2)}
                                </pre>
                            </div>
                            <div>
                                <h4 className="text-xs uppercase text-neutral-500 mb-2">Output / Error</h4>
                                <pre className={`text-xs font-mono bg-black/50 p-4 rounded overflow-auto border border-neutral-800 max-h-60 ${log.error ? 'text-red-400' : 'text-neutral-300'}`}>
                                    {log.error || JSON.stringify(log.output, null, 2)}
                                </pre>
                            </div>
                        </div>
                    </td>
                </tr>
            )}
        </>
    );
}
