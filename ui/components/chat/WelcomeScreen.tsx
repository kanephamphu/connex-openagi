import * as React from "react"
import { Sparkles, ArrowRight } from "lucide-react"
import { motion } from "framer-motion"

interface WelcomeScreenProps {
    onSuggestionClick: (suggestion: string) => void;
}

export function WelcomeScreen({ onSuggestionClick }: WelcomeScreenProps) {
    const suggestions = [
        { label: "Plan a travel itinerary", icon: "✈️" },
        { label: "Analyze market trends", icon: "📈" },
        { label: "Debug python script", icon: "🐍" },
        { label: "Research SEO strategies", icon: "🔍" }
    ]

    return (
        <div className="h-full flex flex-col items-center justify-center text-center p-8 animate-in fade-in zoom-in-95 duration-700">
            <motion.div
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ duration: 0.5, delay: 0.1 }}
                className="w-24 h-24 rounded-3xl bg-gradient-to-tr from-purple-500/20 to-blue-500/20 flex items-center justify-center mb-8 border border-white/5 shadow-2xl shadow-purple-500/10 backdrop-blur-sm"
            >
                <Sparkles className="w-10 h-10 text-white/50" />
            </motion.div>

            <motion.h2
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ duration: 0.5, delay: 0.2 }}
                className="text-3xl font-bold bg-gradient-to-b from-white to-white/40 bg-clip-text text-transparent mb-4"
            >
                How can I help you today?
            </motion.h2>

            <motion.div
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ duration: 0.5, delay: 0.3 }}
                className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl w-full text-sm"
            >
                {suggestions.map((item, i) => (
                    <button
                        key={i}
                        onClick={() => onSuggestionClick(item.label)}
                        className="group p-4 rounded-xl bg-white/5 border border-white/5 hover:bg-white/10 hover:border-white/20 hover:text-white transition-all text-left text-white/60 flex items-center justify-between"
                    >
                        <span className="flex items-center gap-3">
                            <span className="opacity-50 grayscale group-hover:grayscale-0 transition-all">{item.icon}</span>
                            {item.label}
                        </span>
                        <ArrowRight className="w-4 h-4 opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all text-white/40" />
                    </button>
                ))}
            </motion.div>
        </div>
    )
}
