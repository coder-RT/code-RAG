import { useEffect, useRef, useState } from 'react'
import mermaid from 'mermaid'
import { motion } from 'framer-motion'
import { Loader2, AlertCircle } from 'lucide-react'

interface MermaidDiagramProps {
  chart: string
  className?: string
}

mermaid.initialize({
  startOnLoad: false,
  theme: 'dark',
  themeVariables: {
    primaryColor: '#22d3ee',
    primaryTextColor: '#fafafa',
    primaryBorderColor: '#3f3f46',
    lineColor: '#6b6e76',
    secondaryColor: '#8b5cf6',
    tertiaryColor: '#18181b',
    background: '#0a0a0b',
    mainBkg: '#18181b',
    nodeBorder: '#3f3f46',
    clusterBkg: '#18181b',
    titleColor: '#fafafa',
    edgeLabelBackground: '#18181b',
  },
  flowchart: {
    curve: 'basis',
    padding: 20,
  },
})

export default function MermaidDiagram({ chart, className = '' }: MermaidDiagramProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const renderChart = async () => {
      if (!containerRef.current || !chart) return

      setIsLoading(true)
      setError(null)

      try {
        const id = `mermaid-${Date.now()}`
        const { svg } = await mermaid.render(id, chart)
        containerRef.current.innerHTML = svg

        // Style the SVG
        const svgElement = containerRef.current.querySelector('svg')
        if (svgElement) {
          svgElement.style.maxWidth = '100%'
          svgElement.style.height = 'auto'
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to render diagram')
      } finally {
        setIsLoading(false)
      }
    }

    renderChart()
  }, [chart])

  if (error) {
    return (
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className={`flex flex-col items-center justify-center p-8 bg-carbon-900 rounded-xl border border-red-500/30 ${className}`}
      >
        <AlertCircle className="w-8 h-8 text-red-500 mb-3" />
        <p className="text-sm text-red-400">Failed to render diagram</p>
        <p className="text-xs text-carbon-500 mt-1">{error}</p>
      </motion.div>
    )
  }

  return (
    <div className={`relative ${className}`}>
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-carbon-900 rounded-xl">
          <Loader2 className="w-8 h-8 text-accent-cyan animate-spin" />
        </div>
      )}
      <motion.div
        ref={containerRef}
        initial={{ opacity: 0 }}
        animate={{ opacity: isLoading ? 0 : 1 }}
        transition={{ duration: 0.3 }}
        className="overflow-x-auto p-4 bg-carbon-900 rounded-xl border border-carbon-700"
      />
    </div>
  )
}

