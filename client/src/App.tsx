import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import CodeExplorer from './pages/CodeExplorer'
import ArchitectureView from './pages/ArchitectureView'
import InfrastructureView from './pages/InfrastructureView'
import GraphView from './pages/GraphView'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="explore" element={<CodeExplorer />} />
          <Route path="architecture" element={<ArchitectureView />} />
          <Route path="infrastructure" element={<InfrastructureView />} />
          <Route path="graph" element={<GraphView />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App

