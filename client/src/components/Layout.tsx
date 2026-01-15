import { Outlet, NavLink } from 'react-router-dom'
import { motion } from 'framer-motion'
import { 
  LayoutDashboard, 
  Code2, 
  Layers, 
  Cloud, 
  GitGraph,
  Sparkles
} from 'lucide-react'

const navItems = [
  { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/explore', icon: Code2, label: 'Code Explorer' },
  { path: '/architecture', icon: Layers, label: 'Architecture' },
  { path: '/infrastructure', icon: Cloud, label: 'Infrastructure' },
  { path: '/graph', icon: GitGraph, label: 'Graph View' },
]

export default function Layout() {
  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <motion.aside 
        initial={{ x: -80, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        transition={{ duration: 0.4 }}
        className="fixed left-0 top-0 h-screen w-64 bg-carbon-950 border-r border-carbon-800 flex flex-col z-50"
      >
        {/* Logo */}
        <div className="p-6 border-b border-carbon-800">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-accent-cyan to-accent-violet flex items-center justify-center">
              <Code2 className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="font-display text-xl font-bold gradient-text">Code-RAG</h1>
              <p className="text-xs text-carbon-400">Intelligent Analysis</p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 group ${
                  isActive
                    ? 'bg-gradient-to-r from-accent-cyan/20 to-accent-violet/20 text-white border border-accent-cyan/30'
                    : 'text-carbon-400 hover:text-white hover:bg-carbon-800'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <item.icon className={`w-5 h-5 ${isActive ? 'text-accent-cyan' : 'group-hover:text-accent-cyan'}`} />
                  {item.label}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-carbon-800">
          <div className="p-4 rounded-xl bg-gradient-to-br from-carbon-900 to-carbon-800 border border-carbon-700">
            <div className="flex items-center gap-2 mb-2">
              <Sparkles className="w-4 h-4 text-accent-amber" />
              <span className="text-sm font-medium">AI Powered</span>
            </div>
            <p className="text-xs text-carbon-400">
              Using RAG for intelligent code understanding
            </p>
          </div>
        </div>
      </motion.aside>

      {/* Main Content */}
      <main className="flex-1 ml-64">
        <div className="min-h-screen grid-pattern">
          <div className="radial-gradient min-h-screen">
            <Outlet />
          </div>
        </div>
      </main>
    </div>
  )
}

