import { useState } from 'react'
import { motion } from 'framer-motion'
import { useMutation } from '@tanstack/react-query'
import { 
  Cloud, 
  Server, 
  Database, 
  Shield, 
  Search, 
  Loader2,
  Box,
  Link,
  FileCode
} from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { api } from '@/lib/api'

interface Resource {
  type: string
  name: string
  file: string
}

interface Variable {
  name: string
  type: string
  default: string | null
  description: string | null
  file: string
}

interface TerraformModule {
  name: string
  source: string
  file: string
}

const getResourceIcon = (type: string) => {
  if (type.includes('vpc') || type.includes('network')) return Shield
  if (type.includes('db') || type.includes('rds') || type.includes('dynamodb')) return Database
  if (type.includes('s3') || type.includes('storage')) return Box
  if (type.includes('lambda') || type.includes('function')) return FileCode
  return Server
}

const getResourceColor = (type: string) => {
  if (type.includes('vpc') || type.includes('network')) return 'text-accent-violet bg-accent-violet/20'
  if (type.includes('db') || type.includes('rds') || type.includes('dynamodb')) return 'text-accent-emerald bg-accent-emerald/20'
  if (type.includes('s3') || type.includes('storage')) return 'text-accent-amber bg-accent-amber/20'
  if (type.includes('lambda') || type.includes('function')) return 'text-accent-cyan bg-accent-cyan/20'
  return 'text-accent-rose bg-accent-rose/20'
}

export default function InfrastructureView() {
  const [path, setPath] = useState('')
  const [activeTab, setActiveTab] = useState<'resources' | 'modules' | 'variables' | 'explain'>('resources')

  const analyzeMutation = useMutation({
    mutationFn: (tfPath: string) => api.analyzeTerraform(tfPath),
  })

  const explainMutation = useMutation({
    mutationFn: (tfPath: string) => api.explainInfrastructure(tfPath),
  })

  const handleAnalyze = () => {
    if (path.trim()) {
      analyzeMutation.mutate(path)
    }
  }

  const handleExplain = () => {
    if (path.trim()) {
      explainMutation.mutate(path)
    }
  }

  const resources = analyzeMutation.data?.data?.data?.resources as Resource[] || []
  const modules = analyzeMutation.data?.data?.data?.modules as TerraformModule[] || []
  const variables = analyzeMutation.data?.data?.data?.variables as Variable[] || []
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
          Infrastructure <span className="gradient-text">Analysis</span>
        </h1>
        <p className="text-carbon-400">
          Understand your Terraform configuration and cloud resources
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
            placeholder="/path/to/terraform/files"
            className="flex-1 bg-carbon-900 border border-carbon-700 rounded-xl px-4 py-3 text-white placeholder-carbon-500 focus:outline-none focus:border-accent-cyan font-mono text-sm"
          />
          <button
            onClick={handleAnalyze}
            disabled={!path.trim() || analyzeMutation.isPending}
            className="px-6 py-3 rounded-xl bg-gradient-to-r from-accent-emerald to-green-600 text-white font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:opacity-90 transition-opacity flex items-center gap-2"
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
            <Cloud className="w-5 h-5 text-accent-emerald" />
            <h2 className="font-semibold">Infrastructure Summary</h2>
          </div>
          <pre className="text-carbon-300 whitespace-pre-wrap text-sm font-mono">{summary}</pre>
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
            {(['resources', 'modules', 'variables', 'explain'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => {
                  setActiveTab(tab)
                  if (tab === 'explain' && !explainMutation.data) {
                    handleExplain()
                  }
                }}
                className={`px-4 py-2 rounded-xl text-sm font-medium capitalize transition-all ${
                  activeTab === tab
                    ? 'bg-gradient-to-r from-accent-emerald/20 to-green-600/20 text-white border border-accent-emerald/30'
                    : 'bg-carbon-900 text-carbon-400 hover:text-white border border-transparent'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>

          {/* Resources Tab */}
          {activeTab === 'resources' && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {resources.map((resource, index) => {
                const Icon = getResourceIcon(resource.type)
                const colorClass = getResourceColor(resource.type)
                
                return (
                  <motion.div
                    key={`${resource.type}.${resource.name}`}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className="glass rounded-xl p-5"
                  >
                    <div className="flex items-center gap-3 mb-3">
                      <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${colorClass.split(' ')[1]}`}>
                        <Icon className={`w-5 h-5 ${colorClass.split(' ')[0]}`} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <h3 className="font-medium truncate">{resource.name}</h3>
                        <p className="text-xs text-carbon-500 font-mono truncate">{resource.type}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-carbon-400">
                      <FileCode className="w-3 h-3" />
                      <span className="font-mono">{resource.file}</span>
                    </div>
                  </motion.div>
                )
              })}
              
              {resources.length === 0 && (
                <div className="col-span-full text-center py-12 text-carbon-500">
                  <Server className="w-12 h-12 mx-auto mb-3 opacity-30" />
                  <p>No Terraform resources found</p>
                </div>
              )}
            </div>
          )}

          {/* Modules Tab */}
          {activeTab === 'modules' && (
            <div className="space-y-4">
              {modules.map((module, index) => (
                <motion.div
                  key={module.name}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="glass rounded-xl p-5"
                >
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-10 h-10 rounded-lg bg-accent-violet/20 flex items-center justify-center">
                      <Box className="w-5 h-5 text-accent-violet" />
                    </div>
                    <div>
                      <h3 className="font-medium">{module.name}</h3>
                      <p className="text-xs text-carbon-500 font-mono">{module.file}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2 text-sm text-carbon-400">
                    <Link className="w-4 h-4" />
                    <span className="font-mono">{module.source}</span>
                  </div>
                </motion.div>
              ))}
              
              {modules.length === 0 && (
                <div className="text-center py-12 text-carbon-500">
                  <Box className="w-12 h-12 mx-auto mb-3 opacity-30" />
                  <p>No Terraform modules found</p>
                </div>
              )}
            </div>
          )}

          {/* Variables Tab */}
          {activeTab === 'variables' && (
            <div className="glass rounded-2xl overflow-hidden">
              <table className="w-full">
                <thead className="bg-carbon-900 border-b border-carbon-700">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-carbon-400 uppercase tracking-wider">Variable</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-carbon-400 uppercase tracking-wider">Type</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-carbon-400 uppercase tracking-wider">Default</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-carbon-400 uppercase tracking-wider">Description</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-carbon-800">
                  {variables.map((variable) => (
                    <tr key={variable.name} className="hover:bg-carbon-900/50">
                      <td className="px-6 py-4">
                        <span className="font-mono text-accent-cyan">{variable.name}</span>
                      </td>
                      <td className="px-6 py-4">
                        <span className="text-sm text-carbon-400">{variable.type}</span>
                      </td>
                      <td className="px-6 py-4">
                        <span className="font-mono text-sm text-carbon-400">
                          {variable.default || '-'}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span className="text-sm text-carbon-400">
                          {variable.description || '-'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              
              {variables.length === 0 && (
                <div className="text-center py-12 text-carbon-500">
                  <p>No variables defined</p>
                </div>
              )}
            </div>
          )}

          {/* Explain Tab */}
          {activeTab === 'explain' && (
            <div className="glass rounded-2xl p-6">
              {explainMutation.isPending && (
                <div className="flex flex-col items-center justify-center py-12">
                  <Loader2 className="w-8 h-8 text-accent-emerald animate-spin mb-3" />
                  <p className="text-carbon-400">Generating explanation...</p>
                </div>
              )}
              
              {explainMutation.isSuccess && explainMutation.data?.data?.data?.explanation && (
                <div className="prose prose-invert max-w-none">
                  <ReactMarkdown
                    components={{
                      h1: ({ children }) => <h1 className="text-2xl font-bold mb-4 text-white">{children}</h1>,
                      h2: ({ children }) => <h2 className="text-xl font-semibold mb-3 text-white">{children}</h2>,
                      h3: ({ children }) => <h3 className="text-lg font-medium mb-2 text-carbon-200">{children}</h3>,
                      p: ({ children }) => <p className="text-carbon-300 mb-4 leading-relaxed">{children}</p>,
                      ul: ({ children }) => <ul className="list-disc list-inside space-y-1 text-carbon-300 mb-4">{children}</ul>,
                      li: ({ children }) => <li className="text-carbon-300">{children}</li>,
                      strong: ({ children }) => <strong className="text-white font-semibold">{children}</strong>,
                    }}
                  >
                    {explainMutation.data.data.data.explanation as string}
                  </ReactMarkdown>
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
          <Loader2 className="w-12 h-12 text-accent-emerald mx-auto mb-4 animate-spin" />
          <h3 className="text-lg font-medium mb-2">Analyzing Terraform</h3>
          <p className="text-carbon-400">Parsing configuration files...</p>
        </motion.div>
      )}
    </div>
  )
}

