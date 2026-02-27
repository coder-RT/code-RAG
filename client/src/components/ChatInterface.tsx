import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Bot, User, Loader2, Sparkles, ChevronDown, Database } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { api, Project } from '@/lib/api'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: { file: string; snippet: string }[]
  timestamp: Date
}

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [projects, setProjects] = useState<Project[]>([])
  const [selectedProject, setSelectedProject] = useState<string>('')
  const [projectsLoading, setProjectsLoading] = useState(true)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const fetchProjects = async () => {
      try {
        const response = await api.getProjects()
        const data = response.data.data as { projects: Project[] }
        setProjects(data?.projects || [])
        if (data?.projects?.length > 0) {
          setSelectedProject(data.projects[0].name)
        }
      } catch (error) {
        console.error('Failed to fetch projects:', error)
      } finally {
        setProjectsLoading(false)
      }
    }
    fetchProjects()
  }, [])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const sendMessage = async () => {
    if (!input.trim() || isLoading || !selectedProject) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      const response = await api.queryCodebase(input, selectedProject)
      const data = response.data.data as { answer: string; sources?: { file: string; snippet: string }[] }

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data?.answer || 'No answer received',
        sources: data?.sources,
        timestamp: new Date(),
      }

      setMessages((prev) => [...prev, assistantMessage])
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your request. Please try again.',
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-200px)] glass rounded-2xl overflow-hidden">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.length === 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-col items-center justify-center h-full text-center"
          >
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-accent-cyan/20 to-accent-violet/20 flex items-center justify-center mb-4 border border-accent-cyan/30">
              <Sparkles className="w-8 h-8 text-accent-cyan" />
            </div>
            <h3 className="text-xl font-display font-bold mb-2">Ask about your codebase</h3>
            <p className="text-carbon-400 max-w-md">
              I can explain code, describe architecture, show dependencies, and help you understand how everything connects.
            </p>
          </motion.div>
        )}

        <AnimatePresence>
          {messages.map((message) => (
            <motion.div
              key={message.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className={`flex gap-4 ${message.role === 'user' ? 'justify-end' : ''}`}
            >
              {message.role === 'assistant' && (
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-accent-cyan to-accent-violet flex items-center justify-center flex-shrink-0">
                  <Bot className="w-4 h-4 text-white" />
                </div>
              )}
              
              <div className={`max-w-[80%] ${message.role === 'user' ? 'order-first' : ''}`}>
                <div
                  className={`rounded-2xl p-4 ${
                    message.role === 'user'
                      ? 'bg-gradient-to-r from-accent-cyan to-accent-violet text-white'
                      : 'bg-carbon-900 border border-carbon-700'
                  }`}
                >
                  <ReactMarkdown
                    components={{
                      code({ className, children, ...props }) {
                        const match = /language-(\w+)/.exec(className || '')
                        const isInline = !match
                        
                        return isInline ? (
                          <code className="bg-carbon-800 px-1.5 py-0.5 rounded text-accent-cyan font-mono text-sm" {...props}>
                            {children}
                          </code>
                        ) : (
                          <SyntaxHighlighter
                            style={vscDarkPlus}
                            language={match[1]}
                            PreTag="div"
                            className="rounded-lg !bg-carbon-950 !mt-2"
                          >
                            {String(children).replace(/\n$/, '')}
                          </SyntaxHighlighter>
                        )
                      },
                    }}
                  >
                    {message.content}
                  </ReactMarkdown>
                </div>
                
                {/* Sources */}
                {message.sources && message.sources.length > 0 && (
                  <div className="mt-2 space-y-1">
                    <p className="text-xs text-carbon-500">Sources:</p>
                    {message.sources.map((source, idx) => (
                      <div key={idx} className="text-xs text-carbon-400 flex items-center gap-2">
                        <span className="text-accent-cyan font-mono">{source.file}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {message.role === 'user' && (
                <div className="w-8 h-8 rounded-lg bg-carbon-700 flex items-center justify-center flex-shrink-0">
                  <User className="w-4 h-4 text-carbon-300" />
                </div>
              )}
            </motion.div>
          ))}
        </AnimatePresence>

        {isLoading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex gap-4"
          >
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-accent-cyan to-accent-violet flex items-center justify-center">
              <Loader2 className="w-4 h-4 text-white animate-spin" />
            </div>
            <div className="bg-carbon-900 border border-carbon-700 rounded-2xl p-4">
              <div className="flex items-center gap-2 text-carbon-400">
                <span>Analyzing codebase</span>
                <span className="flex gap-1">
                  <span className="w-1.5 h-1.5 bg-accent-cyan rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <span className="w-1.5 h-1.5 bg-accent-cyan rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <span className="w-1.5 h-1.5 bg-accent-cyan rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </span>
              </div>
            </div>
          </motion.div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-carbon-700">
        {/* Project Selector */}
        <div className="mb-3 flex items-center gap-2">
          <Database className="w-4 h-4 text-carbon-400" />
          <span className="text-sm text-carbon-400">Project:</span>
          {projectsLoading ? (
            <span className="text-sm text-carbon-500">Loading projects...</span>
          ) : projects.length === 0 ? (
            <span className="text-sm text-carbon-500">No indexed projects. Index a codebase first.</span>
          ) : (
            <div className="relative">
              <select
                value={selectedProject}
                onChange={(e) => setSelectedProject(e.target.value)}
                className="appearance-none bg-carbon-900 border border-carbon-700 rounded-lg px-3 py-1.5 pr-8 text-sm text-white focus:outline-none focus:border-accent-cyan cursor-pointer"
              >
                {projects.map((project) => (
                  <option key={project.name} value={project.name}>
                    {project.name} ({project.count} chunks)
                  </option>
                ))}
              </select>
              <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-carbon-400 pointer-events-none" />
            </div>
          )}
        </div>
        
        <div className="flex gap-3">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={selectedProject ? `Ask about ${selectedProject}...` : "Select a project first..."}
            rows={1}
            disabled={!selectedProject}
            className="flex-1 bg-carbon-900 border border-carbon-700 rounded-xl px-4 py-3 text-white placeholder-carbon-500 focus:outline-none focus:border-accent-cyan resize-none disabled:opacity-50 disabled:cursor-not-allowed"
          />
          <button
            onClick={sendMessage}
            disabled={!input.trim() || isLoading || !selectedProject}
            className="px-4 py-3 rounded-xl bg-gradient-to-r from-accent-cyan to-accent-violet text-white font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:opacity-90 transition-opacity"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  )
}

