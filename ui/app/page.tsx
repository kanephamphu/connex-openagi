"use client"

import * as React from "react"
import { AnimatePresence, motion } from "framer-motion"
import { Loader2, Settings } from "lucide-react"

// Components
import { ChatHeader } from "@/components/chat/ChatHeader"
import { WelcomeScreen } from "@/components/chat/WelcomeScreen"
import { ChatMessage, Message, TraceStep } from "@/components/chat/ChatMessage"
import { ChatInput } from "@/components/chat/ChatInput"

export default function AGIChatPage() {
  const [prompt, setPrompt] = React.useState("")
  const [isProcessing, setIsProcessing] = React.useState(false)
  const [expandedMessages, setExpandedMessages] = React.useState<Set<number>>(new Set())
  const [pendingConfig, setPendingConfig] = React.useState<{
    skill: string;
    missing_keys: string[];
    schema: any;
  } | null>(null)
  const [configValues, setConfigValues] = React.useState<Record<string, string>>({})
  const [earActive, setEarActive] = React.useState(false)
  const [messages, setMessages] = React.useState<Message[]>([])

  const scrollAreaRef = React.useRef<HTMLDivElement>(null)

  // Auto-scroll
  React.useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight
    }
  }, [messages])

  // Polling sensor status
  React.useEffect(() => {
    const checkStatus = async () => {
      try {
        const res = await fetch("/health")
        const data = await res.json()
        setEarActive(data.ear_active)
      } catch { }
    }
    checkStatus()
    const interval = setInterval(checkStatus, 5000)
    return () => clearInterval(interval)
  }, [])

  const toggleMessageExpansion = (index: number) => {
    setExpandedMessages(prev => {
      const next = new Set(prev)
      if (next.has(index)) next.delete(index)
      else next.add(index)
      return next
    })
  }

  const handleEarToggle = async () => {
    const next = !earActive;
    const res = await fetch(`/api/sensors/ear/toggle?enabled=${next}`, { method: 'POST' });
    if (res.ok) setEarActive(next);
  }

  const handleSubmit = async () => {
    if (!prompt.trim() || isProcessing) return

    const userMsg: Message = { role: "user", content: prompt }
    setMessages(prev => [...prev, userMsg])
    setPrompt("")
    setIsProcessing(true)

    // Prep new assistant message
    setMessages(prev => [...prev, { role: "assistant", content: "", trace: [] }])

    try {
      const response = await fetch("/api/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMsg.content, context: { client: "web-ui" } })
      })

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) throw new Error("No reader")

      let buffer = ""
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split("\n")
        buffer = lines.pop() || ""

        for (const line of lines) {
          const trimmedLine = line.trim()
          if (!trimmedLine || !trimmedLine.startsWith("data: ")) continue
          try {
            const data = JSON.parse(trimmedLine.slice(6))

            if (data.status === "complete") {
              setIsProcessing(false)
              continue
            }

            if (data.phase) {
              setMessages(prev => {
                const newMsgs = [...prev]
                const lastIdx = newMsgs.length - 1
                if (lastIdx < 0 || newMsgs[lastIdx].role !== "assistant") return prev

                const lastMsg = { ...newMsgs[lastIdx] }
                const eventData = data.data || data
                let traceContent = ""

                if (data.phase === "planning") {
                  if (data.type === "planning_started") {
                    traceContent = `Planning: ${eventData.goal || "Analyzing request..."}`
                  } else if (data.type === "reasoning_token") {
                    const lastTraceIdx = lastMsg.trace ? lastMsg.trace.length - 1 : -1
                    const lastTrace = lastTraceIdx >= 0 ? lastMsg.trace![lastTraceIdx] : null

                    if (lastTrace && lastTrace.phase === "reasoning") {
                      lastTrace.content = eventData.partial_content || (lastTrace.content + eventData.token)
                    } else {
                      traceContent = eventData.token || "Thinking..."
                      data.phase = "reasoning"
                    }
                  } else if (data.type === "plan_complete") {
                    traceContent = "Plan finalized."
                  }
                } else if (data.phase === "execution") {
                  if (data.type === "action_started") {
                    traceContent = `Executing: ${eventData.skill} - ${eventData.description || ""}`
                  } else if (data.type === "action_completed") {
                    traceContent = `Completed: ${eventData.action_id}`
                    const output = eventData.output
                    if (output) {
                      const res = output.reply || output.response || output.result || output.text || (typeof output === 'string' ? output : null)
                      if (res) lastMsg.content = res
                    }
                  } else if (data.type === "execution_completed") {
                    traceContent = "Execution finished."
                  }
                }

                if (traceContent) {
                  lastMsg.trace = [...(lastMsg.trace || []), {
                    phase: data.phase,
                    type: data.type || "info",
                    content: traceContent,
                    status: "completed"
                  }]

                  // Auto-expand messages with trace data
                  setExpandedMessages(prev => {
                    const next = new Set(prev)
                    next.add(lastIdx)
                    return next
                  })
                }

                newMsgs[lastIdx] = lastMsg
                return newMsgs
              })
            }

            if (data.type === "config_required") {
              setPendingConfig({
                skill: data.skill,
                missing_keys: data.missing_keys,
                schema: data.schema
              })
              setIsProcessing(false)
            }
          } catch (e) {
            console.error("Parse error", e)
          }
        }
      }
    } catch (error) {
      console.error("Chat error:", error)
      setMessages(prev => [...prev.slice(0, -1), { role: "assistant", content: "Error communicating with AGI server. Please check your connection." }])
    } finally {
      setIsProcessing(false)
    }
  }

  const handleConfigSubmit = async () => {
    if (!pendingConfig) return;
    try {
      const response = await fetch("/api/skills/config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          skill_name: pendingConfig.skill,
          config: configValues
        })
      });

      if (response.ok) {
        setPendingConfig(null);
        setConfigValues({});
        setMessages(prev => [...prev, { role: "assistant", content: `Configuration for ${pendingConfig.skill} has been updated successfully.` }]);
      }
    } catch (e) {
      console.error("Failed to save config", e);
    }
  };

  return (
    <div className="flex h-screen bg-[#0f0f12] text-white font-sans overflow-hidden selection:bg-purple-500/30">

      {/* Background Ambience */}
      <div className="fixed inset-0 z-0 overflow-hidden pointer-events-none">
        <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-purple-900/10 rounded-full blur-[120px] mix-blend-screen animate-pulse" />
        <div className="absolute bottom-[-20%] right-[-10%] w-[40%] h-[60%] bg-blue-900/10 rounded-full blur-[120px] mix-blend-screen animate-pulse delay-1000" />
      </div>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col items-center justify-center relative z-10 w-full max-w-6xl mx-auto px-4 lg:px-6">

        <ChatHeader
          earActive={earActive}
          onEarToggle={handleEarToggle}
        />

        {/* Chat Area */}
        <div className="flex-1 w-full relative flex flex-col overflow-hidden bg-black/20 backdrop-blur-md border border-white/5 rounded-3xl shadow-2xl mb-4">

          <div
            ref={scrollAreaRef}
            className="flex-1 overflow-y-auto w-full p-4 space-y-8 scroll-smooth"
          >
            {messages.length === 0 && (
              <WelcomeScreen
                onSuggestionClick={(suggestion) => setPrompt(suggestion)}
              />
            )}

            <AnimatePresence initial={false}>
              {messages.map((msg, i) => (
                <ChatMessage
                  key={i}
                  index={i}
                  message={msg}
                  isExpanded={expandedMessages.has(i)}
                  onToggleExpand={toggleMessageExpansion}
                />
              ))}
            </AnimatePresence>

            {/* Loading Indicator */}
            {isProcessing && messages[messages.length - 1]?.role === 'user' && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex items-center gap-3 pl-2"
              >
                <div className="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center border border-white/10">
                  <Loader2 className="w-4 h-4 text-purple-400 animate-spin" />
                </div>
                <span className="text-xs text-white/40 animate-pulse">Thinking...</span>
              </motion.div>
            )}

            {/* Config Modal */}
            {pendingConfig && (
              <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
                <div className="w-full max-w-md bg-[#16161a] border border-white/10 rounded-2xl shadow-2xl p-6 relative overflow-hidden">
                  <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-purple-500 to-blue-500" />

                  <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                    <Settings className="w-5 h-5 text-purple-400" />
                    Configuration Required
                  </h3>
                  <p className="text-sm text-white/60 mb-6">
                    Please provide credentials for <strong>{pendingConfig.skill}</strong>.
                  </p>

                  <div className="space-y-4">
                    {pendingConfig.missing_keys.map(key => (
                      <div key={key}>
                        <label className="text-xs font-semibold text-white/40 uppercase tracking-wider mb-1 block">{key}</label>
                        <input
                          type="password"
                          value={configValues[key] || ""}
                          onChange={(e) => setConfigValues(prev => ({ ...prev, [key]: e.target.value }))}
                          className="w-full bg-black/20 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-purple-500/50 transition-colors"
                          placeholder="Enter value..."
                        />
                      </div>
                    ))}
                  </div>

                  <div className="flex gap-3 mt-8">
                    <button
                      onClick={() => setPendingConfig(null)}
                      className="flex-1 px-4 py-2.5 rounded-xl bg-white/5 text-white/60 hover:text-white hover:bg-white/10 transition-colors text-sm font-medium"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleConfigSubmit}
                      className="flex-1 px-4 py-2.5 rounded-xl bg-purple-600 text-white hover:bg-purple-500 transition-colors text-sm font-medium shadow-lg shadow-purple-500/20"
                    >
                      Save Credentials
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>

          <ChatInput
            prompt={prompt}
            isProcessing={isProcessing}
            onPromptChange={setPrompt}
            onSubmit={handleSubmit}
          />
        </div>

      </main>
    </div>
  )
}
