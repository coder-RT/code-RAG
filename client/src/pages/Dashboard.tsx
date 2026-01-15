import { useState } from 'react'
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
  GitGraph
} from 'lucide-react'
import { useMutation } from '@tanstack/react-query'
import { api } from '@/lib/api'
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
  const [isIndexed, setIsIndexed] = useState(false)

  const indexMutation = useMutation({
    mutationFn: (path: string) => api.indexCodebase(path),
    onSuccess: () => {
      setIsIndexed(true)
    },
  })

  const handleIndex = () => {
    if (codebasePath.trim()) {
      indexMutation.mutate(codebasePath)
    }
  }

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
            disabled={!codebasePath.trim() || indexMutation.isPending}
            className="px-6 py-3 rounded-xl bg-gradient-to-r from-accent-cyan to-accent-violet text-white font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:opacity-90 transition-opacity flex items-center gap-2"
          >
            {indexMutation.isPending ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Indexing...
              </>
            ) : (
              <>
                <Upload className="w-4 h-4" />
                Index
              </>
            )}
          </button>
        </div>

        {/* Status */}
        {indexMutation.isSuccess && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-4 p-3 rounded-lg bg-accent-emerald/10 border border-accent-emerald/30 flex items-center gap-3"
          >
            <CheckCircle2 className="w-5 h-5 text-accent-emerald" />
            <div>
              <p className="text-sm font-medium text-accent-emerald">Codebase indexed successfully!</p>
              <p className="text-xs text-carbon-400">
                {(indexMutation.data?.data?.data as { files_indexed?: number })?.files_indexed || 0} files indexed, 
                {(indexMutation.data?.data?.data as { chunks_created?: number })?.chunks_created || 0} chunks created
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

