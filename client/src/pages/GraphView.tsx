import { useState } from 'react'
import { motion } from 'framer-motion'
import { useMutation } from '@tanstack/react-query'
import { 
  GitGraph, 
  Search, 
  Loader2,
  Download,
  FileCode,
  Network
} from 'lucide-react'
import MermaidDiagram from '@/components/MermaidDiagram'
import ReactMarkdown from 'react-markdown'
import { api } from '@/lib/api'

export default function GraphView() {
  const [path, setPath] = useState('')
  const [graphType, setGraphType] = useState<'full' | 'dependencies' | 'integration' | 'terraform'>('full')

  const graphMutation = useMutation({
    mutationFn: (codePath: string) => api.generateGraph(codePath, graphType, 'json'),
  })

  const mermaidMutation = useMutation({
    mutationFn: (codePath: string) => api.exportMermaid(codePath, graphType),
  })

  const summaryMutation = useMutation({
    mutationFn: (codePath: string) => api.getGraphSummary(codePath, graphType),
  })

  const handleGenerate = () => {
    if (path.trim()) {
      graphMutation.mutate(path)
      mermaidMutation.mutate(path)
      summaryMutation.mutate(path)
    }
  }

  const graphData = graphMutation.data?.data?.data
  const mermaidCode = mermaidMutation.data?.data?.data?.mermaid as string
  const summary = summaryMutation.data?.data?.data?.summary as string

  return (
    <div className="p-8 max-w-7xl mx-auto">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="font-display text-3xl font-bold mb-2">
          Dependency <span className="gradient-text">Graph</span>
        </h1>
        <p className="text-carbon-400">
          Visualize how components, modules, and infrastructure connect
        </p>
      </motion.div>

      {/* Controls */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="glass rounded-2xl p-6 mb-6"
      >
        <div className="flex flex-col lg:flex-row gap-4">
          <input
            type="text"
            value={path}
            onChange={(e) => setPath(e.target.value)}
            placeholder="/path/to/your/codebase"
            className="flex-1 bg-carbon-900 border border-carbon-700 rounded-xl px-4 py-3 text-white placeholder-carbon-500 focus:outline-none focus:border-accent-cyan font-mono text-sm"
          />
          
          <div className="flex gap-2">
            {(['full', 'dependencies', 'integration', 'terraform'] as const).map((type) => (
              <button
                key={type}
                onClick={() => setGraphType(type)}
                className={`px-4 py-2 rounded-xl text-sm font-medium capitalize transition-all ${
                  graphType === type
                    ? 'bg-accent-amber/20 text-accent-amber border border-accent-amber/30'
                    : 'bg-carbon-800 text-carbon-400 hover:text-white'
                }`}
              >
                {type}
              </button>
            ))}
          </div>
          
          <button
            onClick={handleGenerate}
            disabled={!path.trim() || graphMutation.isPending}
            className="px-6 py-3 rounded-xl bg-gradient-to-r from-accent-amber to-orange-600 text-white font-medium disabled:opacity-50 hover:opacity-90 transition-opacity flex items-center gap-2"
          >
            {graphMutation.isPending ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <GitGraph className="w-4 h-4" />
            )}
            Generate
          </button>
        </div>
      </motion.div>

      {/* Results */}
      {graphMutation.isSuccess && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Graph Visualization */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="lg:col-span-2"
          >
            <div className="glass rounded-2xl p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <Network className="w-5 h-5 text-accent-amber" />
                  <h2 className="font-semibold">Graph Visualization</h2>
                </div>
                {mermaidCode && (
                  <button
                    onClick={() => {
                      const blob = new Blob([mermaidCode], { type: 'text/plain' })
                      const url = URL.createObjectURL(blob)
                      const a = document.createElement('a')
                      a.href = url
                      a.download = 'graph.mmd'
                      a.click()
                    }}
                    className="flex items-center gap-2 px-3 py-1.5 text-sm rounded-lg bg-carbon-800 hover:bg-carbon-700 transition-colors"
                  >
                    <Download className="w-4 h-4" />
                    Export
                  </button>
                )}
              </div>
              
              {mermaidMutation.isPending ? (
                <div className="flex items-center justify-center py-20">
                  <Loader2 className="w-8 h-8 text-accent-amber animate-spin" />
                </div>
              ) : mermaidCode ? (
                <MermaidDiagram chart={mermaidCode} className="min-h-[400px]" />
              ) : (
                <div className="text-center py-20 text-carbon-500">
                  <Network className="w-12 h-12 mx-auto mb-3 opacity-30" />
                  <p>No graph to display</p>
                </div>
              )}
            </div>
          </motion.div>

          {/* Stats & Summary */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3 }}
            className="space-y-6"
          >
            {/* Stats */}
            {graphData && (
              <div className="glass rounded-2xl p-6">
                <h3 className="font-semibold mb-4">Graph Statistics</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-carbon-900 rounded-xl p-4 text-center">
                    <div className="text-3xl font-bold text-accent-cyan">{graphData.stats?.total_nodes || 0}</div>
                    <div className="text-sm text-carbon-400">Nodes</div>
                  </div>
                  <div className="bg-carbon-900 rounded-xl p-4 text-center">
                    <div className="text-3xl font-bold text-accent-violet">{graphData.stats?.total_edges || 0}</div>
                    <div className="text-sm text-carbon-400">Edges</div>
                  </div>
                </div>
              </div>
            )}

            {/* Node Types */}
            {graphData?.nodes && graphData.nodes.length > 0 && (
              <div className="glass rounded-2xl p-6">
                <h3 className="font-semibold mb-4">Node Types</h3>
                <div className="space-y-2">
                  {Object.entries(
                    graphData.nodes.reduce((acc: Record<string, number>, node) => {
                      acc[node.type] = (acc[node.type] || 0) + 1
                      return acc
                    }, {})
                  ).map(([type, count]) => (
                    <div key={type} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <FileCode className="w-4 h-4 text-carbon-400" />
                        <span className="text-sm capitalize">{type}</span>
                      </div>
                      <span className="text-sm text-carbon-400">{count as number}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Summary */}
            {summary && (
              <div className="glass rounded-2xl p-6 max-h-[400px] overflow-y-auto">
                <h3 className="font-semibold mb-4">Analysis Summary</h3>
                <div className="prose prose-invert prose-sm max-w-none">
                  <ReactMarkdown>{summary}</ReactMarkdown>
                </div>
              </div>
            )}
          </motion.div>
        </div>
      )}

      {/* Loading State */}
      {graphMutation.isPending && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="glass rounded-2xl p-12 text-center"
        >
          <Loader2 className="w-12 h-12 text-accent-amber mx-auto mb-4 animate-spin" />
          <h3 className="text-lg font-medium mb-2">Generating Graph</h3>
          <p className="text-carbon-400">Analyzing dependencies and relationships...</p>
        </motion.div>
      )}
    </div>
  )
}

