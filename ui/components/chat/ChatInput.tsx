import * as React from "react"
import { Loader2, Send } from "lucide-react"

interface ChatInputProps {
    prompt: string;
    isProcessing: boolean;
    onPromptChange: (value: string) => void;
    onSubmit: () => void;
}

export function ChatInput({ prompt, isProcessing, onPromptChange, onSubmit }: ChatInputProps) {
    const textareaRef = React.useRef<HTMLTextAreaElement>(null)

    // Auto-resize
    React.useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto'
            textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px'
        }
    }, [prompt])

    return (
        <div className="p-4 bg-black/20 backdrop-blur-xl border-t border-white/5">
            <div className="relative max-w-4xl mx-auto">
                <div className="absolute inset-0 bg-gradient-to-r from-purple-500/10 to-blue-500/10 rounded-2xl blur-xl" />
                <div className="relative bg-white/5 border border-white/10 rounded-2xl p-2 flex gap-4 shadow-lg focus-within:ring-1 focus-within:ring-purple-500/50 transition-all">
                    <textarea
                        ref={textareaRef}
                        value={prompt}
                        onChange={(e) => onPromptChange(e.target.value)}
                        onKeyDown={(e) => {
                            if (e.key === 'Enter' && !e.shiftKey) {
                                e.preventDefault()
                                onSubmit()
                            }
                        }}
                        placeholder="Type a message..."
                        className="w-full bg-transparent border-none focus:ring-0 text-white placeholder-white/20 resize-none py-3 px-3 min-h-[50px] max-h-[200px] text-[15px] leading-relaxed scrollbar-hide"
                        style={{ height: 'auto' }}
                    />
                    <button
                        onClick={onSubmit}
                        disabled={!prompt.trim() || isProcessing}
                        className={`self-end p-3 rounded-xl transition-all duration-200 border border-white/5 ${prompt.trim() && !isProcessing
                            ? 'bg-purple-600 text-white shadow-lg shadow-purple-500/20 hover:scale-105 active:scale-95'
                            : 'bg-white/5 text-white/20 cursor-not-allowed'
                            }`}
                    >
                        {isProcessing ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
                    </button>
                </div>
            </div>
            <div className="text-center mt-3">
                <p className="text-[10px] text-white/20 font-medium tracking-wide">
                    POWERED BY CONNEX OPENAGI • v1.0.0
                </p>
            </div>
        </div>
    )
}
