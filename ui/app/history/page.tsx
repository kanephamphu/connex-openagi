"use client";

import { useEffect, useState } from "react";

interface HistoryItem {
    id: string;
    goal: string;
    status: "success" | "failed" | "unknown";
    timestamp: number;
}

export default function HistoryPage() {
    const [history, setHistory] = useState<HistoryItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [repairingId, setRepairingId] = useState<string | null>(null);
    const [repairLogs, setRepairLogs] = useState<string[]>([]);
    const [showLogs, setShowLogs] = useState(false);

    useEffect(() => {
        fetch("/api/history")
            .then((res) => res.json())
            .then((data) => {
                setHistory(data.history);
                setLoading(false);
            })
            .catch((err) => {
                console.error("Failed to fetch history:", err);
                setLoading(false);
            });
    }, []);

    const handleRepair = (id: string) => {
        setRepairingId(id);
        setRepairLogs(["Starting manual repair..."]);
        setShowLogs(true);

        const eventSource = new EventSource(`/api/repair/${id}`);

        eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.status === "complete") {
                setRepairLogs((prev) => [...prev, "✅ Repair Complete!"]);
                eventSource.close();
                setRepairingId(null);
            } else if (data.error) {
                setRepairLogs((prev) => [...prev, `❌ Error: ${data.error}`]);
                eventSource.close();
                setRepairingId(null);
            } else {
                // Format update for log
                let msg = "";
                if (data.type === "reasoning_token" && data.token) msg = data.token;
                else if (data.type === "action_started") msg = `▶ Executing: ${data.description}`;
                else if (data.type === "action_completed") msg = `✔ Success: ${data.action_id}`;
                else if (data.type === "action_failed") msg = `⚠ Failed: ${data.error}`;
                else if (data.type === "correction_started") msg = `🔧 Applying Fix...`;
                else if (data.status === "analyzing_failure") msg = `🔍 Analyzing failure trace...`;

                // For tokens, we might want to append to last line if it's a token? 
                // For simplicity, just log major events for now, or accumulate tokens.
                // Let's just log non-tokens for cleanlyness, or tokens if they are aggregated.
                if (msg) setRepairLogs((prev) => [...prev, msg]);
            }
        };

        eventSource.onerror = () => {
            setRepairLogs((prev) => [...prev, "❌ Network Error or Connection Closed"]);
            eventSource.close();
            setRepairingId(null);
        };
    };

    const formatTime = (ts: number) => {
        return new Date(ts * 1000).toLocaleString();
    };

    const [selectedTrace, setSelectedTrace] = useState<any>(null);

    const handleViewTrace = async (id: string) => {
        try {
            const res = await fetch(`/api/history/${id}`);
            const data = await res.json();
            setSelectedTrace(data);
        } catch (err) {
            console.error("Failed to fetch trace:", err);
        }
    };

    return (
        <div className="max-w-4xl mx-auto relative pb-20">
            <h1 className="text-3xl font-bold mb-8">Execution History</h1>

            {/* Trace Detail Modal */}
            {selectedTrace && (
                <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 backdrop-blur-sm p-4">
                    <div className="bg-neutral-900 border border-neutral-700 rounded-xl w-full max-w-3xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
                        <div className="p-4 border-b border-neutral-800 flex justify-between items-center bg-neutral-800/50">
                            <div>
                                <h3 className="font-bold text-white text-lg">Trace Details</h3>
                                <div className="text-xs text-neutral-400 font-mono">{selectedTrace.id}</div>
                            </div>
                            <button onClick={() => setSelectedTrace(null)} className="text-neutral-400 hover:text-white text-2xl px-2">✕</button>
                        </div>
                        <div className="p-6 overflow-auto bg-black/20 flex-1">
                            <div className="mb-6">
                                <h4 className="text-sm font-semibold text-neutral-500 uppercase tracking-widest mb-2">Goal</h4>
                                <div className="bg-neutral-800/50 p-3 rounded-lg text-white border border-neutral-700/50">
                                    {selectedTrace.goal}
                                </div>
                            </div>

                            <h4 className="text-sm font-semibold text-neutral-500 uppercase tracking-widest mb-2">Execution Steps</h4>
                            <div className="space-y-4">
                                {selectedTrace.events && selectedTrace.events.map((event: any, idx: number) => (
                                    <div key={idx} className={`p-4 rounded-lg border text-sm font-mono ${event.type === 'action_failed' ? 'bg-red-900/10 border-red-800/50' :
                                            event.type === 'action_completed' ? 'bg-green-900/10 border-green-800/50' :
                                                'bg-neutral-800/30 border-neutral-700/30'
                                        }`}>
                                        <div className="flex justify-between mb-2 opacity-70">
                                            <span className="font-bold uppercase text-[10px]">{event.type}</span>
                                            <span className="text-[10px]">{new Date(event.timestamp * 1000).toLocaleTimeString()}</span>
                                        </div>

                                        {/* Render Event Details */}
                                        {event.skill && (
                                            <div className="mb-1 text-blue-400">Skill: {event.skill}</div>
                                        )}
                                        {event.action_input && (
                                            <div className="mb-2 p-2 bg-black/30 rounded text-neutral-300 whitespace-pre-wrap">
                                                {JSON.stringify(event.action_input, null, 2)}
                                            </div>
                                        )}
                                        {event.output && (
                                            <div className="mt-2 text-green-400">
                                                Output: {JSON.stringify(event.output).slice(0, 300)}
                                            </div>
                                        )}
                                        {event.error && (
                                            <div className="mt-2 text-red-400 font-bold">
                                                Error: {event.error}
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Repair Logs Modal */}
            {showLogs && (
                <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 backdrop-blur-sm">
                    <div className="bg-neutral-900 border border-neutral-700 rounded-xl w-3/4 max-w-2xl max-h-[80vh] flex flex-col shadow-2xl">
                        <div className="p-4 border-b border-neutral-800 flex justify-between items-center bg-neutral-800/50 rounded-t-xl">
                            <h3 className="font-bold flex items-center gap-2 text-white">
                                <span>🔧</span> Immune System Repair Log
                            </h3>
                            <button onClick={() => setShowLogs(false)} className="text-neutral-400 hover:text-white">✕</button>
                        </div>
                        <div className="p-4 overflow-auto font-mono text-sm space-y-1 flex-1 bg-black/50">
                            {repairLogs.map((log, i) => (
                                <div key={i} className="break-words text-neutral-300 border-l-2 border-transparent pl-2 hover:border-blue-500/50">
                                    {log}
                                </div>
                            ))}
                            {repairingId && <div className="text-blue-400 animate-pulse">Running...</div>}
                        </div>
                    </div>
                </div>
            )}

            {loading ? (
                <div className="text-neutral-400">Loading history...</div>
            ) : (
                <div className="space-y-4">
                    {history.length === 0 && (
                        <div className="text-neutral-500 text-center py-10">No history found.</div>
                    )}

                    {history.map((item) => (
                        <div
                            key={item.id}
                            className="bg-neutral-800/50 border border-neutral-700/50 rounded-lg p-4 hover:bg-neutral-800 transition-colors flex items-center justify-between"
                        >
                            <div className="flex-1 min-w-0 mr-4">
                                <div className="flex items-center gap-3 mb-1">
                                    <span
                                        className={`w-2 h-2 rounded-full ${item.status === "success"
                                            ? "bg-green-500 shadow-[0_0_10px_rgba(34,197,94,0.4)]"
                                            : item.status === "failed"
                                                ? "bg-red-500 shadow-[0_0_10px_rgba(239,68,68,0.4)]"
                                                : "bg-yellow-500"
                                            }`}
                                    />
                                    <h3 className="font-medium text-white truncate">{item.goal}</h3>
                                </div>
                                <p className="text-xs text-neutral-500 pl-5">
                                    {formatTime(item.timestamp)} • ID: {item.id.slice(0, 8)}
                                </p>
                            </div>

                            <div className="flex gap-2 shrink-0">
                                {item.status === "failed" && (
                                    <button
                                        onClick={() => handleRepair(item.id)}
                                        className="px-3 py-1.5 bg-red-500/10 text-red-400 border border-red-500/20 rounded-md text-xs hover:bg-red-500/20 transition-colors flex items-center gap-2"
                                    >
                                        <span>🔧</span> Repair Skill
                                    </button>
                                )}
                                <button
                                    onClick={() => handleViewTrace(item.id)}
                                    className="px-3 py-1.5 bg-neutral-700 text-neutral-300 rounded-md text-xs hover:bg-neutral-600 transition-colors"
                                >
                                    View Trace
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
