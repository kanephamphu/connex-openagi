import * as React from "react"
import { Activity, Clock, Download, Star } from "lucide-react"

interface MotivationSettingsProps {
    config: Record<string, any>;
    onSave: (newConfig: Record<string, any>) => void;
    onClose: () => void;
}

export function MotivationSettings({ config, onSave, onClose }: MotivationSettingsProps) {
    const [localConfig, setLocalConfig] = React.useState({
        motivation_interval: config.motivation_interval || 3600,
        skill_review_min_rating: config.skill_review_min_rating || 4.0,
        skill_review_min_downloads: config.skill_review_min_downloads || 100
    });

    const handleChange = (key: string, value: any) => {
        setLocalConfig(prev => ({ ...prev, [key]: value }));
    };

    const handleSave = () => {
        onSave(localConfig);
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
            <div className="w-full max-w-md bg-[#16161a] border border-white/10 rounded-2xl shadow-2xl p-6 relative overflow-hidden">
                <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-orange-500 to-red-500" />

                <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                    <Activity className="w-5 h-5 text-orange-400" />
                    Motivation Settings
                </h3>
                <p className="text-sm text-white/60 mb-6">
                    Configure how frequently the AGI reviews missing skills and attempts to recover them.
                </p>

                <div className="space-y-6">
                    {/* Interval */}
                    <div>
                        <label className="text-xs font-semibold text-white/40 uppercase tracking-wider mb-2 flex items-center gap-2">
                            <Clock className="w-3 h-3" />
                            Check Interval (Seconds)
                        </label>
                        <input
                            type="number"
                            value={localConfig.motivation_interval}
                            onChange={(e) => handleChange("motivation_interval", parseInt(e.target.value))}
                            className="w-full bg-black/20 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-orange-500/50 transition-colors"
                        />
                        <p className="text-xs text-white/30 mt-1">Default: 3600s (1 hour)</p>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        {/* Min Rating */}
                        <div>
                            <label className="text-xs font-semibold text-white/40 uppercase tracking-wider mb-2 flex items-center gap-2">
                                <Star className="w-3 h-3" />
                                Min Rating
                            </label>
                            <input
                                type="number"
                                step="0.1"
                                max="5.0"
                                value={localConfig.skill_review_min_rating}
                                onChange={(e) => handleChange("skill_review_min_rating", parseFloat(e.target.value))}
                                className="w-full bg-black/20 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-orange-500/50 transition-colors"
                            />
                        </div>

                        {/* Min Downloads */}
                        <div>
                            <label className="text-xs font-semibold text-white/40 uppercase tracking-wider mb-2 flex items-center gap-2">
                                <Download className="w-3 h-3" />
                                Min Downloads
                            </label>
                            <input
                                type="number"
                                value={localConfig.skill_review_min_downloads}
                                onChange={(e) => handleChange("skill_review_min_downloads", parseInt(e.target.value))}
                                className="w-full bg-black/20 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-orange-500/50 transition-colors"
                            />
                        </div>
                    </div>
                </div>

                <div className="flex gap-3 mt-8">
                    <button
                        onClick={onClose}
                        className="flex-1 px-4 py-2.5 rounded-xl bg-white/5 text-white/60 hover:text-white hover:bg-white/10 transition-colors text-sm font-medium"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleSave}
                        className="flex-1 px-4 py-2.5 rounded-xl bg-orange-600 text-white hover:bg-orange-500 transition-colors text-sm font-medium shadow-lg shadow-orange-500/20"
                    >
                        Save Settings
                    </button>
                </div>
            </div>
        </div>
    );
}
