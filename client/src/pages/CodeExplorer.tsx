import { useState } from 'react'
import { motion } from 'framer-motion'
import { useMutation } from '@tanstack/react-query'
import { 
  FolderTree, 
  FileCode, 
  Search, 
  Loader2,
  ChevronRight,
  ChevronDown,
  FileText
} from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { api } from '@/lib/api'

interface TreeNode {
  [key: string]: string | TreeNode
}

interface TreeViewProps {
  data: TreeNode
  path?: string
  onSelect: (path: string) => void
}

function TreeView({ data, path = '', onSelect }: TreeViewProps) {
  const [expanded, setExpanded] = useState<Record<string, boolean>>({})

  const toggleExpand = (key: string) => {
    setExpanded((prev) => ({ ...prev, [key]: !prev[key] }))
  }

  return (
    <div className="space-y-1">
      {Object.entries(data).map(([key, value]) => {
        const isDirectory = typeof value === 'object'
        const fullPath = path ? `${path}/${key.replace('/', '')}` : key.replace('/', '')
        const isExpanded = expanded[fullPath]

        return (
          <div key={key}>
            <button
              onClick={() => {
                if (isDirectory) {
                  toggleExpand(fullPath)
                } else {
                  onSelect(fullPath)
                }
              }}
              className="flex items-center gap-2 w-full px-2 py-1.5 rounded-lg hover:bg-carbon-800 text-left text-sm transition-colors group"
            >
              {isDirectory ? (
                <>
                  {isExpanded ? (
                    <ChevronDown className="w-4 h-4 text-carbon-500" />
                  ) : (
                    <ChevronRight className="w-4 h-4 text-carbon-500" />
                  )}
                  <FolderTree className="w-4 h-4 text-accent-amber" />
                </>
              ) : (
                <>
                  <span className="w-4" />
                  <FileCode className="w-4 h-4 text-accent-cyan" />
                </>
              )}
              <span className={`${isDirectory ? 'text-carbon-200' : 'text-carbon-400'} group-hover:text-white`}>
                {key}
              </span>
            </button>
            
            {isDirectory && isExpanded && (
              <div className="ml-4 border-l border-carbon-800 pl-2">
                <TreeView data={value as TreeNode} path={fullPath} onSelect={onSelect} />
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

export default function CodeExplorer() {
  const [basePath, setBasePath] = useState('')
  const [selectedFile, setSelectedFile] = useState<string | null>(null)
  const [detailLevel, setDetailLevel] = useState<'summary' | 'detailed' | 'verbose'>('summary')

  const structureMutation = useMutation({
    mutationFn: (path: string) => api.getStructure(path),
  })

  const explainMutation = useMutation({
    mutationFn: (path: string) => api.explainCode(path, detailLevel),
  })

  const handleLoadStructure = () => {
    if (basePath.trim()) {
      structureMutation.mutate(basePath)
    }
  }

  const handleSelectFile = (relativePath: string) => {
    const fullPath = `${basePath}/${relativePath}`
    setSelectedFile(fullPath)
    explainMutation.mutate(fullPath)
  }

  return (
    <div className="p-8 max-w-7xl mx-auto">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="font-display text-3xl font-bold mb-2">
          Code <span className="gradient-text">Explorer</span>
        </h1>
        <p className="text-carbon-400">
          Browse and understand your codebase file by file
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
            value={basePath}
            onChange={(e) => setBasePath(e.target.value)}
            placeholder="/path/to/your/codebase"
            className="flex-1 bg-carbon-900 border border-carbon-700 rounded-xl px-4 py-3 text-white placeholder-carbon-500 focus:outline-none focus:border-accent-cyan font-mono text-sm"
          />
          <button
            onClick={handleLoadStructure}
            disabled={!basePath.trim() || structureMutation.isPending}
            className="px-6 py-3 rounded-xl bg-gradient-to-r from-accent-cyan to-accent-violet text-white font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:opacity-90 transition-opacity flex items-center gap-2"
          >
            {structureMutation.isPending ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Search className="w-4 h-4" />
            )}
            Load
          </button>
        </div>
      </motion.div>

      {/* Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* File Tree */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          className="glass rounded-2xl p-4 h-[calc(100vh-320px)] overflow-y-auto"
        >
          <div className="flex items-center gap-2 mb-4 pb-3 border-b border-carbon-700">
            <FolderTree className="w-5 h-5 text-accent-amber" />
            <h2 className="font-medium">File Structure</h2>
          </div>

          {structureMutation.isPending && (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-6 h-6 text-accent-cyan animate-spin" />
            </div>
          )}

          {structureMutation.isSuccess && structureMutation.data?.data?.data?.structure && (
            <TreeView 
              data={structureMutation.data.data.data.structure as TreeNode} 
              onSelect={handleSelectFile}
            />
          )}

          {!structureMutation.isPending && !structureMutation.data && (
            <div className="text-center py-12 text-carbon-500">
              <FileText className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">Enter a path to explore</p>
            </div>
          )}
        </motion.div>

        {/* Explanation Panel */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3 }}
          className="lg:col-span-2 glass rounded-2xl p-6 h-[calc(100vh-320px)] overflow-y-auto"
        >
          <div className="flex items-center justify-between mb-4 pb-3 border-b border-carbon-700">
            <div className="flex items-center gap-2">
              <FileCode className="w-5 h-5 text-accent-cyan" />
              <h2 className="font-medium">
                {selectedFile ? selectedFile.split('/').pop() : 'Code Explanation'}
              </h2>
            </div>
            
            {/* Detail Level Selector */}
            <div className="flex gap-1">
              {(['summary', 'detailed', 'verbose'] as const).map((level) => (
                <button
                  key={level}
                  onClick={() => setDetailLevel(level)}
                  className={`px-3 py-1 text-xs rounded-lg capitalize transition-colors ${
                    detailLevel === level
                      ? 'bg-accent-cyan/20 text-accent-cyan border border-accent-cyan/30'
                      : 'bg-carbon-800 text-carbon-400 hover:text-white'
                  }`}
                >
                  {level}
                </button>
              ))}
            </div>
          </div>

          {explainMutation.isPending && (
            <div className="flex flex-col items-center justify-center py-12">
              <Loader2 className="w-8 h-8 text-accent-cyan animate-spin mb-3" />
              <p className="text-carbon-400">Analyzing code...</p>
            </div>
          )}

          {explainMutation.isSuccess && explainMutation.data?.data?.data?.explanation && (
            <div className="prose prose-invert max-w-none">
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
                        className="rounded-lg !bg-carbon-950"
                      >
                        {String(children).replace(/\n$/, '')}
                      </SyntaxHighlighter>
                    )
                  },
                  h1: ({ children }) => <h1 className="text-2xl font-bold mb-4 text-white">{children}</h1>,
                  h2: ({ children }) => <h2 className="text-xl font-semibold mb-3 text-white">{children}</h2>,
                  h3: ({ children }) => <h3 className="text-lg font-medium mb-2 text-carbon-200">{children}</h3>,
                  p: ({ children }) => <p className="text-carbon-300 mb-4 leading-relaxed">{children}</p>,
                  ul: ({ children }) => <ul className="list-disc list-inside space-y-1 text-carbon-300 mb-4">{children}</ul>,
                  ol: ({ children }) => <ol className="list-decimal list-inside space-y-1 text-carbon-300 mb-4">{children}</ol>,
                  li: ({ children }) => <li className="text-carbon-300">{children}</li>,
                  strong: ({ children }) => <strong className="text-white font-semibold">{children}</strong>,
                }}
              >
                {explainMutation.data.data.data.explanation as string}
              </ReactMarkdown>
            </div>
          )}

          {!explainMutation.isPending && !explainMutation.data && (
            <div className="flex flex-col items-center justify-center py-12 text-carbon-500">
              <FileCode className="w-12 h-12 mb-3 opacity-30" />
              <p>Select a file to see its explanation</p>
            </div>
          )}
        </motion.div>
      </div>
    </div>
  )
}

