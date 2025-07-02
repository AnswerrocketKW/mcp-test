from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from typing import Dict, Any, List, Optional
from answer_rocket import AnswerRocketClient
import os
import asyncio
import inspect

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


def extract_skill_parameters(skill_info) -> Dict[str, Dict[str, Any]]:
    """Extract parameters from skill info using the GraphQL schema fields."""
    parameters = {}
    
    if not hasattr(skill_info, 'parameters') or not skill_info.parameters:
        return parameters
    
    for param in skill_info.parameters:
        copilot_parameter_type = getattr(param, 'copilot_parameter_type', None)
        if copilot_parameter_type != "CHAT":
            continue

        param_name = str(param.name)
        
        # Determine parameter type based on isMulti field
        param_type = "array" if getattr(param, 'is_multi', False) else "string"
        
        # Get description from llm_description or description field
        description = str(getattr(param, 'llm_description', '') or 
                         getattr(param, 'description', '') or 
                         f"Parameter {param_name}")
        
        # Check if parameter has constrained values
        constrained_values = getattr(param, 'constrained_values', None)
        if constrained_values:
            description += f" (Allowed values: {', '.join(map(str, constrained_values))})"
        
        # Determine if required based on whether it has a value or inheritedValue
        # has_default = bool(getattr(param, 'value', None) or getattr(param, 'inherited_value', None))
        # required = not has_default  # If no default value, it's required
        
        parameters[param_name] = {
            'type': param_type,
            'description': description,
            'required': False,
            'is_multi': getattr(param, 'is_multi', False),
            'constrained_values': constrained_values,
            'key': getattr(param, 'key', param_name)  # Use key field if available
        }
    
    return parameters


def create_skill_tool_with_annotations(skill_info):
    """Create a tool function with proper annotations for a specific skill."""
    skill_id = str(skill_info.copilot_skill_id)
    skill_name = str(skill_info.name)
    skill_description = str(skill_info.description or skill_info.detailed_description or f"Execute {skill_name} skill")
    
    # Extract parameters from skill
    skill_parameters = extract_skill_parameters(skill_info)
    
    # Create ToolAnnotations with appropriate hints based on skill metadata
    annotations = ToolAnnotations(
        title=skill_info.detailed_name if hasattr(skill_info, 'detailed_name') else skill_name,
        # Most copilot skills are read-only queries
        readOnlyHint=not getattr(skill_info, 'scheduling_only', False),
        # Skills are typically non-destructive
        destructiveHint=False,
        # Skills with same params should return same results
        idempotentHint=True,
        # Skills may interact with external data sources
        openWorldHint=True
    )
    
    # Build function signature dynamically based on parameters
    def create_dynamic_function(skill_params):
        async def skill_tool_function(**kwargs) -> Dict[str, Any]:
            """Execute this AnswerRocket skill."""
            try:
                # Validate and transform parameters
                processed_params = {}
                for param_name, param_info in skill_params.items():
                    if param_name in kwargs:
                        value = kwargs[param_name]
                        # if the value is null, don't include it in the processed_params
                        if value is None:
                            continue
                        # Use the 'key' field if available, otherwise use name
                        param_key = param_info.get('key', param_name)
                        
                        # Validate constrained values if present
                        # if param_info.get('constrained_values') and value not in param_info['constrained_values']:
                        #     return {
                        #         "success": False,
                        #         "error": f"Invalid value for {param_name}. Allowed values: {param_info['constrained_values']}",
                        #         "skill_name": skill_name,
                        #         "skill_id": skill_id
                        #     }
                        
                        processed_params[param_key] = value
                    elif param_info.get('required', False):
                        return {
                            "success": False,
                            "error": f"Required parameter '{param_name}' not provided",
                            "skill_name": skill_name,
                            "skill_id": skill_id
                        }
                
                # Create AnswerRocket client
                ar_client = AnswerRocketClient(AR_URL, AR_TOKEN)
                if not ar_client.can_connect():
                    raise ValueError("Cannot connect to AnswerRocket")
                
                # Run the skill with processed parameters
                skill_result = ar_client.skill.run(COPILOT_ID, skill_name, processed_params)
                
                if not skill_result.success:
                    return {
                        "success": False,
                        "error": skill_result.error,
                        "code": skill_result.code,
                        "skill_name": skill_name,
                        "skill_id": skill_id,
                        "parameters_used": processed_params
                    }
                
                if skill_result.data != None:
                    return {
                        "success": True,
                        "data": skill_result.data.get("final_message", ""),
                        "code": skill_result.code,
                        "skill_name": skill_name,
                        "skill_id": skill_id,
                        "parameters_used": processed_params
                    }
                else:
                    return {
                        "success": True,
                        "data": "No data returned from skill",
                        "code": skill_result.code,
                        "skill_name": skill_name,
                        "skill_id": skill_id,
                        "parameters_used": processed_params
                    }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Error running skill {skill_name}: {str(e)}",
                    "skill_name": skill_name,
                    "skill_id": skill_id,
                    "parameters_attempted": kwargs
                }
        
        # Set function metadata
        skill_tool_function.__name__ = f"skill_{skill_name.lower().replace(' ', '_')}"
        skill_tool_function.__doc__ = skill_description
        
        # Add parameter annotations for better MCP integration
        sig_params = []
        for param_name, param_info in skill_params.items():
            is_required = param_info.get('required', False)
            base_type = List[str] if param_info['type'] == 'array' else str
            param_type = base_type if is_required else Optional[base_type]
            default = inspect.Parameter.empty if is_required else None
            sig_params.append(
                inspect.Parameter(
                    param_name,
                    inspect.Parameter.KEYWORD_ONLY,
                    default=default,
                    annotation=param_type
                )
            )
        
        # Create proper function signature
        skill_tool_function.__signature__ = inspect.Signature(sig_params)
        
        return skill_tool_function
    
    # Create the function with captured parameters
    tool_function = create_dynamic_function(skill_parameters)
    
    return tool_function, annotations, skill_parameters





async def fetch_skill_info(skill_id: str):
    """Fetch skill information asynchronously."""
    try:
        skill_info = ar_client.config.get_copilot_skill(
            copilot_id=COPILOT_ID,
            copilot_skill_id=str(skill_id),
            use_published_version=True
        )
        return skill_info
    except Exception as e:
        print(f"❌ Error fetching skill {skill_id}: {e}")
        return None


async def register_skill_tool(skill_info):
    """Register a single skill as a tool."""
    if not skill_info:
        return False
    
    try:
        skill_name = str(skill_info.name)

        # # log the skill description by saving tmp
        # file = open("/tmp/skill_description.txt", "w")
        # file.write(str(skill_info.description) + "\n" + str(skill_info.detailed_description) + "\n" + str(skill_info))
        # file.close()

        skill_description = str(skill_info.detailed_description) or f"Execute {skill_name}"
        
        # Create a safe tool name (alphanumeric and underscores only)
        safe_tool_name = "".join(c if c.isalnum() or c == '_' else '_' for c in skill_name.lower())
        safe_tool_name = safe_tool_name.strip('_') or f"skill_{skill_info.copilot_skill_id}"
        
        # Create skill execution tool with dynamic parameters and annotations
        skill_tool, annotations, tool_parameters = create_skill_tool_with_annotations(skill_info)
        
        # Add the tool with annotations
        mcp.add_tool(
            skill_tool,
            name=safe_tool_name,
            description=skill_description,
            annotations=annotations
        )
        
        # Log parameter info
        param_count = len(tool_parameters) if tool_parameters else 0
        param_info = f" with {param_count} parameters" if param_count > 0 else ""
        print(f"✅ Created tool for skill: {skill_name} ({safe_tool_name}){param_info}")
        
        if param_count > 0:
            for param_name, param_config in tool_parameters.items():
                required_text = 'required' if param_config['required'] else 'optional'
                constrained_text = f" [{', '.join(param_config['constrained_values'])}]" if param_config.get('constrained_values') else ""
                print(f"   - {param_name}: {param_config['type']} ({required_text}){constrained_text}")
        
        return True
    except Exception as e:
        print(f"❌ Error registering tool for skill {skill_info.name if skill_info else 'unknown'}: {e}")
        return False


async def initialize_skill_tools_async():
    """Initialize tools for all skills in this copilot using parallel processing."""
    if not copilot_info or not copilot_info.copilot_skill_ids:
        print(f"No skills found for copilot {COPILOT_NAME}")
        return
    
    # Convert skill IDs to list
    skill_ids = copilot_info.copilot_skill_ids
    if not isinstance(skill_ids, list):
        skill_ids = [skill_ids] if skill_ids else []
    
    print(f"Initializing tools for {len(skill_ids)} skills...")
    
    # Fetch all skill info in parallel
    skill_infos = await asyncio.gather(*[fetch_skill_info(str(skill_id)) for skill_id in skill_ids])
    
    # Register all skills in parallel
    results = await asyncio.gather(*[register_skill_tool(skill_info) for skill_info in skill_infos])
    
    success_count = sum(1 for result in results if result)
    print(f"🚀 Successfully initialized {success_count}/{len(skill_ids)} skill tools for '{COPILOT_NAME}'")


def initialize_skill_tools():
    """Wrapper to run async initialization."""
    asyncio.run(initialize_skill_tools_async())


# Initialize all skill tools
initialize_skill_tools()


if __name__ == "__main__":
    print(f"Starting MCP server for copilot: {COPILOT_NAME} (ID: {COPILOT_ID})")
    mcp.run(transport='stdio')
    print("Server stopped")