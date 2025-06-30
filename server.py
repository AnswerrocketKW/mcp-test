from mcp.server.fastmcp import FastMCP
from typing import Dict, Any, List, Optional
from answer_rocket import AnswerRocketClient
import os
import asyncio

# Get environment variables
AR_URL = os.getenv("AR_URL", "")
AR_TOKEN = os.getenv("AR_TOKEN", "")
COPILOT_ID = os.getenv("COPILOT_ID", "")

if not COPILOT_ID:
    raise ValueError("COPILOT_ID environment variable is required")

if not AR_URL or not AR_TOKEN:
    raise ValueError("AR_URL and AR_TOKEN environment variables are required")

# Initialize AnswerRocket client
ar_client = AnswerRocketClient(AR_URL, AR_TOKEN)

# Get copilot information to use name for server
def get_copilot_info():
    """Get copilot information including name and skills."""
    try:
        if not ar_client.can_connect():
            raise ValueError("Cannot connect to AnswerRocket")
        
        # Get copilot information
        copilot_info = ar_client.config.get_copilot(True, COPILOT_ID)
        if not copilot_info:
            raise ValueError(f"Copilot with ID '{COPILOT_ID}' not found")
        
        return copilot_info
    except Exception as e:
        print(f"Error getting copilot info: {e}")
        # Fallback to using COPILOT_ID as name
        return None

# Get copilot info at startup
copilot_info = get_copilot_info()
COPILOT_NAME = str(copilot_info.name) if copilot_info and copilot_info.name else COPILOT_ID

# Create MCP server with copilot name
mcp = FastMCP(COPILOT_NAME)


def create_skill_tool(skill_info):
    """Create a tool function for a specific skill."""
    skill_id = str(skill_info.copilot_skill_id)
    skill_name = str(skill_info.name)
    skill_description = str(skill_info.description or skill_info.detailed_description or f"Execute {skill_name} skill")
    
    async def skill_tool_function(parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute this AnswerRocket skill.
        
        Args:
            parameters: Optional dictionary of parameters to pass to the skill
            
        Returns:
            Dict[str, Any]: Skill execution result
        """
        try:
            # Create AnswerRocket client
            ar_client = AnswerRocketClient(AR_URL, AR_TOKEN)
            if not ar_client.can_connect():
                raise ValueError("Cannot connect to AnswerRocket")
            
            # Run the skill
            skill_result = ar_client.skill.run(COPILOT_ID, skill_name, parameters)
            
            if not skill_result.success:
                return {
                    "success": False,
                    "error": skill_result.error,
                    "code": skill_result.code,
                    "skill_name": skill_name,
                    "skill_id": skill_id
                }
            
            return {
                "success": True,
                "data": skill_result.data,
                "code": skill_result.code,
                "skill_name": skill_name,
                "skill_id": skill_id
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error running skill {skill_name}: {str(e)}",
                "skill_name": skill_name,
                "skill_id": skill_id
            }
    
    return skill_tool_function


def create_chat_skill_tool(skill_info):
    """Create a chat-based tool function for a specific skill."""
    skill_id = str(skill_info.copilot_skill_id)
    skill_name = str(skill_info.name)
    skill_description = str(skill_info.description or skill_info.detailed_description or f"Ask questions to {skill_name} skill")
    
    async def chat_skill_tool_function(question: str) -> Dict[str, Any]:
        """
        Ask a question to this AnswerRocket skill and get insights with visualizations.
        
        Args:
            question: The question to ask this skill
            
        Returns:
            Dict[str, Any]: Response with chat_reply and artifact html for display
        """
        try:
            # Validate parameters
            if not question or not isinstance(question, str):
                raise ValueError("Question must be a non-empty string")
            
            # Create AnswerRocket client
            ar_client = AnswerRocketClient(AR_URL, AR_TOKEN)
            if not ar_client.can_connect():
                raise ValueError("Cannot connect to AnswerRocket")
            
            # Ask question using the chat interface
            skill_reply = ar_client.chat.ask_question(COPILOT_ID, question)

            # Check if the response has an error
            error_msg = getattr(getattr(skill_reply, 'answer', None), 'error', None)
            if error_msg:
                return {
                    "chat_reply": f"An error occurred: {error_msg}",
                    "artifact_html": "Error from AnswerRocket",
                    "skill_name": skill_name,
                    "skill_id": skill_id
                }

            # Extract message and payload
            answer = getattr(skill_reply, 'answer', None)
            message = getattr(answer, 'message', 'No message available') if answer else "No message available"
            
            # Extract custom payload if available
            payload = None
            if answer and hasattr(answer, 'report_results'):
                report_results = getattr(answer, 'report_results', [])
                if report_results and len(report_results) > 0:
                    payload = getattr(report_results[0], 'custom_payload', None)
            
            tabs = None
            if isinstance(payload, dict) and "tabs" in payload:
                if isinstance(payload["tabs"], dict) and "tabs" in payload["tabs"]:
                    tabs = payload["tabs"]["tabs"] or []
                elif isinstance(payload["tabs"], list) and payload["tabs"] and isinstance(payload["tabs"][0], dict):
                    tabs = payload["tabs"]
                    for t in payload["tabs"]:
                        if "label" not in t:
                            t["label"] = t.get("title") or "-"
            
            html = ""
            for t in tabs or []:
                html += f"<div class='tab'><h3>{t['label']}</h3><div>{t['content']}</div></div>"

            return {
                "chat_reply": message,
                "artifact_html": html,
                "skill_name": skill_name,
                "skill_id": skill_id
            }
            
        except Exception as e:
            return {
                "chat_reply": f"An error occurred: {str(e)}",
                "artifact_html": f"<div class='alert alert-danger'>Error in {skill_name}: {str(e)}</div>",
                "skill_name": skill_name,
                "skill_id": skill_id
            }
    
    return chat_skill_tool_function


def initialize_skill_tools():
    """Initialize tools for all skills in this copilot."""
    if not copilot_info or not copilot_info.copilot_skill_ids:
        print(f"No skills found for copilot {COPILOT_NAME}")
        return
    
    # Convert skill IDs to list - handle potential Field objects
    skill_ids_raw = copilot_info.copilot_skill_ids
    skill_ids = []
    
    if skill_ids_raw:
        # Try different ways to extract the actual list value
        if hasattr(skill_ids_raw, '__iter__') and not isinstance(skill_ids_raw, str):
            try:
                skill_ids = list(skill_ids_raw)
            except:
                skill_ids = []
        elif hasattr(skill_ids_raw, 'default'):
            skill_ids = skill_ids_raw.default or []
        elif hasattr(skill_ids_raw, 'value'):
            skill_ids = skill_ids_raw.value or []
    
    print(f"Initializing tools for {len(skill_ids)} skills...")
    
    for skill_id in skill_ids:
        try:
            # Get detailed skill information
            skill_info = ar_client.config.get_copilot_skill(True, COPILOT_ID, skill_id)
            if not skill_info:
                print(f"Warning: Could not get info for skill {skill_id}")
                continue
            
            skill_name = str(skill_info.name)
            skill_description = str(skill_info.description or skill_info.detailed_description or f"Execute {skill_name}")
            
            # Create a safe tool name (alphanumeric and underscores only)
            safe_tool_name = "".join(c if c.isalnum() or c == '_' else '_' for c in skill_name.lower())
            safe_tool_name = safe_tool_name.strip('_')
            
            # Ensure tool name is not empty
            if not safe_tool_name:
                safe_tool_name = f"skill_{skill_id}"
            
            # Create both execution and chat tools for each skill
            
            # 1. Skill execution tool (for running with parameters)
            skill_tool = create_skill_tool(skill_info)
            mcp.add_tool(
                skill_tool,
                name=f"run_{safe_tool_name}",
                description=f"Execute the {skill_name} skill with optional parameters. {skill_description[:200]}..."
            )
            
            # 2. Chat-based skill tool (for asking questions)
            chat_tool = create_chat_skill_tool(skill_info)
            mcp.add_tool(
                chat_tool,
                name=f"ask_{safe_tool_name}",
                description=f"Ask a question to the {skill_name} skill and get insights with visualizations. {skill_description[:200]}..."
            )
            
            print(f"✅ Created tools for skill: {skill_name} (run_{safe_tool_name}, ask_{safe_tool_name})")
            
        except Exception as e:
            print(f"❌ Error creating tool for skill {skill_id}: {e}")
            continue
    
    print(f"🚀 Initialized MCP server '{COPILOT_NAME}' with dynamic skill tools")


# Initialize all skill tools
initialize_skill_tools()


if __name__ == "__main__":
    print(f"Starting MCP server for copilot: {COPILOT_NAME} (ID: {COPILOT_ID})")
    mcp.run(transport='stdio')
    print("Server stopped")