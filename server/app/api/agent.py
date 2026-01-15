"""
Agent API - Endpoints for the Code-RAG agent
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from app.agent import CodeRAGAgent

router = APIRouter()

# Global agent instance (in production, you'd want session-based agents)
_agent: Optional[CodeRAGAgent] = None


def get_agent() -> CodeRAGAgent:
    """Get or create the agent instance"""
    global _agent
    if _agent is None:
        _agent = CodeRAGAgent()
    return _agent


class ChatRequest(BaseModel):
    """Request for agent chat"""
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Response from agent chat"""
    response: str
    tool_calls: List[Dict[str, Any]]
    context: str


class PlanRequest(BaseModel):
    """Request for generating a plan"""
    query: str


class SetCodebaseRequest(BaseModel):
    """Request to set the active codebase"""
    path: str


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a message to the Code-RAG agent and get a response.
    The agent will automatically use tools as needed.
    """
    try:
        agent = get_agent()
        result = await agent.chat(request.message)
        
        return ChatResponse(
            response=result["response"],
            tool_calls=result.get("tool_calls", []),
            context=result.get("context", "")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/plan")
async def generate_plan(request: PlanRequest):
    """
    Generate a plan for answering a complex query.
    Returns a list of steps the agent would take.
    """
    try:
        agent = get_agent()
        steps = await agent.plan(request.query)
        
        return {
            "success": True,
            "query": request.query,
            "plan": steps
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/set-codebase")
async def set_codebase(request: SetCodebaseRequest):
    """
    Set the active codebase for the agent session.
    """
    agent = get_agent()
    agent.set_codebase(request.path)
    
    return {
        "success": True,
        "message": f"Active codebase set to: {request.path}"
    }


@router.get("/history")
async def get_history():
    """
    Get the conversation history for the current session.
    """
    agent = get_agent()
    history = agent.get_conversation_history()
    
    return {
        "success": True,
        "history": history
    }


@router.post("/clear")
async def clear_conversation():
    """
    Clear the conversation history and reset the agent.
    """
    agent = get_agent()
    agent.clear_conversation()
    
    return {
        "success": True,
        "message": "Conversation cleared"
    }


@router.get("/tools")
async def list_tools():
    """
    List all available tools the agent can use.
    """
    agent = get_agent()
    tools = agent.get_available_tools()
    
    return {
        "success": True,
        "tools": tools
    }

