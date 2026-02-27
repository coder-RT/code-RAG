import { useState, useRef, useEffect, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Bot, User, Loader2, Sparkles, ChevronDown, FileCode, ChevronRight, Cpu, Plus, Database } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { api, Project, LLMModel } from '@/lib/api'
import { useChatStore, Message } from '@/stores/chatStore'
import ChatSidebar from './ChatSidebar'

export default function ChatInterface() {
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [projects, setProjects] = useState<Project[]>([])
  const [selectedProject, setSelectedProject] = useState<string>('')
  const [projectsLoading, setProjectsLoading] = useState(true)
  const [models, setModels] = useState<LLMModel[]>([])
  const [selectedModel, setSelectedModel] = useState<string>('gpt-4o')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Zustand store for persistent conversations
  const { 
    addMessage, 
    setActiveProject, 
    setActiveConversation,
    createConversation,
    getActiveConversation,
    activeConversationId,
    projects: chatProjects,
  } = useChatStore()
  
  // Get messages for current conversation (reactive to store changes)
  const activeConversation = useMemo(() => {
    return getActiveConversation()
  }, [getActiveConversation, activeConversationId, chatProjects])

  const messages = activeConversation?.messages || []

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [projectsRes, modelsRes] = await Promise.all([
          api.getProjects(),
          api.getModels()
        ])
        
        const projectsData = projectsRes.data.data as { projects: Project[] }
        setProjects(projectsData?.projects || [])
        if (projectsData?.projects?.length > 0) {
          const firstProject = projectsData.projects[0].name
          setSelectedProject(firstProject)
          setActiveProject(firstProject)
        }
        
        const modelsData = modelsRes.data.data as { models: LLMModel[] }
        setModels(modelsData?.models || [])
        if (modelsData?.models?.length > 0) {
          setSelectedModel(modelsData.models[0].id)
        }
      } catch (error) {
        console.error('Failed to fetch data:', error)
      } finally {
        setProjectsLoading(false)
      }
    }
    fetchData()
  }, [setActiveProject])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Update active project when selection changes
  const handleProjectChange = (projectName: string) => {
    setSelectedProject(projectName)
    setActiveProject(projectName)
  }

  const handleNewConversation = () => {
    if (selectedProject) {
      createConversation(selectedProject)
    }
  }

  const sendMessage = async () => {
    if (!input.trim() || isLoading || !selectedProject || !activeConversationId) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date().toISOString(),
    }

    addMessage(selectedProject, activeConversationId, userMessage)
    setInput('')
    setIsLoading(true)

    try {
      const response = await api.queryCodebase(input, selectedProject, selectedModel)
      const data = response.data.data as { answer: string; sources?: { file: string; snippet: string }[]; model_used?: string }

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data?.answer || 'No answer received',
        sources: data?.sources,
        timestamp: new Date().toISOString(),
        modelUsed: data?.model_used || selectedModel,
      }

      addMessage(selectedProject, activeConversationId, assistantMessage)
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your request. Please try again.',
        timestamp: new Date().toISOString(),
      }
      addMessage(selectedProject, activeConversationId, errorMessage)
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
    <div className="flex h-[calc(100vh-200px)] glass rounded-2xl overflow-hidden">
      {/* Sidebar */}
      <div className="w-64 flex-shrink-0">
        <ChatSidebar 
          projects={projects}
          selectedProject={selectedProject}
          onProjectSelect={handleProjectChange}
        />
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header with Project & Model Selectors */}
        <div className="px-4 py-3 border-b border-carbon-700 flex items-center justify-between bg-carbon-900/50">
          <div className="flex items-center gap-4">
            {/* Project Selector */}
            <div className="flex items-center gap-2">
              <Database className="w-4 h-4 text-accent-cyan" />
              <div className="relative">
                <select
                  value={selectedProject}
                  onChange={(e) => handleProjectChange(e.target.value)}
                  className="appearance-none bg-carbon-800 border border-carbon-700 rounded-lg px-3 py-1.5 pr-8 text-sm text-white focus:outline-none focus:border-accent-cyan cursor-pointer font-medium"
                >
                  {projects.length === 0 ? (
                    <option value="">No indexed projects</option>
                  ) : (
                    projects.map((project) => (
                      <option key={project.name} value={project.name}>
                        {project.name}
                      </option>
                    ))
                  )}
                </select>
                <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-carbon-400 pointer-events-none" />
              </div>
            </div>

            {/* Conversation Title */}
            <div className="flex items-center gap-2 text-carbon-400">
              <span className="text-carbon-600">/</span>
              <span className="text-sm truncate max-w-[200px]">
                {activeConversation?.title || 'New Chat'}
              </span>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            {/* New Chat Button */}
            <button
              onClick={handleNewConversation}
              disabled={!selectedProject}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-carbon-300 hover:text-white hover:bg-carbon-800 rounded-lg transition-colors disabled:opacity-50"
            >
              <Plus className="w-4 h-4" />
              New Chat
            </button>

            {/* Model Selector */}
            <div className="flex items-center gap-2">
              <Cpu className="w-4 h-4 text-carbon-400" />
              <div className="relative">
                <select
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  className="appearance-none bg-carbon-800 border border-carbon-700 rounded-lg px-3 py-1.5 pr-8 text-sm text-white focus:outline-none focus:border-accent-violet cursor-pointer"
                >
                  {models.map((model) => (
                    <option key={model.id} value={model.id} title={model.description}>
                      {model.name}
                    </option>
                  ))}
                </select>
                <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-carbon-400 pointer-events-none" />
              </div>
            </div>
          </div>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {projectsLoading ? (
            <div className="flex items-center justify-center h-full">
              <Loader2 className="w-8 h-8 text-accent-cyan animate-spin" />
            </div>
          ) : !selectedProject ? (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex flex-col items-center justify-center h-full text-center"
            >
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-accent-cyan/20 to-accent-violet/20 flex items-center justify-center mb-4 border border-accent-cyan/30">
                <Sparkles className="w-8 h-8 text-accent-cyan" />
              </div>
              <h3 className="text-xl font-display font-bold mb-2">No projects indexed</h3>
              <p className="text-carbon-400 max-w-md">
                Index a codebase from the Dashboard to start asking questions.
              </p>
            </motion.div>
          ) : messages.length === 0 ? (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex flex-col items-center justify-center h-full text-center"
            >
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-accent-cyan/20 to-accent-violet/20 flex items-center justify-center mb-4 border border-accent-cyan/30">
                <Sparkles className="w-8 h-8 text-accent-cyan" />
              </div>
              <h3 className="text-xl font-display font-bold mb-2">Ask about {selectedProject}</h3>
              <p className="text-carbon-400 max-w-md">
                I can explain code, describe architecture, show dependencies, and help you understand how everything connects.
              </p>
            </motion.div>
          ) : (
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
                  
                  <div className={`max-w-[85%] ${message.role === 'user' ? 'order-first' : ''}`}>
                    <div
                      className={`rounded-2xl ${
                        message.role === 'user'
                          ? 'bg-gradient-to-r from-accent-cyan to-accent-violet text-white px-5 py-3'
                          : 'bg-carbon-900/80 border border-carbon-700/50 px-6 py-5'
                      }`}
                    >
                      {message.role === 'assistant' ? (
                        <div className="prose prose-invert prose-sm max-w-none">
                          <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                            components={{
                              h1: ({ children }) => (
                                <h1 className="text-xl font-bold text-white mt-6 mb-3 pb-2 border-b border-carbon-700 first:mt-0">
                                  {children}
                                </h1>
                              ),
                              h2: ({ children }) => (
                                <h2 className="text-lg font-semibold text-white mt-5 mb-2 flex items-center gap-2 first:mt-0">
                                  <span className="w-1 h-5 bg-accent-cyan rounded-full"></span>
                                  {children}
                                </h2>
                              ),
                              h3: ({ children }) => (
                                <h3 className="text-base font-semibold text-carbon-200 mt-4 mb-2 first:mt-0">
                                  {children}
                                </h3>
                              ),
                              h4: ({ children }) => (
                                <h4 className="text-sm font-semibold text-carbon-300 mt-3 mb-1.5 first:mt-0">
                                  {children}
                                </h4>
                              ),
                              p: ({ children }) => (
                                <p className="text-carbon-200 leading-relaxed mb-4 last:mb-0">
                                  {children}
                                </p>
                              ),
                              ul: ({ children }) => (
                                <ul className="space-y-2 mb-4 last:mb-0 ml-1">
                                  {children}
                                </ul>
                              ),
                              ol: ({ children }) => (
                                <ol className="space-y-2 mb-4 last:mb-0 ml-1 list-decimal list-inside">
                                  {children}
                                </ol>
                              ),
                              li: ({ children }) => (
                                <li className="text-carbon-200 leading-relaxed flex items-start gap-2">
                                  <ChevronRight className="w-4 h-4 text-accent-cyan mt-0.5 flex-shrink-0" />
                                  <span className="flex-1">{children}</span>
                                </li>
                              ),
                              code({ className, children, ...props }) {
                                const match = /language-(\w+)/.exec(className || '')
                                const isInline = !match && !String(children).includes('\n')
                                
                                if (isInline) {
                                  return (
                                    <code 
                                      className="bg-carbon-800 px-1.5 py-0.5 rounded text-accent-cyan font-mono text-[13px] border border-carbon-700" 
                                      {...props}
                                    >
                                      {children}
                                    </code>
                                  )
                                }
                                
                                const language = match ? match[1] : 'text'
                                return (
                                  <div className="my-4 rounded-lg overflow-hidden border border-carbon-700 bg-carbon-950">
                                    <div className="flex items-center justify-between px-4 py-2 bg-carbon-800/50 border-b border-carbon-700">
                                      <span className="text-xs text-carbon-400 font-mono">{language}</span>
                                    </div>
                                    <SyntaxHighlighter
                                      style={oneDark}
                                      language={language}
                                      PreTag="div"
                                      customStyle={{
                                        margin: 0,
                                        padding: '1rem',
                                        background: 'transparent',
                                        fontSize: '13px',
                                      }}
                                    >
                                      {String(children).replace(/\n$/, '')}
                                    </SyntaxHighlighter>
                                  </div>
                                )
                              },
                              a: ({ href, children }) => (
                                <a 
                                  href={href} 
                                  className="text-accent-cyan hover:text-accent-cyan/80 underline underline-offset-2 transition-colors"
                                  target="_blank"
                                  rel="noopener noreferrer"
                                >
                                  {children}
                                </a>
                              ),
                              strong: ({ children }) => (
                                <strong className="font-semibold text-white">{children}</strong>
                              ),
                              em: ({ children }) => (
                                <em className="italic text-carbon-300">{children}</em>
                              ),
                              blockquote: ({ children }) => (
                                <blockquote className="border-l-2 border-accent-violet pl-4 my-4 text-carbon-300 italic">
                                  {children}
                                </blockquote>
                              ),
                              hr: () => (
                                <hr className="my-6 border-carbon-700" />
                              ),
                              table: ({ children }) => (
                                <div className="my-4 overflow-x-auto rounded-lg border border-carbon-700">
                                  <table className="w-full text-sm">
                                    {children}
                                  </table>
                                </div>
                              ),
                              thead: ({ children }) => (
                                <thead className="bg-carbon-800/50 border-b border-carbon-700">
                                  {children}
                                </thead>
                              ),
                              th: ({ children }) => (
                                <th className="px-4 py-2 text-left font-semibold text-carbon-200">
                                  {children}
                                </th>
                              ),
                              td: ({ children }) => (
                                <td className="px-4 py-2 text-carbon-300 border-t border-carbon-700/50">
                                  {children}
                                </td>
                              ),
                            }}
                          >
                            {message.content}
                          </ReactMarkdown>
                        </div>
                      ) : (
                        <p className="leading-relaxed">{message.content}</p>
                      )}
                    </div>
                    
                    {/* Sources */}
                    {message.sources && message.sources.length > 0 && (
                      <div className="mt-3 p-3 rounded-xl bg-carbon-800/30 border border-carbon-700/30">
                        <div className="flex items-center gap-2 mb-2">
                          <FileCode className="w-3.5 h-3.5 text-carbon-400" />
                          <span className="text-xs font-medium text-carbon-400 uppercase tracking-wide">
                            Referenced Files
                          </span>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {message.sources.map((source, idx) => (
                            <div 
                              key={idx} 
                              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-carbon-800/50 border border-carbon-700/50 hover:border-accent-cyan/30 transition-colors cursor-default"
                            >
                              <span className="w-1.5 h-1.5 rounded-full bg-accent-cyan"></span>
                              <span className="text-xs font-mono text-carbon-300">{source.file.split('/').pop()}</span>
                            </div>
                          ))}
                        </div>
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
          )}

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
          <div className="flex gap-3">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={selectedProject ? `Ask about ${selectedProject}...` : "Select a project first..."}
              rows={1}
              disabled={!selectedProject || !activeConversationId}
              className="flex-1 bg-carbon-900 border border-carbon-700 rounded-xl px-4 py-3 text-white placeholder-carbon-500 focus:outline-none focus:border-accent-cyan resize-none disabled:opacity-50 disabled:cursor-not-allowed"
            />
            <button
              onClick={sendMessage}
              disabled={!input.trim() || isLoading || !selectedProject || !activeConversationId}
              className="px-4 py-3 rounded-xl bg-gradient-to-r from-accent-cyan to-accent-violet text-white font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:opacity-90 transition-opacity"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
