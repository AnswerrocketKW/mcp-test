from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
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


def extract_skill_parameters(skill_info):
    """Extract parameters directly from skill object."""
    parameters = {}
    
    try:
        # Get parameters directly from the skill object
        if hasattr(skill_info, 'parameters') and skill_info.parameters:
            # Handle potential Field objects or direct values
            skill_params = skill_info.parameters
            if hasattr(skill_params, '__iter__') and not isinstance(skill_params, str):
                # If it's iterable (list/dict), use it directly
                if isinstance(skill_params, dict):
                    parameters = skill_params
                elif isinstance(skill_params, list):
                     # Convert list of parameter objects to dict
                     for param in skill_params:
                         if hasattr(param, 'name'):
                             param_name = str(param.name)
                             # Check if it's multi-value (list of strings) or single string
                             is_multi = bool(getattr(param, 'is_multi', False))
                             param_type = "array" if is_multi else "string"
                             
                             param_config = {
                                 'type': param_type,
                                 'description': str(getattr(param, 'description', '')),
                                 'required': bool(getattr(param, 'required', False))
                             }
                             parameters[param_name] = param_config
                        
    except Exception as e:
        print(f"Warning: Error extracting parameters from skill: {e}")
    
    return parameters


def create_skill_tool_with_annotations(skill_info):
    """Create a tool function and annotations for a specific skill."""
    skill_id = str(skill_info.copilot_skill_id)
    skill_name = str(skill_info.name)
    skill_description = str(skill_info.description or skill_info.detailed_description or f"Execute {skill_name} skill")
    
    # Extract parameters from skill nodes
    skill_parameters = extract_skill_parameters(skill_info)
    
    # Create ToolAnnotations
    tool_parameters = {}
    
    if skill_parameters:
        for param_name, param_info in skill_parameters.items():
            # Handle different parameter info formats
            param_description = ""
            param_type = "string"  # default
            required = False
            
            if isinstance(param_info, dict):
                param_description = param_info.get('description', '')
                param_type = param_info.get('type', 'string')
                required = param_info.get('required', False)
            elif isinstance(param_info, str):
                param_description = param_info
            
            # Only two types: string or array of strings
            mcp_type = "array" if param_type == "array" else "string"
            
            tool_parameters[param_name] = {
                "type": mcp_type,
                "description": param_description,
                "required": required
            }
    
    # Create annotations
    annotations = ToolAnnotations() if tool_parameters else None
    if annotations and tool_parameters:
        # Set parameters directly on the annotations object
        for param_name, param_config in tool_parameters.items():
            setattr(annotations, param_name, param_config)
    
    # Create the tool function
    async def skill_tool_function(**kwargs) -> Dict[str, Any]:
        """Execute this AnswerRocket skill with its specific parameters."""
        try:
            # Filter kwargs to only include expected parameters
            if skill_parameters:
                filtered_params = {k: v for k, v in kwargs.items() if k in skill_parameters}
            else:
                # If no specific parameters, treat all kwargs as parameters
                filtered_params = kwargs
            
            # Create AnswerRocket client
            ar_client = AnswerRocketClient(AR_URL, AR_TOKEN)
            if not ar_client.can_connect():
                raise ValueError("Cannot connect to AnswerRocket")
            
            # Run the skill
            skill_result = ar_client.skill.run(COPILOT_ID, skill_name, filtered_params)
            
            if not skill_result.success:
                return {
                    "success": False,
                    "error": skill_result.error,
                    "code": skill_result.code,
                    "skill_name": skill_name,
                    "skill_id": skill_id,
                    "parameters_used": filtered_params
                }
            
            return {
                "success": True,
                "data": skill_result.data,
                "code": skill_result.code,
                "skill_name": skill_name,
                "skill_id": skill_id,
                "parameters_used": filtered_params
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error running skill {skill_name}: {str(e)}",
                "skill_name": skill_name,
                "skill_id": skill_id,
                "parameters_attempted": kwargs
            }
    
    return skill_tool_function, annotations, tool_parameters





def initialize_skill_tools():
    """Initialize tools for all skills in this copilot."""
    if not copilot_info or not copilot_info.copilot_skill_ids:
        print(f"No skills found for copilot {COPILOT_NAME}")
        return
    
    # Convert skill IDs to list - handle potential Field objects
    skill_ids = []
    try:
        # Try to access the skill IDs in different ways
        if copilot_info.copilot_skill_ids:
            # Try direct conversion first
            skill_ids = copilot_info.copilot_skill_ids
            if not isinstance(skill_ids, list):
                # If it's not a list, try to convert it
                skill_ids = [skill_ids] if skill_ids else []
    except Exception as e:
        print(f"Warning: Could not extract skill IDs: {e}")
        skill_ids = []
    
    print(f"Initializing tools for {len(skill_ids)} skills...")
    
    for skill_id in skill_ids:
        try:
            # Get detailed skill information with full node data
            skill_info = ar_client.config.get_copilot_skill(
                copilot_id=COPILOT_ID,
                copilot_skill_id=str(skill_id),
                use_published_version=True
            )
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
            
            # Create skill execution tool with dynamic parameters and annotations
            skill_tool, annotations, tool_parameters = create_skill_tool_with_annotations(skill_info)
            
            # Add the tool with annotations
            mcp.add_tool(
                skill_tool,
                name=safe_tool_name,
                description=f"Execute the {skill_name} skill. {skill_description[:200]}...",
                annotations=annotations
            )
            
            # Log parameter info
            param_count = len(tool_parameters) if tool_parameters else 0
            param_info = f" with {param_count} parameters" if param_count > 0 else ""
            print(f"✅ Created tool for skill: {skill_name} ({safe_tool_name}){param_info}")
            
            if param_count > 0:
                for param_name, param_config in tool_parameters.items():
                    print(f"   - {param_name}: {param_config['type']} ({'required' if param_config['required'] else 'optional'})")
            
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