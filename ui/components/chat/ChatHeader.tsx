import * as React from "react"
import { Brain, Mic, MicOff, Monitor, Settings } from "lucide-react"

interface ChatHeaderProps {
    earActive: boolean;
    onEarToggle: () => void;
}

export function ChatHeader({ earActive, onEarToggle }: ChatHeaderProps) {
    return (
        <header className="w-full py-6 flex items-center justify-between border-b border-white/5 bg-black/20 backdrop-blur-xl sticky top-0 z-20 rounded-b-2xl px-6 mb-4 shadow-lg shrink-0">
            <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-blue-600 flex items-center justify-center shadow-lg shadow-purple-500/20">
                    <Brain className="w-6 h-6 text-white" />
                </div>
                <div>
                    <h1 className="text-xl font-bold tracking-tight bg-gradient-to-r from-white to-white/60 bg-clip-text text-transparent">
                        Connex OpenAGI
                    </h1>
                    <div className="flex items-center gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                        <p className="text-xs text-white/40 font-medium tracking-wide uppercase">System Online</p>
                    </div>
                </div>
            </div>

            <div className="flex items-center gap-4">
                <button
                    onClick={onEarToggle}
                    className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold transition-all border ${earActive
                        ? 'bg-blue-500/10 text-blue-400 border-blue-500/30 shadow-[0_0_12px_rgba(59,130,246,0.3)]'
                        : 'bg-white/5 text-white/40 border-white/10 hover:bg-white/10'
                        }`}
                >
                    {earActive ? <Mic className="w-3.5 h-3.5" /> : <MicOff className="w-3.5 h-3.5" />}
                    <span>{earActive ? "Listening" : "Ear Off"}</span>
                </button>

                <div className="h-8 w-[1px] bg-white/10" />

                <div className="flex gap-2">
                    <div className="p-2 rounded-lg bg-white/5 hover:bg-white/10 transition-colors cursor-pointer text-white/60 hover:text-white">
                        <Monitor className="w-4 h-4" />
                    </div>
                    <div className="p-2 rounded-lg bg-white/5 hover:bg-white/10 transition-colors cursor-pointer text-white/60 hover:text-white">
                        <Settings className="w-4 h-4" />
                    </div>
                </div>
            </div>
        </header>
    )
}
