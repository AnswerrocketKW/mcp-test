"""Utility functions for the MCP server."""

import os
import sys
from typing import Any, Dict, List, Optional, Tuple
from answer_rocket.client import AnswerRocketClient
from answer_rocket.graphql.schema import MaxCopilot, MaxCopilotSkill

from .models import SkillConfig, SkillParameter


def validate_environment() -> Tuple[str, str, str]:
    """Validate required environment variables."""
    ar_url = os.getenv("AR_URL")
    ar_token = os.getenv("AR_TOKEN")
    copilot_id = os.getenv("COPILOT_ID")
    
    if not ar_url:
        print("Error: AR_URL environment variable is required", file=sys.stderr)
        sys.exit(1)
    if not ar_token:
        print("Error: AR_TOKEN environment variable is required", file=sys.stderr)
        sys.exit(1)
    if not copilot_id:
        print("Error: COPILOT_ID environment variable is required", file=sys.stderr)
        sys.exit(1)
        
    return ar_url, ar_token, copilot_id


def create_client(ar_url: str, ar_token: str) -> AnswerRocketClient:
    """Create and validate AnswerRocket client."""
    client = AnswerRocketClient(url=ar_url, token=ar_token)
    
    if not client.can_connect():
        print(f"Error: Cannot connect to AnswerRocket at {ar_url}", file=sys.stderr)
        print("Please check your AR_URL and AR_TOKEN", file=sys.stderr)
        sys.exit(1)
        
    return client


def extract_skill_parameters(skill: MaxCopilotSkill) -> List[SkillParameter]:
    """Extract parameters from a skill."""
    parameters = []
    
    if not skill.parameters:
        return parameters
        
    for param in skill.parameters:
        skill_param = SkillParameter.from_max_parameter(param)
        if skill_param:
            parameters.append(skill_param)
            
    return parameters


def build_skill_configs(copilot: MaxCopilot, client: AnswerRocketClient) -> List[SkillConfig]:
    """Build skill configurations for all skills in a copilot."""
    skill_configs = []
    
    if not copilot.copilot_skill_ids:
        return skill_configs
        
    for skill_id in copilot.copilot_skill_ids:
        try:
            skill = client.config.get_copilot_skill(str(skill_id))
            if skill and not skill.scheduling_only:
                parameters = extract_skill_parameters(skill)
                skill_config = SkillConfig(
                    skill=skill,
                    parameters=parameters,
                    copilot_id=str(copilot.copilot_id)
                )
                skill_configs.append(skill_config)
        except Exception as e:
            print(f"Warning: Failed to load skill {skill_id}: {e}", file=sys.stderr)
            
    return skill_configs


def validate_skill_arguments(args: Dict[str, Any], skill_config: SkillConfig) -> Dict[str, Any]:
    """Validate and process skill arguments."""
    validated_args = {}
    
    for param in skill_config.parameters:
        if param.name in args:
            value = args[param.name]
            
            # Validate constrained values
            if param.constrained_values:
                if param.is_multi:
                    if not isinstance(value, list):
                        value = [value]
                    invalid_values = [v for v in value if v not in param.constrained_values]
                    if invalid_values:
                        raise ValueError(
                            f"Invalid values for {param.name}: {invalid_values}. "
                            f"Allowed values: {param.constrained_values}"
                        )
                else:
                    if value not in param.constrained_values:
                        raise ValueError(
                            f"Invalid value for {param.name}: {value}. "
                            f"Allowed values: {param.constrained_values}"
                        )
            
            # Handle multi-value parameters
            if param.is_multi and not isinstance(value, list):
                value = [value]
                
            validated_args[param.name] = value
        elif param.required:
            raise ValueError(f"Missing required parameter: {param.name}")
            
    return validated_args