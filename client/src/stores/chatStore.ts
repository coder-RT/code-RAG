import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: { file: string; snippet: string }[]
  timestamp: string
  modelUsed?: string
}

export interface Conversation {
  id: string
  title: string
  messages: Message[]
  createdAt: string
  updatedAt: string
}

export interface ProjectChats {
  projectName: string
  conversations: Conversation[]
}

interface ChatState {
  projects: Record<string, ProjectChats>
  activeProjectName: string | null
  activeConversationId: string | null
  
  // Actions
  setActiveProject: (projectName: string) => void
  setActiveConversation: (conversationId: string) => void
  createConversation: (projectName: string, title?: string) => string
  deleteConversation: (projectName: string, conversationId: string) => void
  renameConversation: (projectName: string, conversationId: string, title: string) => void
  addMessage: (projectName: string, conversationId: string, message: Message) => void
  getActiveConversation: () => Conversation | null
  getProjectConversations: (projectName: string) => Conversation[]
  clearAllData: () => void
}

const generateTitle = (firstMessage?: string): string => {
  if (!firstMessage) return `Chat ${new Date().toLocaleDateString()}`
  const truncated = firstMessage.slice(0, 40)
  return truncated.length < firstMessage.length ? `${truncated}...` : truncated
}

export const useChatStore = create<ChatState>()(
  persist(
    (set, get) => ({
      projects: {},
      activeProjectName: null,
      activeConversationId: null,

      setActiveProject: (projectName: string) => {
        const { projects } = get()
        
        // Initialize project if it doesn't exist
        if (!projects[projectName]) {
          const newConvId = `conv_${Date.now()}`
          set({
            activeProjectName: projectName,
            activeConversationId: newConvId,
            projects: {
              ...projects,
              [projectName]: {
                projectName,
                conversations: [{
                  id: newConvId,
                  title: 'New Chat',
                  messages: [],
                  createdAt: new Date().toISOString(),
                  updatedAt: new Date().toISOString(),
                }],
              },
            },
          })
        } else {
          // Set active to first conversation if exists
          const projectChats = projects[projectName]
          const firstConv = projectChats.conversations[0]
          set({
            activeProjectName: projectName,
            activeConversationId: firstConv?.id || null,
          })
        }
      },

      setActiveConversation: (conversationId: string) => {
        set({ activeConversationId: conversationId })
      },

      createConversation: (projectName: string, title?: string) => {
        const { projects } = get()
        const newConvId = `conv_${Date.now()}`
        const newConv: Conversation = {
          id: newConvId,
          title: title || 'New Chat',
          messages: [],
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        }

        const projectChats = projects[projectName] || {
          projectName,
          conversations: [],
        }

        set({
          activeConversationId: newConvId,
          projects: {
            ...projects,
            [projectName]: {
              ...projectChats,
              conversations: [newConv, ...projectChats.conversations],
            },
          },
        })

        return newConvId
      },

      deleteConversation: (projectName: string, conversationId: string) => {
        const { projects, activeConversationId } = get()
        const projectChats = projects[projectName]
        if (!projectChats) return

        const updatedConversations = projectChats.conversations.filter(
          (c) => c.id !== conversationId
        )

        // If deleting active conversation, switch to another
        let newActiveConvId = activeConversationId
        if (activeConversationId === conversationId) {
          newActiveConvId = updatedConversations[0]?.id || null
        }

        set({
          activeConversationId: newActiveConvId,
          projects: {
            ...projects,
            [projectName]: {
              ...projectChats,
              conversations: updatedConversations,
            },
          },
        })
      },

      renameConversation: (projectName: string, conversationId: string, title: string) => {
        const { projects } = get()
        const projectChats = projects[projectName]
        if (!projectChats) return

        set({
          projects: {
            ...projects,
            [projectName]: {
              ...projectChats,
              conversations: projectChats.conversations.map((c) =>
                c.id === conversationId ? { ...c, title, updatedAt: new Date().toISOString() } : c
              ),
            },
          },
        })
      },

      addMessage: (projectName: string, conversationId: string, message: Message) => {
        const { projects } = get()
        const projectChats = projects[projectName]
        if (!projectChats) return

        const conversation = projectChats.conversations.find((c) => c.id === conversationId)
        if (!conversation) return

        // Auto-generate title from first user message if title is "New Chat"
        const shouldUpdateTitle = 
          conversation.title === 'New Chat' && 
          message.role === 'user' && 
          conversation.messages.length === 0

        set({
          projects: {
            ...projects,
            [projectName]: {
              ...projectChats,
              conversations: projectChats.conversations.map((c) =>
                c.id === conversationId
                  ? {
                      ...c,
                      title: shouldUpdateTitle ? generateTitle(message.content) : c.title,
                      messages: [...c.messages, message],
                      updatedAt: new Date().toISOString(),
                    }
                  : c
              ),
            },
          },
        })
      },

      getActiveConversation: () => {
        const { projects, activeProjectName, activeConversationId } = get()
        if (!activeProjectName || !activeConversationId) return null
        
        const projectChats = projects[activeProjectName]
        if (!projectChats) return null
        
        return projectChats.conversations.find((c) => c.id === activeConversationId) || null
      },

      getProjectConversations: (projectName: string) => {
        const { projects } = get()
        return projects[projectName]?.conversations || []
      },

      clearAllData: () => {
        set({ projects: {}, activeProjectName: null, activeConversationId: null })
      },
    }),
    {
      name: 'code-rag-chat-storage',
      version: 2,
    }
  )
)
