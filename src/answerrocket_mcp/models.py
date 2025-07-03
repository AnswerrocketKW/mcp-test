"""Type definitions and models for the MCP server."""

from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from answer_rocket.graphql.schema import MaxCopilot, MaxCopilotSkill, MaxCopilotSkillParameter


@dataclass
class SkillParameter:
    """Processed skill parameter for MCP tool generation."""
    name: str
    type_hint: type
    description: Optional[str]
    required: bool
    is_multi: bool
    constrained_values: Optional[List[str]]
    
    @classmethod
    def from_max_parameter(cls, param: MaxCopilotSkillParameter) -> Optional['SkillParameter']:
        """Create SkillParameter from MaxCopilotSkillParameter."""
        if not param.name or not param.value:
            return None
            
        # Determine type from parameter value and metadata
        type_hint = str
        if param.is_multi:
            type_hint = List[str]
            
        return cls(
            name=param.name,
            type_hint=type_hint,
            description=param.llm_description or param.description,
            required=param.value.lower() != "[optional]",
            is_multi=bool(param.is_multi),
            constrained_values=param.constrained_values if param.constrained_values else None
        )


@dataclass
class SkillConfig:
    """Configuration for a skill tool."""
    skill: MaxCopilotSkill
    parameters: List[SkillParameter]
    copilot_id: str
    
    @property
    def tool_name(self) -> str:
        """Generate MCP tool name from skill name."""
        return self.skill.name.replace(" ", "_").replace("-", "_")
    
    @property
    def tool_description(self) -> str:
        """Get tool description."""
        return self.skill.detailed_description or self.skill.description