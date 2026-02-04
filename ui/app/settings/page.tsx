
"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { ArrowLeft, Save, RefreshCw } from "lucide-react";

export default function SettingsPage() {
    const [config, setConfig] = useState<any>({});
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState<string | null>(null);

    useEffect(() => {
        fetchConfig();
    }, []);

    const fetchConfig = async () => {
        try {
            setLoading(true);
            const res = await fetch("http://localhost:8001/api/config");
            const data = await res.json();
            setConfig(data.config || {});
        } catch (e) {
            console.error("Failed to load config", e);
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async (e: React.FormEvent) => {
        e.preventDefault();
        setSaving(true);
        setMessage(null);

        // Prepare payload (filter out masked values if unchanged?)
        // Actually, for simplicity, we send back what changed. 
        // If the user didn't edit a masked value (***), we shouldn't send it back 
        // or the backend needs to ignore it. 
        // Current backend logic: sets whatever is sent.
        // Issue: If I send "OpenAI Key: ***123", it will save that literal string.
        // Fix: We need to detect if value starts with "***". If so, remove it from payload.

        const payload: any = {};
        for (const [key, value] of Object.entries(config)) {
            if (typeof value === 'string' && value.startsWith("***")) {
                continue; // Skip masked values
            }
            payload[key] = value;
        }

        try {
            const res = await fetch("http://localhost:8001/api/config", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ config: payload }),
            });
            if (res.ok) {
                setMessage("Configuration saved successfully!");
                // Reload to get fresh state (and re-mask)
                fetchConfig();
            } else {
                setMessage("Failed to save configuration.");
            }
        } catch (e) {
            setMessage("Error saving configuration.");
        } finally {
            setSaving(false);
        }
    };

    const handleChange = (key: string, value: any) => {
        setConfig((prev: any) => ({ ...prev, [key]: value }));
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
            </div>
        );
    }

    // Group settings for better UI
    const apiKeys = ["openai_api_key", "anthropic_api_key", "deepseek_api_key", "groq_api_key", "google_api_key"];
    const modelSettings = ["default_planner", "default_executor", "planner_model", "executor_model", "temperature", "max_tokens"];
    const runtimeSettings = ["verbose", "max_retries", "action_timeout", "self_correction_enabled"];

    const renderField = (key: string) => {
        const value = config[key];
        const isBool = typeof value === "boolean" || (value === undefined && (key === "verbose" || key === "self_correction_enabled"));

        return (
            <div key={key} className="mb-4">
                <label className="block text-sm font-medium text-gray-400 mb-1 capitalize">
                    {key.replace(/_/g, " ")}
                </label>

                {isBool ? (
                    <div className="flex items-center space-x-2">
                        <button
                            type="button"
                            onClick={() => handleChange(key, !value)}
                            className={`w-12 h-6 rounded-full transition-colors flex items-center px-1 ${value ? 'bg-green-500' : 'bg-gray-700'}`}
                        >
                            <div className={`w-4 h-4 bg-white rounded-full transition-transform ${value ? 'translate-x-6' : 'translate-x-0'}`} />
                        </button>
                        <span className="text-gray-300">{value ? "Enabled" : "Disabled"}</span>
                    </div>
                ) : (
                    <input
                        type={typeof value === 'number' ? 'number' : 'text'}
                        value={value ?? ""}
                        onChange={(e) => {
                            const val = e.target.type === 'number' ? parseFloat(e.target.value) : e.target.value;
                            handleChange(key, val);
                        }}
                        className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white focus:ring-2 focus:ring-primary-500 focus:outline-none"
                    />
                )}
            </div>
        );
    };

    return (
        <div className="min-h-screen bg-gray-900 text-white p-8 font-sans">
            <div className="max-w-4xl mx-auto">
                <header className="flex items-center justify-between mb-8">
                    <div className="flex items-center gap-4">
                        <Link href="/" className="p-2 hover:bg-gray-800 rounded-full transition-colors">
                            <ArrowLeft size={24} />
                        </Link>
                        <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
                            System Settings
                        </h1>
                    </div>
                    <button
                        onClick={fetchConfig}
                        className="p-2 bg-gray-800 hover:bg-gray-700 rounded text-gray-400 hover:text-white transition-colors"
                        title="Refresh Config"
                    >
                        <RefreshCw size={20} />
                    </button>
                </header>

                {message && (
                    <div className={`p-4 mb-6 rounded ${message.includes("success") ? "bg-green-900/50 text-green-200" : "bg-red-900/50 text-red-200"}`}>
                        {message}
                    </div>
                )}

                <form onSubmit={handleSave} className="space-y-8">
                    {/* API Keys Section */}
                    <section className="bg-gray-800/50 p-6 rounded-lg border border-gray-700">
                        <h2 className="text-xl font-semibold mb-4 text-secondary-400 border-b border-gray-700 pb-2">
                            API Credentials
                        </h2>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {apiKeys.map(key => renderField(key))}
                        </div>
                    </section>

                    {/* Model Settings Section */}
                    <section className="bg-gray-800/50 p-6 rounded-lg border border-gray-700">
                        <h2 className="text-xl font-semibold mb-4 text-blue-400 border-b border-gray-700 pb-2">
                            Model Configuration
                        </h2>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {modelSettings.map(key => renderField(key))}
                        </div>
                    </section>

                    {/* Runtime Params Section */}
                    <section className="bg-gray-800/50 p-6 rounded-lg border border-gray-700">
                        <h2 className="text-xl font-semibold mb-4 text-purple-400 border-b border-gray-700 pb-2">
                            Runtime Parameters
                        </h2>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {runtimeSettings.map(key => renderField(key))}
                        </div>
                    </section>

                    {/* Save Action */}
                    <div className="sticky bottom-6 flex justify-end">
                        <button
                            type="submit"
                            disabled={saving}
                            className="flex items-center gap-2 px-8 py-3 bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white font-bold rounded-full shadow-lg transform transition-all hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            <Save size={20} />
                            {saving ? "Saving..." : "Save Changes"}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
