import { useState, useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import { 
  FolderOpen, 
  Upload, 
  CheckCircle2, 
  AlertCircle,
  Loader2,
  Code2,
  Layers,
  Cloud,
  GitGraph,
  Zap,
  Cpu
} from 'lucide-react'
import { useMutation } from '@tanstack/react-query'
import { api, IndexOptions, TaskStatusResponse } from '@/lib/api'
import ChatInterface from '@/components/ChatInterface'

const features = [
  {
    icon: Code2,
    title: 'Code Explanation',
    description: 'Understand what each file and function does',
    color: 'from-accent-cyan to-cyan-600',
  },
  {
    icon: Layers,
    title: 'Architecture Analysis',
    description: 'Discover modules, layers, and patterns',
    color: 'from-accent-violet to-purple-600',
  },
  {
    icon: Cloud,
    title: 'Infrastructure Mapping',
    description: 'Connect Terraform to your application',
    color: 'from-accent-emerald to-green-600',
  },
  {
    icon: GitGraph,
    title: 'Dependency Graphs',
    description: 'Visualize how everything connects',
    color: 'from-accent-amber to-orange-600',
  },
]

export default function Dashboard() {
  const [codebasePath, setCodebasePath] = useState('')
  const [projectName, setProjectName] = useState('')
  const [isIndexed, setIsIndexed] = useState(false)
  const [asyncMode, setAsyncMode] = useState(false)
  const [embeddingProvider, setEmbeddingProvider] = useState<'openai' | 'huggingface'>('openai')
  const [taskId, setTaskId] = useState<string | null>(null)
  const [taskStatus, setTaskStatus] = useState<TaskStatusResponse | null>(null)
  const pollingRef = useRef<NodeJS.Timeout | null>(null)

  const indexMutation = useMutation({
    mutationFn: (options: IndexOptions) => api.indexCodebase(options),
    onSuccess: (response) => {
      const data = response.data?.data as Record<string, unknown>
      if (asyncMode && data?.task_id) {
        setTaskId(data.task_id as string)
      } else {
        setIsIndexed(true)
      }
    },
  })

  useEffect(() => {
    if (taskId && asyncMode) {
      pollingRef.current = setInterval(async () => {
        try {
          const response = await api.getTaskStatus(taskId)
          setTaskStatus(response.data)
          
          if (response.data.status === 'SUCCESS') {
            setIsIndexed(true)
            setTaskId(null)
            if (pollingRef.current) clearInterval(pollingRef.current)
          } else if (response.data.status === 'FAILURE') {
            setTaskId(null)
            if (pollingRef.current) clearInterval(pollingRef.current)
          }
        } catch {
          console.error('Failed to fetch task status')
        }
      }, 2000)
    }
    
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current)
    }
  }, [taskId, asyncMode])

  const handleIndex = () => {
    if (codebasePath.trim()) {
      setIsIndexed(false)
      setTaskStatus(null)
      indexMutation.mutate({
        path: codebasePath,
        projectName: projectName.trim() || undefined,
        asyncMode,
        embeddingProvider,
      })
    }
  }

  const isProcessing = indexMutation.isPending || !!taskId

  return (
    <div className="p-8 max-w-7xl mx-auto">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-12"
      >
        <h1 className="font-display text-4xl font-bold mb-3">
          Welcome to <span className="gradient-text">Code-RAG</span>
        </h1>
        <p className="text-carbon-400 text-lg">
          Your AI-powered assistant for understanding codebases
        </p>
      </motion.div>

      {/* Index Codebase Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="glass rounded-2xl p-6 mb-8"
      >
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-accent-cyan/20 to-accent-violet/20 flex items-center justify-center border border-accent-cyan/30">
            <FolderOpen className="w-5 h-5 text-accent-cyan" />
          </div>
          <div>
            <h2 className="font-semibold text-lg">Index a Codebase</h2>
            <p className="text-sm text-carbon-400">Point to a local directory to analyze</p>
          </div>
        </div>

        <div className="space-y-3 mb-4">
          <div className="flex gap-3">
            <input
              type="text"
              value={codebasePath}
              onChange={(e) => setCodebasePath(e.target.value)}
              placeholder="/path/to/your/codebase"
              className="flex-1 bg-carbon-900 border border-carbon-700 rounded-xl px-4 py-3 text-white placeholder-carbon-500 focus:outline-none focus:border-accent-cyan font-mono text-sm"
            />
            <button
              onClick={handleIndex}
              disabled={!codebasePath.trim() || isProcessing}
              className="px-6 py-3 rounded-xl bg-gradient-to-r from-accent-cyan to-accent-violet text-white font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:opacity-90 transition-opacity flex items-center gap-2"
            >
              {isProcessing ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  {taskId ? 'Processing...' : 'Indexing...'}
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4" />
                  Index
                </>
              )}
            </button>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-sm text-carbon-400 min-w-fit">Project Name:</span>
            <input
              type="text"
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
              placeholder="my_project (optional, defaults to folder name)"
              className="flex-1 bg-carbon-900 border border-carbon-700 rounded-lg px-3 py-2 text-white placeholder-carbon-500 focus:outline-none focus:border-accent-cyan text-sm"
            />
          </div>
        </div>

        {/* Options Row */}
        <div className="flex flex-wrap items-center gap-6">
          {/* Embedding Provider */}
          <div className="flex items-center gap-3">
            <span className="text-sm text-carbon-400">Embeddings:</span>
            <div className="flex rounded-lg overflow-hidden border border-carbon-700">
              <button
                onClick={() => setEmbeddingProvider('huggingface')}
                disabled={isProcessing}
                className={`px-3 py-1.5 text-sm flex items-center gap-1.5 transition-colors ${
                  embeddingProvider === 'huggingface'
                    ? 'bg-accent-violet/20 text-accent-violet border-r border-carbon-700'
                    : 'bg-carbon-900 text-carbon-400 hover:text-white border-r border-carbon-700'
                }`}
              >
                <Cpu className="w-3.5 h-3.5" />
                Local (Free)
              </button>
              <button
                onClick={() => setEmbeddingProvider('openai')}
                disabled={isProcessing}
                className={`px-3 py-1.5 text-sm flex items-center gap-1.5 transition-colors ${
                  embeddingProvider === 'openai'
                    ? 'bg-accent-emerald/20 text-accent-emerald'
                    : 'bg-carbon-900 text-carbon-400 hover:text-white'
                }`}
              >
                <Zap className="w-3.5 h-3.5" />
                OpenAI (Fast)
              </button>
            </div>
          </div>

          {/* Async Mode Toggle */}
          <label className="flex items-center gap-2 cursor-pointer">
            <div className="relative">
              <input
                type="checkbox"
                checked={asyncMode}
                onChange={(e) => setAsyncMode(e.target.checked)}
                disabled={isProcessing}
                className="sr-only peer"
              />
              <div className="w-9 h-5 bg-carbon-700 rounded-full peer peer-checked:bg-accent-cyan/50 transition-colors"></div>
              <div className="absolute left-0.5 top-0.5 w-4 h-4 bg-carbon-400 rounded-full peer-checked:translate-x-4 peer-checked:bg-accent-cyan transition-all"></div>
            </div>
            <span className="text-sm text-carbon-400">
              Async Mode
              <span className="text-xs text-carbon-500 ml-1">(requires Redis)</span>
            </span>
          </label>
        </div>

        {/* Async Progress */}
        {taskId && taskStatus && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-4 p-4 rounded-lg bg-accent-cyan/10 border border-accent-cyan/30"
          >
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <Loader2 className="w-4 h-4 text-accent-cyan animate-spin" />
                <span className="text-sm font-medium text-accent-cyan">
                  {taskStatus.stage === 'loading' && 'Loading files...'}
                  {taskStatus.stage === 'chunking' && 'Chunking files...'}
                  {taskStatus.stage === 'embedding' && 'Generating embeddings...'}
                  {taskStatus.stage === 'storing' && 'Storing in database...'}
                  {!['loading', 'chunking', 'embedding', 'storing'].includes(taskStatus.stage || '') && 'Processing...'}
                </span>
              </div>
              <span className="text-sm text-carbon-400">{taskStatus.progress || 0}%</span>
            </div>
            <div className="w-full bg-carbon-800 rounded-full h-2">
              <div 
                className="bg-gradient-to-r from-accent-cyan to-accent-violet h-2 rounded-full transition-all duration-300"
                style={{ width: `${taskStatus.progress || 0}%` }}
              />
            </div>
            {taskStatus.message && (
              <p className="text-xs text-carbon-400 mt-2">{taskStatus.message}</p>
            )}
          </motion.div>
        )}

        {/* Success Status */}
        {isIndexed && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-4 p-3 rounded-lg bg-accent-emerald/10 border border-accent-emerald/30 flex items-center gap-3"
          >
            <CheckCircle2 className="w-5 h-5 text-accent-emerald" />
            <div>
              <p className="text-sm font-medium text-accent-emerald">Codebase indexed successfully!</p>
              <p className="text-xs text-carbon-400">
                {taskStatus?.result 
                  ? `${(taskStatus.result as { files_indexed?: number }).files_indexed || 0} files indexed, ${(taskStatus.result as { chunks_created?: number }).chunks_created || 0} chunks created`
                  : indexMutation.data?.data?.data 
                    ? `${(indexMutation.data.data.data as { files_indexed?: number }).files_indexed || 0} files indexed, ${(indexMutation.data.data.data as { chunks_created?: number }).chunks_created || 0} chunks created`
                    : 'Indexing complete'
                }
              </p>
            </div>
          </motion.div>
        )}

        {indexMutation.isError && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-4 p-3 rounded-lg bg-accent-rose/10 border border-accent-rose/30 flex items-center gap-3"
          >
            <AlertCircle className="w-5 h-5 text-accent-rose" />
            <p className="text-sm text-accent-rose">Failed to index codebase. Please check the path and try again.</p>
          </motion.div>
        )}

        {taskStatus?.status === 'FAILURE' && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-4 p-3 rounded-lg bg-accent-rose/10 border border-accent-rose/30 flex items-center gap-3"
          >
            <AlertCircle className="w-5 h-5 text-accent-rose" />
            <p className="text-sm text-accent-rose">{taskStatus.message || 'Task failed. Please try again.'}</p>
          </motion.div>
        )}
      </motion.div>

      {/* Features Grid */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8"
      >
        {features.map((feature, index) => (
          <motion.div
            key={feature.title}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 + index * 0.05 }}
            className="glass rounded-xl p-5 hover:border-carbon-600 transition-colors cursor-pointer group"
          >
            <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${feature.color} flex items-center justify-center mb-3 group-hover:scale-110 transition-transform`}>
              <feature.icon className="w-5 h-5 text-white" />
            </div>
            <h3 className="font-medium mb-1">{feature.title}</h3>
            <p className="text-sm text-carbon-400">{feature.description}</p>
          </motion.div>
        ))}
      </motion.div>

      {/* Chat Interface */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        <h2 className="font-display text-2xl font-bold mb-4">Ask Questions</h2>
        <ChatInterface />
      </motion.div>
    </div>
  )
}

