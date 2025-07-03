"""MCP Server implementation for AnswerRocket."""

import asyncio
import json
from typing import Any, Callable, Dict, List
from functools import partial

from mcp.types import ToolAnnotations
from mcp.server.fastmcp import FastMCP
from answer_rocket.client import AnswerRocketClient
from answer_rocket.graphql.schema import MaxCopilot

from .models import SkillConfig
from .utils import (
    validate_environment,
    create_client,
    build_skill_configs,
    validate_skill_arguments
)


class AnswerRocketMCPServer:
    """MCP Server for AnswerRocket copilots."""
    
    def __init__(self, ar_url: str, ar_token: str, copilot_id: str):
        self.ar_url = ar_url
        self.ar_token = ar_token
        self.copilot_id = copilot_id
        self.client: AnswerRocketClient = None
        self.copilot: MaxCopilot = None
        self.mcp: FastMCP = None
        self.skill_configs: List[SkillConfig] = []
        
    def initialize(self) -> FastMCP:
        """Initialize the MCP server."""
        # Create client and fetch copilot
        self.client = create_client(self.ar_url, self.ar_token)
        self.copilot = self.client.config.get_copilot(self.copilot_id)
        
        if not self.copilot:
            raise ValueError(f"Copilot {self.copilot_id} not found")
            
        # Initialize MCP with copilot name
        server_name = f"{self.copilot.name} Assistant"
        self.mcp = FastMCP(server_name)
        
        # Build skill configurations
        self.skill_configs = build_skill_configs(self.copilot, self.client)
        
        # Register tools
        self._register_tools()
        
        return self.mcp
        
    def _register_tools(self):
        """Register all skill tools with MCP."""
        for skill_config in self.skill_configs:
            self._register_skill_tool(skill_config)
            
    def _register_skill_tool(self, skill_config: SkillConfig):
        """Register a single skill as an MCP tool."""
        # Create the tool function
        tool_func = self._create_tool_function(skill_config)
        
        # Build annotations
        annotations = self._build_tool_annotations(skill_config)
        
        # Register with MCP
        self.mcp.tool(
            name=skill_config.tool_name,
            description=skill_config.tool_description,
            annotations=annotations
        )(tool_func)
        
    def _create_tool_function(self, skill_config: SkillConfig) -> Callable:
        """Create a tool function for a skill."""
        async def skill_tool(**kwargs) -> Dict[str, Any]:
            try:
                # Validate arguments
                validated_args = validate_skill_arguments(kwargs, skill_config)
                
                # Run the skill
                result = await asyncio.get_event_loop().run_in_executor(
                    None,
                    partial(
                        self.client.skill.run,
                        skill_id=str(skill_config.skill.copilot_skill_id),
                        inputs=validated_args,
                        copilot_id=self.copilot_id
                    )
                )
                
                if result.success:
                    return {
                        "success": True,
                        "data": result.data.model_dump() if result.data else None
                    }
                else:
                    return {
                        "success": False,
                        "error": result.error or "Unknown error occurred"
                    }
                    
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }
                
        return skill_tool
        
    def _build_tool_annotations(self, skill_config: SkillConfig) -> ToolAnnotations:
        """Build tool annotations for a skill."""
        properties = {}
        required = []
        
        for param in skill_config.parameters:
            # Build property schema
            prop_schema = {"type": "string"}
            
            if param.is_multi:
                prop_schema = {
                    "type": "array",
                    "items": {"type": "string"}
                }
                
            if param.description:
                prop_schema["description"] = param.description
                
            if param.constrained_values:
                if param.is_multi:
                    prop_schema["items"]["enum"] = param.constrained_values
                else:
                    prop_schema["enum"] = param.constrained_values
                    
            properties[param.name] = prop_schema
            
            if param.required:
                required.append(param.name)
                
        return ToolAnnotations(
            input_schema={
                "type": "object",
                "properties": properties,
                "required": required
            }
        )


def create_server() -> FastMCP:
    """Create and initialize the MCP server."""
    ar_url, ar_token, copilot_id = validate_environment()
    server = AnswerRocketMCPServer(ar_url, ar_token, copilot_id)
    return server.initialize()