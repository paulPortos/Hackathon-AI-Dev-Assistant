from typing import Any, Dict, List

from pydantic import BaseModel, Field, field_validator


class SeniorDevParserOutput(BaseModel):
    assistant_message: str = Field(default='')
    check_in_question: str = Field(default='')
    choices: List[str] = Field(default_factory=list)
    allow_free_text: bool = Field(default=True)
    conversation_summary: str = Field(default='')
    claims: List[Dict[str, Any]] = Field(default_factory=list)
    findings: List[Dict[str, Any]] = Field(default_factory=list)

    @field_validator('claims', 'findings', mode='before')
    @classmethod
    def coerce_list_items_to_dicts(cls, v):
        """Coerce string items to {'text': str} so Pydantic does not reject them."""
        if not isinstance(v, list):
            return v
        result = []
        for item in v:
            if isinstance(item, dict):
                result.append(item)
            elif isinstance(item, str) and item.strip():
                result.append({'text': item.strip()})
            # silently drop None / empty strings
        return result
