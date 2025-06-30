from mcp.server.fastmcp import FastMCP
from typing import Dict, Any, List, Optional
from answer_rocket import AnswerRocketClient
import os

# Get environment variables
AR_URL = os.getenv("AR_URL", "")
AR_TOKEN = os.getenv("AR_TOKEN", "")
COPILOT_ID = os.getenv("COPILOT_ID", "")

if not COPILOT_ID:
    raise ValueError("COPILOT_ID environment variable is required")

# Create an MCP server with copilot-specific name
mcp = FastMCP(f"mcp-rocket-server-{COPILOT_ID}")


# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}! This is the AnswerRocket MCP server for copilot {COPILOT_ID}."


def ar_ask_question(copilot_id: str, question: str) -> Dict[str, Any]:
    """Ask a question to AnswerRocket copilot."""
    # Create AnswerRocket client
    ar_client = AnswerRocketClient(AR_URL, AR_TOKEN)
    if ar_client.can_connect():
        skill_reply = ar_client.chat.ask_question(copilot_id, question)

        # Check if the response has an error
        error_msg = getattr(getattr(skill_reply, 'answer', None), 'error', None)
        if error_msg:
            return {
                "chat_reply": f"An error occurred: {error_msg}",
                "artifact_html": "Error from AnswerRocket"
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
            "artifact_html": html
        }
    else:
        return {
            "chat_reply": "Error connecting to AnswerRocket",
            "artifact_html": "Error from AnswerRocket"
        }


# Ask Question Tool (automatically uses the configured copilot)
@mcp.tool(description=f"Ask a question to AnswerRocket copilot {COPILOT_ID} and get charts, graphs and insights.")
async def ask_question(fully_contextualized_question: str) -> Dict[str, Any]:
    """
    A tool that provides charts, graphs and insights for user questions using this copilot.
    
    Args:
        fully_contextualized_question: The user's question with full context
        
    Returns:
        Dict[str, Any]: Response with chat_reply and artifact html for display
    """
    
    try:
        # Validate parameters
        if not fully_contextualized_question or not isinstance(fully_contextualized_question, str):
            raise ValueError("Question must be a non-empty string")
        
        return ar_ask_question(COPILOT_ID, fully_contextualized_question)
        
    except Exception as e:
        error_message = f"Error in Ask Question tool: {str(e)}"
        
        return {
            "chat_reply": f"An error occurred: {str(e)}",
            "artifact_html": f"<div class='alert alert-danger'>{error_message}</div>"
        }


# Get Copilot Information Tool
@mcp.tool(description=f"Get information about copilot {COPILOT_ID}, including its available skills.")
async def get_copilot_info(use_published_version: bool = True) -> Dict[str, Any]:
    """
    Get detailed information about this copilot including its available skills.
    
    Args:
        use_published_version: Whether to use the published version of the copilot (default: True)
        
    Returns:
        Dict[str, Any]: Copilot information including name, description, and skill IDs
    """
    
    try:
        # Create AnswerRocket client
        ar_client = AnswerRocketClient(AR_URL, AR_TOKEN)
        if not ar_client.can_connect():
            raise ValueError("Cannot connect to AnswerRocket")
        
        # Get copilot information
        copilot_info = ar_client.config.get_copilot(use_published_version, COPILOT_ID)
        
        if not copilot_info:
            return {
                "error": f"Copilot with ID '{COPILOT_ID}' not found"
            }
        
        return {
            "copilot_id": copilot_info.copilot_id,
            "name": copilot_info.name,
            "description": copilot_info.description,
            "system_prompt": copilot_info.system_prompt,
            "skill_ids": copilot_info.copilot_skill_ids,
            "connection_datasets": copilot_info.connection_datasets,
            "copilot_topics": copilot_info.copilot_topics
        }
        
    except Exception as e:
        return {
            "error": f"Error getting copilot info: {str(e)}"
        }


# Get Copilot Skill Information Tool
@mcp.tool(description=f"Get detailed information about a specific skill within copilot {COPILOT_ID}.")
async def get_skill_info(skill_id: str, use_published_version: bool = True) -> Dict[str, Any]:
    """
    Get detailed information about a specific skill.
    
    Args:
        skill_id: The ID of the skill to get information about
        use_published_version: Whether to use the published version of the skill (default: True)
        
    Returns:
        Dict[str, Any]: Skill information including name, description, and parameters
    """
    
    try:
        # Validate parameters
        if not skill_id or not isinstance(skill_id, str):
            raise ValueError("Skill ID must be a non-empty string")
        
        # Create AnswerRocket client
        ar_client = AnswerRocketClient(AR_URL, AR_TOKEN)
        if not ar_client.can_connect():
            raise ValueError("Cannot connect to AnswerRocket")
        
        # Get skill information
        skill_info = ar_client.config.get_copilot_skill(use_published_version, COPILOT_ID, skill_id)
        
        if not skill_info:
            return {
                "error": f"Skill with ID '{skill_id}' not found in copilot '{COPILOT_ID}'"
            }
        
        return {
            "copilot_skill_id": skill_info.copilot_skill_id,
            "name": skill_info.name,
            "detailed_name": skill_info.detailed_name,
            "description": skill_info.description,
            "detailed_description": skill_info.detailed_description,
            "skill_type": skill_info.copilot_skill_type,
            "dataset_id": skill_info.dataset_id,
            "scheduling_only": skill_info.scheduling_only,
            "skill_chat_questions": [
                {
                    "question_id": getattr(q, 'copilot_skill_chat_question_id', None),
                    "question": getattr(q, 'question', None),
                    "expected_response": getattr(q, 'expected_completion_response', None)
                }
                for q in (getattr(skill_info, 'skill_chat_questions', None) or [])
            ]
        }
        
    except Exception as e:
        return {
            "error": f"Error getting skill info: {str(e)}"
        }


# Run Copilot Skill Tool
@mcp.tool(description=f"Run a specific skill within copilot {COPILOT_ID} with optional parameters.")
async def run_skill(skill_name: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Run a specific skill within this copilot.
    
    Args:
        skill_name: The name of the skill to run
        parameters: Optional dictionary of parameters to pass to the skill
        
    Returns:
        Dict[str, Any]: Skill execution result
    """
    
    try:
        # Validate parameters
        if not skill_name or not isinstance(skill_name, str):
            raise ValueError("Skill name must be a non-empty string")
        
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
                "code": skill_result.code
            }
        
        return {
            "success": True,
            "data": skill_result.data,
            "code": skill_result.code
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error running skill: {str(e)}"
        }


# Dynamically create skill-specific tools
def create_skill_tools():
    """Create dynamic tools for each skill in the copilot."""
    try:
        # Create AnswerRocket client
        ar_client = AnswerRocketClient(AR_URL, AR_TOKEN)
        if not ar_client.can_connect():
            print(f"Warning: Cannot connect to AnswerRocket to create skill tools")
            return
        
        # Get copilot information
        copilot_info = ar_client.config.get_copilot(True, COPILOT_ID)
        if not copilot_info or not copilot_info.copilot_skill_ids:
            print(f"Warning: No skills found for copilot {COPILOT_ID}")
            return
        
        # Create a tool for each skill
        for skill_id in (copilot_info.copilot_skill_ids or []):
            try:
                skill_info = ar_client.config.get_copilot_skill(True, COPILOT_ID, skill_id)
                if not skill_info:
                    continue
                
                skill_name = str(skill_info.name or skill_id)
                skill_description = str(skill_info.description or skill_info.detailed_description or f"Run the {skill_name} skill")
                
                # Create a closure to capture the current skill_name
                def make_skill_tool(name: str, desc: str):
                    async def skill_tool_func(parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
                        return await run_skill(name, parameters)
                    
                    skill_tool_func.__name__ = f"run_{name.lower().replace(' ', '_').replace('-', '_')}"
                    skill_tool_func.__doc__ = f"""
                    Run the {name} skill.
                    
                    Args:
                        parameters: Optional dictionary of parameters to pass to the skill
                        
                    Returns:
                        Dict[str, Any]: Skill execution result
                    """
                    
                    return skill_tool_func
                
                # Add the tool to the MCP server
                skill_tool = make_skill_tool(skill_name, skill_description)
                mcp.add_tool(
                    skill_tool,
                    description=f"{skill_description} (Skill: {skill_name})"
                )
                
            except Exception as e:
                print(f"Warning: Could not create tool for skill {skill_id}: {e}")
                
    except Exception as e:
        print(f"Warning: Error creating skill tools: {e}")


# Create skill tools on startup
create_skill_tools()


if __name__ == "__main__":
    print(f"Starting MCP server for copilot {COPILOT_ID}")
    mcp.run(transport='stdio')
    print("Server stopped")