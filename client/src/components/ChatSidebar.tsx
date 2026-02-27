import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  ChevronRight, 
  ChevronDown, 
  MessageSquare, 
  Plus, 
  Trash2, 
  FolderOpen,
  Pencil,
  Check,
  X
} from 'lucide-react'
import { useChatStore, Conversation } from '@/stores/chatStore'
import { Project } from '@/lib/api'

interface ChatSidebarProps {
  projects: Project[]
  selectedProject: string
  onProjectSelect: (projectName: string) => void
}

export default function ChatSidebar({ 
  projects, 
  selectedProject, 
  onProjectSelect 
}: ChatSidebarProps) {
  const [expandedProjects, setExpandedProjects] = useState<Set<string>>(new Set([selectedProject]))
  const [hoveredConv, setHoveredConv] = useState<string | null>(null)

  const { 
    projects: chatProjects,
    activeConversationId,
    setActiveProject,
    setActiveConversation,
    createConversation,
    deleteConversation,
    renameConversation,
    getProjectConversations,
  } = useChatStore()

  const toggleProject = (projectName: string) => {
    const newExpanded = new Set(expandedProjects)
    if (newExpanded.has(projectName)) {
      newExpanded.delete(projectName)
    } else {
      newExpanded.add(projectName)
    }
    setExpandedProjects(newExpanded)
  }

  const handleProjectClick = (projectName: string) => {
    onProjectSelect(projectName)
    setActiveProject(projectName)
    
    // Auto-expand when clicking
    const newExpanded = new Set(expandedProjects)
    newExpanded.add(projectName)
    setExpandedProjects(newExpanded)
  }

  const handleNewConversation = (projectName: string, e: React.MouseEvent) => {
    e.stopPropagation()
    createConversation(projectName)
  }

  const handleDeleteConversation = (projectName: string, convId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    if (confirm('Delete this conversation?')) {
      deleteConversation(projectName, convId)
    }
  }

  const handleRenameConversation = (projectName: string, convId: string, newTitle: string) => {
    if (newTitle.trim()) {
      renameConversation(projectName, convId, newTitle.trim())
    }
  }

  const handleConversationClick = (projectName: string, convId: string) => {
    if (selectedProject !== projectName) {
      onProjectSelect(projectName)
      setActiveProject(projectName)
    }
    setActiveConversation(convId)
  }

  return (
    <div className="h-full flex flex-col bg-carbon-950 border-r border-carbon-800">
      {/* Header */}
      <div className="p-4 border-b border-carbon-800">
        <h2 className="text-sm font-semibold text-carbon-300 uppercase tracking-wide">
          Conversations
        </h2>
      </div>

      {/* Projects & Conversations List */}
      <div className="flex-1 overflow-y-auto py-2">
        {projects.length === 0 ? (
          <div className="px-4 py-8 text-center text-carbon-500 text-sm">
            No indexed projects yet.
            <br />
            Index a codebase to start chatting.
          </div>
        ) : (
          <div className="space-y-1">
            {projects.map((project) => {
              const isExpanded = expandedProjects.has(project.name)
              const isActive = selectedProject === project.name
              const conversations = getProjectConversations(project.name)

              return (
                <div key={project.name}>
                  {/* Project Header */}
                  <div
                    onClick={() => handleProjectClick(project.name)}
                    className={`
                      flex items-center gap-2 px-3 py-2 mx-2 rounded-lg cursor-pointer
                      transition-colors group
                      ${isActive 
                        ? 'bg-accent-cyan/10 text-accent-cyan' 
                        : 'text-carbon-300 hover:bg-carbon-800/50 hover:text-white'
                      }
                    `}
                  >
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        toggleProject(project.name)
                      }}
                      className="p-0.5 hover:bg-carbon-700 rounded transition-colors"
                    >
                      {isExpanded ? (
                        <ChevronDown className="w-4 h-4" />
                      ) : (
                        <ChevronRight className="w-4 h-4" />
                      )}
                    </button>
                    
                    <FolderOpen className="w-4 h-4 flex-shrink-0" />
                    
                    <span className="flex-1 truncate text-sm font-medium">
                      {project.name}
                    </span>

                    <span className="text-xs text-carbon-500 group-hover:hidden">
                      {conversations.length}
                    </span>

                    <button
                      onClick={(e) => handleNewConversation(project.name, e)}
                      className="hidden group-hover:flex p-1 hover:bg-carbon-700 rounded transition-colors"
                      title="New conversation"
                    >
                      <Plus className="w-3.5 h-3.5" />
                    </button>
                  </div>

                  {/* Conversations List */}
                  <AnimatePresence>
                    {isExpanded && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.15 }}
                        className="overflow-hidden"
                      >
                        <div className="ml-6 mr-2 space-y-0.5 py-1">
                          {conversations.length === 0 ? (
                            <div className="px-3 py-2 text-xs text-carbon-500 italic">
                              No conversations yet
                            </div>
                          ) : (
                            conversations.map((conv) => (
                              <ConversationItem
                                key={conv.id}
                                conversation={conv}
                                isActive={activeConversationId === conv.id && isActive}
                                isHovered={hoveredConv === conv.id}
                                onHover={() => setHoveredConv(conv.id)}
                                onLeave={() => setHoveredConv(null)}
                                onClick={() => handleConversationClick(project.name, conv.id)}
                                onDelete={(e) => handleDeleteConversation(project.name, conv.id, e)}
                                onRename={(newTitle) => handleRenameConversation(project.name, conv.id, newTitle)}
                              />
                            ))
                          )}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}

interface ConversationItemProps {
  conversation: Conversation
  isActive: boolean
  isHovered: boolean
  onHover: () => void
  onLeave: () => void
  onClick: () => void
  onDelete: (e: React.MouseEvent) => void
  onRename: (newTitle: string) => void
}

function ConversationItem({
  conversation,
  isActive,
  isHovered,
  onHover,
  onLeave,
  onClick,
  onDelete,
  onRename,
}: ConversationItemProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [editTitle, setEditTitle] = useState(conversation.title)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus()
      inputRef.current.select()
    }
  }, [isEditing])

  const handleStartEdit = (e: React.MouseEvent) => {
    e.stopPropagation()
    setEditTitle(conversation.title)
    setIsEditing(true)
  }

  const handleSaveEdit = (e?: React.MouseEvent) => {
    e?.stopPropagation()
    if (editTitle.trim() && editTitle !== conversation.title) {
      onRename(editTitle.trim())
    }
    setIsEditing(false)
  }

  const handleCancelEdit = (e?: React.MouseEvent) => {
    e?.stopPropagation()
    setEditTitle(conversation.title)
    setIsEditing(false)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    e.stopPropagation()
    if (e.key === 'Enter') {
      handleSaveEdit()
    } else if (e.key === 'Escape') {
      handleCancelEdit()
    }
  }

  if (isEditing) {
    return (
      <div
        className="flex items-center gap-1 px-2 py-1.5 rounded-lg bg-carbon-800 border border-carbon-600"
        onClick={(e) => e.stopPropagation()}
      >
        <input
          ref={inputRef}
          type="text"
          value={editTitle}
          onChange={(e) => setEditTitle(e.target.value)}
          onKeyDown={handleKeyDown}
          onBlur={() => handleSaveEdit()}
          className="flex-1 bg-transparent text-sm text-white outline-none min-w-0"
        />
        <button
          onClick={handleSaveEdit}
          className="p-1 hover:bg-carbon-700 text-accent-emerald rounded transition-colors"
          title="Save"
        >
          <Check className="w-3 h-3" />
        </button>
        <button
          onClick={handleCancelEdit}
          className="p-1 hover:bg-carbon-700 text-carbon-400 rounded transition-colors"
          title="Cancel"
        >
          <X className="w-3 h-3" />
        </button>
      </div>
    )
  }

  return (
    <div
      onClick={onClick}
      onMouseEnter={onHover}
      onMouseLeave={onLeave}
      className={`
        flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer
        transition-colors group
        ${isActive 
          ? 'bg-accent-violet/15 text-accent-violet border-l-2 border-accent-violet' 
          : 'text-carbon-400 hover:bg-carbon-800/50 hover:text-carbon-200'
        }
      `}
    >
      <MessageSquare className="w-3.5 h-3.5 flex-shrink-0" />
      
      <span className="flex-1 truncate text-sm">
        {conversation.title}
      </span>

      {(isHovered || isActive) && (
        <div className="flex items-center gap-0.5">
          <button
            onClick={handleStartEdit}
            className="p-1 hover:bg-carbon-700 hover:text-accent-cyan rounded transition-colors"
            title="Rename conversation"
          >
            <Pencil className="w-3 h-3" />
          </button>
          <button
            onClick={onDelete}
            className="p-1 hover:bg-carbon-700 hover:text-accent-rose rounded transition-colors"
            title="Delete conversation"
          >
            <Trash2 className="w-3 h-3" />
          </button>
        </div>
      )}
    </div>
  )
}
