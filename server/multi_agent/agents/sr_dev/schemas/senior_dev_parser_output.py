from typing import Any, Dict, List

from pydantic import BaseModel, Field


class SeniorDevParserOutput(BaseModel):
    assistant_message: str = Field(default='')
    check_in_question: str = Field(default='')
    choices: List[str] = Field(default_factory=list)
    allow_free_text: bool = Field(default=True)
    conversation_summary: str = Field(default='')
    claims: List[Dict[str, Any]] = Field(default_factory=list)
    findings: List[Dict[str, Any]] = Field(default_factory=list)
