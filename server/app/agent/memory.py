"""
Agent Memory - Conversation and context management for the Code-RAG agent
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json


class MessageRole(str, Enum):
    """Message roles in conversation"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class Message:
    """A single message in the conversation"""
    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    tool_call_id: Optional[str] = None
    tool_calls: Optional[List[Dict]] = None


@dataclass
class ToolCall:
    """Record of a tool call"""
    id: str
    name: str
    arguments: Dict[str, Any]
    result: Any
    timestamp: datetime = field(default_factory=datetime.now)
    duration_ms: Optional[float] = None


class ConversationMemory:
    """
    Manages conversation history and context for the agent.
    Handles message storage, summarization, and context window management.
    """
    
    def __init__(self, max_messages: int = 50, max_tokens: int = 8000):
        self.max_messages = max_messages
        self.max_tokens = max_tokens
        self.messages: List[Message] = []
        self.tool_calls: List[ToolCall] = []
        self.metadata: Dict[str, Any] = {}
        
    def add_message(self, role: MessageRole, content: str, **kwargs) -> Message:
        """Add a message to the conversation"""
        message = Message(role=role, content=content, **kwargs)
        self.messages.append(message)
        
        # Trim if exceeds max
        if len(self.messages) > self.max_messages:
            self._trim_messages()
        
        return message
    
    def add_user_message(self, content: str) -> Message:
        """Add a user message"""
        return self.add_message(MessageRole.USER, content)
    
    def add_assistant_message(self, content: str, tool_calls: Optional[List[Dict]] = None) -> Message:
        """Add an assistant message"""
        return self.add_message(MessageRole.ASSISTANT, content, tool_calls=tool_calls)
    
    def add_tool_result(self, tool_call_id: str, content: str) -> Message:
        """Add a tool result message"""
        return self.add_message(MessageRole.TOOL, content, tool_call_id=tool_call_id)
    
    def record_tool_call(self, call: ToolCall):
        """Record a tool call for history"""
        self.tool_calls.append(call)
    
    def get_messages(self, limit: Optional[int] = None) -> List[Message]:
        """Get conversation messages"""
        if limit:
            return self.messages[-limit:]
        return self.messages
    
    def get_messages_for_llm(self) -> List[Dict]:
        """
        Get messages formatted for LLM API.
        Returns list of message dicts with role and content.
        """
        formatted = []
        
        for msg in self.messages:
            message_dict = {
                "role": msg.role.value,
                "content": msg.content
            }
            
            if msg.tool_call_id:
                message_dict["tool_call_id"] = msg.tool_call_id
            
            if msg.tool_calls:
                message_dict["tool_calls"] = msg.tool_calls
            
            formatted.append(message_dict)
        
        return formatted
    
    def get_recent_tool_calls(self, limit: int = 5) -> List[ToolCall]:
        """Get recent tool calls"""
        return self.tool_calls[-limit:]
    
    def clear(self):
        """Clear conversation history"""
        self.messages = []
        self.tool_calls = []
    
    def set_metadata(self, key: str, value: Any):
        """Set conversation metadata"""
        self.metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get conversation metadata"""
        return self.metadata.get(key, default)
    
    def _trim_messages(self):
        """Trim old messages, keeping system message if present"""
        # Keep system message if it exists
        system_msg = None
        if self.messages and self.messages[0].role == MessageRole.SYSTEM:
            system_msg = self.messages[0]
        
        # Keep most recent messages
        keep_count = self.max_messages - (1 if system_msg else 0)
        recent = self.messages[-keep_count:] if not system_msg else self.messages[-keep_count:]
        
        if system_msg:
            self.messages = [system_msg] + recent
        else:
            self.messages = recent
    
    def get_context_summary(self) -> str:
        """Generate a summary of the current context"""
        summary_parts = []
        
        # Indexed codebase
        if codebase := self.get_metadata("indexed_codebase"):
            summary_parts.append(f"Indexed codebase: {codebase}")
        
        # Recent topics
        user_messages = [m for m in self.messages if m.role == MessageRole.USER][-3:]
        if user_messages:
            topics = [m.content[:50] + "..." if len(m.content) > 50 else m.content 
                     for m in user_messages]
            summary_parts.append(f"Recent topics: {', '.join(topics)}")
        
        # Tool usage
        if self.tool_calls:
            tool_names = list(set(tc.name for tc in self.tool_calls[-5:]))
            summary_parts.append(f"Recent tools used: {', '.join(tool_names)}")
        
        return " | ".join(summary_parts) if summary_parts else "No context"
    
    def to_dict(self) -> Dict:
        """Serialize memory to dictionary"""
        return {
            "messages": [
                {
                    "role": m.role.value,
                    "content": m.content,
                    "timestamp": m.timestamp.isoformat(),
                    "metadata": m.metadata
                }
                for m in self.messages
            ],
            "tool_calls": [
                {
                    "id": tc.id,
                    "name": tc.name,
                    "arguments": tc.arguments,
                    "timestamp": tc.timestamp.isoformat()
                }
                for tc in self.tool_calls
            ],
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ConversationMemory":
        """Deserialize memory from dictionary"""
        memory = cls()
        
        for msg_data in data.get("messages", []):
            memory.add_message(
                role=MessageRole(msg_data["role"]),
                content=msg_data["content"],
                metadata=msg_data.get("metadata", {})
            )
        
        memory.metadata = data.get("metadata", {})
        return memory


class WorkingMemory:
    """
    Short-term working memory for the current task.
    Stores intermediate results, plans, and observations.
    """
    
    def __init__(self):
        self.current_goal: Optional[str] = None
        self.plan: List[str] = []
        self.observations: List[Dict] = []
        self.scratchpad: Dict[str, Any] = {}
    
    def set_goal(self, goal: str):
        """Set the current goal"""
        self.current_goal = goal
    
    def set_plan(self, steps: List[str]):
        """Set the execution plan"""
        self.plan = steps
    
    def add_observation(self, tool: str, result: Any, summary: str):
        """Add an observation from tool execution"""
        self.observations.append({
            "tool": tool,
            "result": result,
            "summary": summary,
            "timestamp": datetime.now().isoformat()
        })
    
    def note(self, key: str, value: Any):
        """Store something in the scratchpad"""
        self.scratchpad[key] = value
    
    def recall(self, key: str) -> Any:
        """Recall something from the scratchpad"""
        return self.scratchpad.get(key)
    
    def get_observations_summary(self) -> str:
        """Get a summary of observations"""
        if not self.observations:
            return "No observations yet."
        
        summaries = [f"- {obs['tool']}: {obs['summary']}" for obs in self.observations]
        return "\n".join(summaries)
    
    def clear(self):
        """Clear working memory"""
        self.current_goal = None
        self.plan = []
        self.observations = []
        self.scratchpad = {}

