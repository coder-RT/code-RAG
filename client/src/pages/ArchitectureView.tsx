import { useState } from 'react'
import { motion } from 'framer-motion'
import { useMutation } from '@tanstack/react-query'
import { 
  Layers, 
  Box, 
  GitBranch, 
  Search, 
  Loader2,
  Sparkles
} from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { api } from '@/lib/api'

interface Module {
  name: string
  path: string
  type: string
  files: string[]
  description: string
}

interface Layer {
  name: string
  paths: string[]
  description: string
}

export default function ArchitectureView() {
  const [path, setPath] = useState('')
  const [activeTab, setActiveTab] = useState<'modules' | 'layers' | 'patterns'>('modules')

  const analyzeMutation = useMutation({
    mutationFn: (codePath: string) => api.analyzeArchitecture(codePath, 'full'),
  })

  const handleAnalyze = () => {
    if (path.trim()) {
      analyzeMutation.mutate(path)
    }
  }

  const modules = analyzeMutation.data?.data?.data?.modules as Module[] || []
  const layers = analyzeMutation.data?.data?.data?.layers as Layer[] || []
  const patterns = analyzeMutation.data?.data?.data?.patterns as { analysis: string }[] || []
  const summary = analyzeMutation.data?.data?.data?.summary as string

  return (
    <div className="p-8 max-w-7xl mx-auto">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="font-display text-3xl font-bold mb-2">
          Architecture <span className="gradient-text">Analysis</span>
        </h1>
        <p className="text-carbon-400">
          Discover modules, layers, and design patterns in your codebase
        </p>
      </motion.div>

      {/* Path Input */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="glass rounded-2xl p-6 mb-6"
      >
        <div className="flex gap-3">
          <input
            type="text"
            value={path}
            onChange={(e) => setPath(e.target.value)}
            placeholder="/path/to/your/codebase"
            className="flex-1 bg-carbon-900 border border-carbon-700 rounded-xl px-4 py-3 text-white placeholder-carbon-500 focus:outline-none focus:border-accent-cyan font-mono text-sm"
          />
          <button
            onClick={handleAnalyze}
            disabled={!path.trim() || analyzeMutation.isPending}
            className="px-6 py-3 rounded-xl bg-gradient-to-r from-accent-violet to-purple-600 text-white font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:opacity-90 transition-opacity flex items-center gap-2"
          >
            {analyzeMutation.isPending ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <Search className="w-4 h-4" />
                Analyze
              </>
            )}
          </button>
        </div>
      </motion.div>

      {/* Summary Card */}
      {summary && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="glass rounded-2xl p-6 mb-6"
        >
          <div className="flex items-center gap-2 mb-4">
            <Sparkles className="w-5 h-5 text-accent-amber" />
            <h2 className="font-semibold">Architecture Summary</h2>
          </div>
          <p className="text-carbon-300 leading-relaxed whitespace-pre-wrap">{summary}</p>
        </motion.div>
      )}

      {/* Tabs */}
      {analyzeMutation.isSuccess && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
        >
          <div className="flex gap-2 mb-6">
            {(['modules', 'layers', 'patterns'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-2 rounded-xl text-sm font-medium capitalize transition-all ${
                  activeTab === tab
                    ? 'bg-gradient-to-r from-accent-violet/20 to-purple-600/20 text-white border border-accent-violet/30'
                    : 'bg-carbon-900 text-carbon-400 hover:text-white border border-transparent'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>

          {/* Modules Tab */}
          {activeTab === 'modules' && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {modules.map((module, index) => (
                <motion.div
                  key={module.path}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="glass rounded-xl p-5"
                >
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-10 h-10 rounded-lg bg-accent-violet/20 flex items-center justify-center">
                      <Box className="w-5 h-5 text-accent-violet" />
                    </div>
                    <div>
                      <h3 className="font-medium">{module.name}</h3>
                      <p className="text-xs text-carbon-500 font-mono">{module.path}</p>
                    </div>
                  </div>
                  
                  <div className="mb-3">
                    <span className="inline-block px-2 py-0.5 text-xs rounded-full bg-carbon-800 text-carbon-300">
                      {module.type}
                    </span>
                  </div>
                  
                  <p className="text-sm text-carbon-400 mb-3">{module.description}</p>
                  
                  {module.files.length > 0 && (
                    <div className="pt-3 border-t border-carbon-800">
                      <p className="text-xs text-carbon-500 mb-2">Files ({module.files.length})</p>
                      <div className="flex flex-wrap gap-1">
                        {module.files.slice(0, 5).map((file) => (
                          <span key={file} className="text-xs px-2 py-0.5 rounded bg-carbon-800 text-carbon-400 font-mono">
                            {file}
                          </span>
                        ))}
                        {module.files.length > 5 && (
                          <span className="text-xs px-2 py-0.5 text-carbon-500">
                            +{module.files.length - 5} more
                          </span>
                        )}
                      </div>
                    </div>
                  )}
                </motion.div>
              ))}
              
              {modules.length === 0 && (
                <div className="col-span-full text-center py-12 text-carbon-500">
                  <Box className="w-12 h-12 mx-auto mb-3 opacity-30" />
                  <p>No modules detected</p>
                </div>
              )}
            </div>
          )}

          {/* Layers Tab */}
          {activeTab === 'layers' && (
            <div className="space-y-4">
              {layers.map((layer, index) => (
                <motion.div
                  key={layer.name}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="glass rounded-xl p-5"
                >
                  <div className="flex items-center gap-3 mb-3">
                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                      layer.name === 'presentation' ? 'bg-accent-cyan/20' :
                      layer.name === 'business' ? 'bg-accent-violet/20' :
                      layer.name === 'data' ? 'bg-accent-emerald/20' :
                      layer.name === 'infrastructure' ? 'bg-accent-amber/20' :
                      'bg-carbon-800'
                    }`}>
                      <Layers className={`w-5 h-5 ${
                        layer.name === 'presentation' ? 'text-accent-cyan' :
                        layer.name === 'business' ? 'text-accent-violet' :
                        layer.name === 'data' ? 'text-accent-emerald' :
                        layer.name === 'infrastructure' ? 'text-accent-amber' :
                        'text-carbon-400'
                      }`} />
                    </div>
                    <div>
                      <h3 className="font-medium capitalize">{layer.name} Layer</h3>
                      <p className="text-sm text-carbon-400">{layer.description}</p>
                    </div>
                  </div>
                  
                  <div className="flex flex-wrap gap-2">
                    {layer.paths.map((p) => (
                      <span key={p} className="text-sm px-3 py-1 rounded-lg bg-carbon-800 text-carbon-300 font-mono">
                        {p}
                      </span>
                    ))}
                  </div>
                </motion.div>
              ))}
              
              {layers.length === 0 && (
                <div className="text-center py-12 text-carbon-500">
                  <Layers className="w-12 h-12 mx-auto mb-3 opacity-30" />
                  <p>No architectural layers detected</p>
                </div>
              )}
            </div>
          )}

          {/* Patterns Tab */}
          {activeTab === 'patterns' && (
            <div className="glass rounded-2xl p-6">
              <div className="flex items-center gap-2 mb-4">
                <GitBranch className="w-5 h-5 text-accent-emerald" />
                <h2 className="font-semibold">Detected Patterns</h2>
              </div>
              
              {patterns.length > 0 ? (
                <div className="prose prose-invert max-w-none">
                  {patterns.map((pattern, index) => (
                    <ReactMarkdown key={index}>
                      {pattern.analysis}
                    </ReactMarkdown>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 text-carbon-500">
                  <GitBranch className="w-12 h-12 mx-auto mb-3 opacity-30" />
                  <p>No patterns analysis available</p>
                </div>
              )}
            </div>
          )}
        </motion.div>
      )}

      {/* Loading State */}
      {analyzeMutation.isPending && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="glass rounded-2xl p-12 text-center"
        >
          <Loader2 className="w-12 h-12 text-accent-violet mx-auto mb-4 animate-spin" />
          <h3 className="text-lg font-medium mb-2">Analyzing Architecture</h3>
          <p className="text-carbon-400">This may take a moment for large codebases...</p>
        </motion.div>
      )}
    </div>
  )
}

