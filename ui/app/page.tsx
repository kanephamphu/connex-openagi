"use client"

import * as React from "react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Zap, Brain, Terminal, MessageSquare, Loader2, PlayCircle, CheckCircle2, ChevronDown, ChevronUp, Mic, MicOff } from "lucide-react"

// Types
type Message = {
  role: "user" | "assistant"
  content: string
  trace?: TraceStep[]
}

type TraceStep = {
  phase: "planning" | "execution" | "reasoning"
  type: string
  content: string
  status: "running" | "completed" | "failed"
}

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
  const [messages, setMessages] = React.useState<Message[]>([])
  const scrollAreaRef = React.useRef<HTMLDivElement>(null)

  // Auto-scroll
  React.useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight
    }
  }, [messages])

  const handleSubmit = async () => {
    if (!prompt.trim() || isProcessing) return

    const userMsg: Message = { role: "user", content: prompt }
    setMessages(prev => [...prev, userMsg])
    setPrompt("")
    setIsProcessing(true)

    // Prep new assistant message
    setMessages(prev => [...prev, { role: "assistant", content: "", trace: [] }])

    try {
      // Use relative path which will be proxied or served by same origin
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
            console.log("AGI Event:", data)

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
                    // Update the last trace if it's already reasoning, or add a new one
                    const lastTraceIdx = lastMsg.trace ? lastMsg.trace.length - 1 : -1
                    const lastTrace = lastTraceIdx >= 0 ? lastMsg.trace![lastTraceIdx] : null

                    if (lastTrace && lastTrace.phase === "reasoning") {
                      lastTrace.content = eventData.partial_content || (lastTrace.content + eventData.token)
                      traceContent = "" // Handled
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
                      if (res) {
                        lastMsg.content = res
                      }
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
              setIsProcessing(false) // Stop processing to show prompt
            }
          } catch (e) {
            console.error("Parse error", e, trimmedLine)
          }
        }
      }
    } catch (error) {
      console.error("Chat error:", error)
      setMessages(prev => [...prev.slice(0, -1), { role: "assistant", content: "Error communicating with AGI server." }])
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
        // Optionally notify user or retry last query?
        // For now, simple success message
        setMessages(prev => [...prev, { role: "assistant", content: `Configuration for ${pendingConfig.skill} updated successfully. You can try your request again.` }]);
      }
    } catch (e) {
      console.error("Failed to save config", e);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-background text-foreground">
      <header className="border-b p-4 flex items-center justify-between bg-white/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="flex items-center gap-2">
          <Brain className="w-6 h-6 text-primary" />
          <div>
            <h1 className="text-lg font-bold leading-none">Connex AGI</h1>
            <p className="text-xs text-muted-foreground">Autonomous Planning Agent</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div
            onClick={async () => {
              const next = !earActive;
              const res = await fetch(`/api/sensors/ear/toggle?enabled=${next}`, { method: 'POST' });
              if (res.ok) setEarActive(next);
            }}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-[10px] font-bold uppercase tracking-wider transition-all cursor-pointer border ${earActive ? 'bg-blue-500/10 text-blue-500 border-blue-500/20 shadow-[0_0_10px_rgba(59,130,246,0.2)]' : 'bg-neutral-100 text-neutral-400 border-neutral-200'}`}
          >
            {earActive ? <Mic className="w-3.5 h-3.5 animate-pulse" /> : <MicOff className="w-3.5 h-3.5" />}
            Ear: {earActive ? "Listening" : "Off"}
          </div>
          <div className="text-xs text-muted-foreground font-mono">
            System: Online
          </div>
        </div>
      </header>

      <main className="flex-1 overflow-hidden relative flex flex-col max-w-5xl mx-auto w-full">
        <ScrollArea className="flex-1 p-4" ref={scrollAreaRef}>
          <div className="flex flex-col gap-6 pb-4">
            {messages.length === 0 && (
              <div className="flex flex-col items-center justify-center min-h-[50vh] text-center text-muted-foreground animate-in fade-in duration-500">
                <div className="w-20 h-20 rounded-full bg-primary/5 flex items-center justify-center mb-6">
                  <Brain className="w-10 h-10 text-primary opacity-50" />
                </div>
                <h3 className="text-xl font-medium mb-2">Ready to assist</h3>
                <p className="max-w-md text-sm">
                  I can help you plan complex tasks, research the web, execute code, and manage skills.
                </p>
              </div>
            )}

            {messages.map((msg, i) => (
              <div key={i} className={`flex gap-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start mb-8'} group`}>
                {msg.role === 'assistant' && (
                  <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center border border-primary/20 overflow-hidden shrink-0 mt-1">
                    <Brain className="w-4 h-4 text-primary" />
                  </div>
                )}

                <div className={`flex flex-col gap-2 max-w-[85%] lg:max-w-[75%]`}>
                  <div className={`p-4 rounded-2xl shadow-sm overflow-hidden ${msg.role === 'user'
                    ? 'bg-primary text-primary-foreground rounded-tr-none'
                    : 'bg-white border text-foreground rounded-tl-none'
                    }`}>
                    {msg.role === 'user' ? (
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                    ) : (
                      <div className="prose prose-sm dark:prose-invert max-w-none text-foreground break-words leading-relaxed">
                        <ReactMarkdown
                          remarkPlugins={[remarkGfm]}
                          components={{
                            code({ node, inline, className, children, ...props }: any) {
                              const match = /language-(\w+)/.exec(className || '')
                              return !inline ? (
                                <div className="relative my-4 rounded-lg bg-slate-950 p-4 font-mono text-sm text-slate-50 overflow-x-auto">
                                  <div className="absolute top-0 right-0 p-2 text-xs text-slate-400 font-sans">
                                    {match ? match[1] : 'code'}
                                  </div>
                                  <code className={className} {...props}>
                                    {children}
                                  </code>
                                </div>
                              ) : (
                                <code className="bg-muted px-1.5 py-0.5 rounded-md font-mono text-sm" {...props}>
                                  {children}
                                </code>
                              )
                            },
                            ul({ children }) { return <ul className="list-disc pl-5 my-2 space-y-1">{children}</ul> },
                            ol({ children }) { return <ol className="list-decimal pl-5 my-2 space-y-1">{children}</ol> },
                            h1({ children }) { return <h1 className="text-xl font-bold mt-6 mb-3 border-b pb-2">{children}</h1> },
                            h2({ children }) { return <h2 className="text-lg font-semibold mt-5 mb-2">{children}</h2> },
                            h3({ children }) { return <h3 className="text-base font-semibold mt-4 mb-2">{children}</h3> },
                            p({ children }) { return <p className="mb-3 last:mb-0 leading-7">{children}</p> },
                            a({ children, href }) { return <a href={href} target="_blank" rel="noopener noreferrer" className="text-primary underline underline-offset-2 hover:text-primary/80 transition-colors">{children}</a> },
                            blockquote({ children }) { return <blockquote className="border-l-4 border-primary/20 pl-4 py-1 my-4 italic bg-muted/30 rounded-r-lg">{children}</blockquote> }
                          }}
                        >
                          {msg.content || (msg.trace?.length ? "Thinking process..." : "")}
                        </ReactMarkdown>
                      </div>
                    )}
                  </div>

                  {/* Thought Process (Claude Style) */}
                  {msg.trace && msg.trace.length > 0 && (
                    <div className="ml-1 mt-1 bg-muted/30 rounded-lg border text-xs overflow-hidden w-full max-w-lg">
                      <button
                        onClick={() => toggleMessageExpansion(i)}
                        className="w-full px-3 py-1.5 bg-muted/50 border-b flex items-center justify-between font-medium text-muted-foreground/80 hover:bg-muted/70 transition-colors"
                      >
                        <div className="flex items-center gap-2">
                          <Terminal className="w-3 h-3" />
                          Execution Plan
                        </div>
                        {expandedMessages.has(i) ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                      </button>

                      {expandedMessages.has(i) && (
                        <div className="p-2 space-y-1 max-h-60 overflow-y-auto animate-in slide-in-from-top-2 duration-200">
                          {msg.trace.map((step, idx) => (
                            <div key={idx} className="flex gap-2 items-start py-1.5 border-b border-border/40 last:border-0 pl-1">
                              {step.phase === 'planning' ? (
                                <PlayCircle className="w-3.5 h-3.5 mt-0.5 text-blue-500 shrink-0" />
                              ) : step.phase === 'reasoning' ? (
                                <Brain className="w-3.5 h-3.5 mt-0.5 text-purple-500 shrink-0" />
                              ) : (
                                <CheckCircle2 className="w-3.5 h-3.5 mt-0.5 text-green-500 shrink-0" />
                              )}
                              <div className="font-mono opacity-90 leading-snug">{step.content}</div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {msg.role === 'user' && (
                  <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center border overflow-hidden shrink-0 mt-1">
                    <span className="text-xs font-semibold text-gray-500">YOU</span>
                  </div>
                )}
              </div>
            ))}

            {isProcessing && messages[messages.length - 1].role === 'user' && (
              <div className="flex gap-4 animate-pulse">
                <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center border border-primary/20 shrink-0">
                  <Loader2 className="w-4 h-4 text-primary animate-spin" />
                </div>
                <div className="bg-white border shadow-sm p-4 rounded-2xl rounded-tl-none w-32 h-12 flex items-center">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-primary/40 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                    <div className="w-2 h-2 bg-primary/40 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                    <div className="w-2 h-2 bg-primary/40 rounded-full animate-bounce"></div>
                  </div>
                </div>
              </div>
            )}

            {pendingConfig && (
              <div className="flex justify-center my-8 animate-in zoom-in-95 duration-300">
                <Card className="w-full max-w-md border-primary/30 shadow-lg relative overflow-hidden">
                  <div className="absolute top-0 left-0 w-1 h-full bg-primary"></div>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-lg flex items-center gap-2">
                      <Zap className="w-4 h-4 text-primary" />
                      Configuration Required
                    </CardTitle>
                    <CardDescription>
                      The <strong>{pendingConfig.skill}</strong> skill needs these credentials to proceed.
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {pendingConfig.missing_keys.map(key => (
                      <div key={key} className="space-y-1.5">
                        <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">{key}</label>
                        <input
                          type="password"
                          className="w-full p-2 text-sm border rounded-md bg-muted/50 focus:ring-2 focus:ring-primary/20 outline-none transition-all"
                          placeholder={`Enter ${key}...`}
                          value={configValues[key] || ""}
                          onChange={(e) => setConfigValues(prev => ({ ...prev, [key]: e.target.value }))}
                        />
                      </div>
                    ))}
                    <div className="pt-2 flex gap-2">
                      <Button onClick={handleConfigSubmit} className="flex-1">Save Configuration</Button>
                      <Button variant="ghost" onClick={() => setPendingConfig(null)}>Cancel</Button>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}
          </div>
        </ScrollArea>

        <div className="p-4 bg-background border-t">
          <div className="relative max-w-4xl mx-auto">
            <Textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  handleSubmit()
                }
              }}
              placeholder="Send a message to AGI..."
              className="min-h-[60px] pr-14 resize-none py-4 text-base shadow-sm border-gray-200 focus:border-primary/50 focus:ring-primary/20"
            />
            <Button
              className="absolute right-3 bottom-3 h-9 w-9 p-0 rounded-lg shadow-sm transition-all hover:scale-105"
              size="sm"
              onClick={handleSubmit}
              disabled={!prompt.trim() || isProcessing}
            >
              {isProcessing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Zap className="h-4 w-4 fill-current" />}
            </Button>
          </div>
          <div className="text-center mt-2">
            <p className="text-[10px] text-muted-foreground">
              AGI can make mistakes. Please verify important information.
            </p>
          </div>
        </div>
      </main>
    </div>
  )
}
