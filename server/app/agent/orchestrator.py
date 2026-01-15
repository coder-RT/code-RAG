"""
Agent Orchestrator - Main agent loop and coordination for Code-RAG
"""

import json
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime

from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.agent.tools import ToolRegistry, ToolResult, get_tools_for_openai
from app.agent.memory import ConversationMemory, WorkingMemory, MessageRole, ToolCall
from app.agent.prompts import SYSTEM_PROMPT, PLANNING_PROMPT, SYNTHESIS_PROMPT


class CodeRAGAgent:
    """
    Main orchestrator for the Code-RAG coding agent.
    Coordinates tools, memory, and LLM to answer user queries.
    """
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            openai_api_key=settings.OPENAI_API_KEY,
            temperature=0.1
        )
        self.tool_registry = ToolRegistry()
        self.conversation = ConversationMemory()
        self.working_memory = WorkingMemory()
        
        # Initialize with system prompt
        self.conversation.add_message(MessageRole.SYSTEM, SYSTEM_PROMPT)
    
    async def chat(self, message: str) -> Dict[str, Any]:
        """
        Main entry point for user messages.
        Processes the message and returns a response.
        """
        # Add user message to conversation
        self.conversation.add_user_message(message)
        self.working_memory.set_goal(message)
        
        # Get response with potential tool calls
        response = await self._run_agent_loop(message)
        
        return {
            "response": response,
            "tool_calls": [
                {"name": tc.name, "success": tc.result is not None}
                for tc in self.working_memory.observations
            ],
            "context": self.conversation.get_context_summary()
        }
    
    async def _run_agent_loop(self, query: str, max_iterations: int = 5) -> str:
        """
        Run the agent loop with tool calling.
        Iteratively calls tools until a final answer is ready.
        """
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            # Get LLM response with tool options
            messages = self.conversation.get_messages_for_llm()
            tools = get_tools_for_openai()
            
            response = await self.llm.ainvoke(
                messages,
                tools=tools,
                tool_choice="auto"
            )
            
            # Check if response has tool calls
            if hasattr(response, 'tool_calls') and response.tool_calls:
                # Execute tool calls
                for tool_call in response.tool_calls:
                    await self._execute_tool_call(tool_call)
            else:
                # No tool calls - we have a final answer
                final_response = response.content
                self.conversation.add_assistant_message(final_response)
                self.working_memory.clear()
                return final_response
        
        # Max iterations reached - synthesize from observations
        return await self._synthesize_response(query)
    
    async def _execute_tool_call(self, tool_call) -> ToolResult:
        """Execute a single tool call and record the result"""
        tool_name = tool_call.function.name
        
        try:
            arguments = json.loads(tool_call.function.arguments)
        except json.JSONDecodeError:
            arguments = {}
        
        # Record the tool call
        start_time = datetime.now()
        
        # Execute the tool
        result = await self.tool_registry.execute(tool_name, **arguments)
        
        duration = (datetime.now() - start_time).total_seconds() * 1000
        
        # Record in memory
        tc_record = ToolCall(
            id=tool_call.id,
            name=tool_name,
            arguments=arguments,
            result=result.data if result.success else result.error,
            duration_ms=duration
        )
        self.conversation.record_tool_call(tc_record)
        
        # Add observation to working memory
        summary = self._summarize_tool_result(tool_name, result)
        self.working_memory.add_observation(tool_name, result.data, summary)
        
        # Add tool result to conversation
        result_content = json.dumps(result.data) if result.success else f"Error: {result.error}"
        self.conversation.add_tool_result(tool_call.id, result_content)
        
        # Add assistant message acknowledging the tool call
        self.conversation.add_assistant_message(
            "",
            tool_calls=[{
                "id": tool_call.id,
                "type": "function",
                "function": {
                    "name": tool_name,
                    "arguments": json.dumps(arguments)
                }
            }]
        )
        
        return result
    
    def _summarize_tool_result(self, tool_name: str, result: ToolResult) -> str:
        """Generate a brief summary of a tool result"""
        if not result.success:
            return f"Failed: {result.error}"
        
        data = result.data
        
        if tool_name == "query_codebase":
            return f"Found answer with {len(data.get('sources', []))} sources"
        elif tool_name == "explain_code":
            return f"Generated explanation ({len(str(data))} chars)"
        elif tool_name == "analyze_architecture":
            modules = len(data.get('modules', []))
            layers = len(data.get('layers', []))
            return f"Found {modules} modules, {layers} layers"
        elif tool_name == "analyze_terraform":
            resources = len(data.get('resources', []))
            return f"Found {resources} resources"
        elif tool_name == "generate_graph":
            stats = data.get('stats', {})
            return f"Generated graph: {stats.get('total_nodes', 0)} nodes, {stats.get('total_edges', 0)} edges"
        elif tool_name == "get_structure":
            return "Retrieved directory structure"
        
        return "Completed successfully"
    
    async def _synthesize_response(self, query: str) -> str:
        """Synthesize a final response from observations"""
        observations = self.working_memory.get_observations_summary()
        
        prompt = SYNTHESIS_PROMPT.format(
            question=query,
            tool_results=observations
        )
        
        response = await self.llm.ainvoke(prompt)
        final_response = response.content
        
        self.conversation.add_assistant_message(final_response)
        self.working_memory.clear()
        
        return final_response
    
    async def plan(self, query: str) -> List[str]:
        """
        Generate a plan for answering a complex query.
        Returns a list of steps to execute.
        """
        prompt = PLANNING_PROMPT.format(question=query)
        response = await self.llm.ainvoke(prompt)
        
        # Parse the plan from the response
        # This is a simple implementation - could be enhanced
        plan_text = response.content
        steps = [
            line.strip().lstrip("0123456789.-) ")
            for line in plan_text.split("\n")
            if line.strip() and not line.strip().startswith("#")
        ]
        
        self.working_memory.set_plan(steps)
        return steps
    
    def set_codebase(self, path: str):
        """Set the current codebase being analyzed"""
        self.conversation.set_metadata("indexed_codebase", path)
    
    def get_conversation_history(self) -> List[Dict]:
        """Get the conversation history"""
        return [
            {
                "role": msg.role.value,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat()
            }
            for msg in self.conversation.get_messages()
            if msg.role != MessageRole.SYSTEM
        ]
    
    def clear_conversation(self):
        """Clear the conversation history"""
        self.conversation.clear()
        self.working_memory.clear()
        self.conversation.add_message(MessageRole.SYSTEM, SYSTEM_PROMPT)
    
    def get_available_tools(self) -> List[Dict]:
        """Get list of available tools"""
        return self.tool_registry.list_tools()

