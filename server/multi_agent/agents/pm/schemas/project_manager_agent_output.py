from typing import Any, Dict, List

from pydantic import BaseModel, Field


class ProjectManagerAgentOutput(BaseModel):
    summary: str = Field(default='')
    vulnerabilities: List[Dict[str, Any]] = Field(default_factory=list)
    tasks: List[Dict[str, Any]] = Field(default_factory=list)
