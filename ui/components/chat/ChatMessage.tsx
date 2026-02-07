import * as React from "react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import { motion, AnimatePresence } from "framer-motion"
import { Brain, Terminal, PlayCircle, CheckCircle2, ChevronDown, ChevronUp } from "lucide-react"

export type TraceStep = {
    phase: "planning" | "execution" | "reasoning"
    type: string
    content: string
    status: "running" | "completed" | "failed"
}

export type Message = {
    role: "user" | "assistant"
    content: string
    trace?: TraceStep[]
}

interface ChatMessageProps {
    message: Message;
    index: number;
    isExpanded: boolean;
    onToggleExpand: (index: number) => void;
}

export function ChatMessage({ message, index, isExpanded, onToggleExpand }: ChatMessageProps) {
    const isUser = message.role === 'user';

    return (
        <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ duration: 0.4, type: "spring", stiffness: 100 }}
            className={`flex gap-4 ${isUser ? 'justify-end' : 'justify-start'} group px-2`}
        >
            {/* Avatar (Assistant) */}
            {!isUser && (
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shrink-0 shadow-lg mt-1 ring-1 ring-white/10">
                    <Brain className="w-4 h-4 text-white" />
                </div>
            )}

            <div className={`flex flex-col gap-2 max-w-[85%] lg:max-w-[70%]`}>
                <div className={`p-5 rounded-2xl shadow-md backdrop-blur-md border border-white/5 relative overflow-hidden ${isUser
                    ? 'bg-blue-600/20 text-blue-50 border-blue-500/20 rounded-tr-sm'
                    : 'bg-white/5 text-gray-100 rounded-tl-sm'
                    }`}>
                    {isUser && (
                        <div className="absolute inset-0 bg-gradient-to-br from-blue-600/10 to-transparent pointer-events-none" />
                    )}

                    <div className="relative z-10">
                        {isUser ? (
                            <p className="whitespace-pre-wrap leading-relaxed">{message.content}</p>
                        ) : (
                            <div className="prose prose-invert prose-p:leading-relaxed prose-code:bg-black/50 prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-code:text-blue-300 prose-pre:bg-black/50 prose-pre:border prose-pre:border-white/10 max-w-none">
                                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                    {message.content || (message.trace?.length ? "Processing..." : "")}
                                </ReactMarkdown>
                            </div>
                        )}
                    </div>
                </div>

                {/* Trace / Execution Plan */}
                {message.trace && message.trace.length > 0 && (
                    <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        className="ml-1 mt-1 rounded-xl border border-white/5 bg-black/20 overflow-hidden w-full"
                    >
                        <button
                            onClick={() => onToggleExpand(index)}
                            className="w-full px-4 py-2 flex items-center justify-between text-xs font-medium text-white/40 hover:text-white/80 hover:bg-white/5 transition-colors uppercase tracking-wider"
                        >
                            <div className="flex items-center gap-2">
                                <Terminal className="w-3 h-3" />
                                Execution Trace
                            </div>
                            {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                        </button>

                        <AnimatePresence>
                            {isExpanded && (
                                <motion.div
                                    initial={{ height: 0, opacity: 0 }}
                                    animate={{ height: "auto", opacity: 1 }}
                                    exit={{ height: 0, opacity: 0 }}
                                    className="px-2 pb-2"
                                >
                                    <div className="bg-black/40 rounded-lg p-2 max-h-64 overflow-y-auto space-y-1 custom-scrollbar">
                                        {message.trace.map((step, idx) => (
                                            <div key={idx} className="flex gap-3 items-start p-2 rounded hover:bg-white/5 transition-colors border-b border-white/5 last:border-0">
                                                <div className="shrink-0 mt-0.5">
                                                    {step.phase === 'planning' ? (
                                                        <PlayCircle className="w-3.5 h-3.5 text-blue-400" />
                                                    ) : step.phase === 'reasoning' ? (
                                                        <Brain className="w-3.5 h-3.5 text-purple-400" />
                                                    ) : (
                                                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                                                    )}
                                                </div>
                                                <div className="text-xs font-mono text-white/70 leading-relaxed break-words">
                                                    {step.content}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </motion.div>
                )}
            </div>
        </motion.div>
    )
}
