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
  projectName: string
  messages: Message[]
  createdAt: string
  updatedAt: string
}

interface ChatState {
  conversations: Record<string, Conversation>
  activeProjectName: string | null
  
  // Actions
  setActiveProject: (projectName: string) => void
  addMessage: (projectName: string, message: Message) => void
  getConversation: (projectName: string) => Conversation | null
  clearConversation: (projectName: string) => void
  clearAllConversations: () => void
}

export const useChatStore = create<ChatState>()(
  persist(
    (set, get) => ({
      conversations: {},
      activeProjectName: null,

      setActiveProject: (projectName: string) => {
        set({ activeProjectName: projectName })
        
        // Create conversation if it doesn't exist
        const { conversations } = get()
        if (!conversations[projectName]) {
          set({
            conversations: {
              ...conversations,
              [projectName]: {
                id: `conv_${Date.now()}`,
                projectName,
                messages: [],
                createdAt: new Date().toISOString(),
                updatedAt: new Date().toISOString(),
              },
            },
          })
        }
      },

      addMessage: (projectName: string, message: Message) => {
        const { conversations } = get()
        const conversation = conversations[projectName] || {
          id: `conv_${Date.now()}`,
          projectName,
          messages: [],
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        }

        set({
          conversations: {
            ...conversations,
            [projectName]: {
              ...conversation,
              messages: [...conversation.messages, message],
              updatedAt: new Date().toISOString(),
            },
          },
        })
      },

      getConversation: (projectName: string) => {
        const { conversations } = get()
        return conversations[projectName] || null
      },

      clearConversation: (projectName: string) => {
        const { conversations } = get()
        if (conversations[projectName]) {
          set({
            conversations: {
              ...conversations,
              [projectName]: {
                ...conversations[projectName],
                messages: [],
                updatedAt: new Date().toISOString(),
              },
            },
          })
        }
      },

      clearAllConversations: () => {
        set({ conversations: {} })
      },
    }),
    {
      name: 'code-rag-chat-storage',
      version: 1,
    }
  )
)
