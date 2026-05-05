from agno.agent import Agent
from agno.models.google import Gemini
import json

from django.conf import settings

from multi_agent.agents.sr_dev.prompts.senior_dev_parser_instructions import senior_dev_parser_instructions
from multi_agent.agents.sr_dev.schemas import SeniorDevParserOutput


def senior_dev_parser_run(*, session, user_message, assistant_text, tool_call_summary):
    """Executes a structured parser agent to extract data from a conversation turn."""
    def normalize_output(value):
        if isinstance(value, SeniorDevParserOutput):
            return value.model_dump()
        if hasattr(value, 'model_dump'):
            return value.model_dump()
        if isinstance(value, dict):
            return SeniorDevParserOutput(**value).model_dump()
        if isinstance(value, str):
            return SeniorDevParserOutput(**json.loads(value)).model_dump()
        raise ValueError('Senior Dev parser returned an unsupported response')

    agent = Agent(
        name='Senior Dev Structured Parser',
        model=Gemini(id=settings.SR_DEV_AGENT_MODEL),
        output_schema=SeniorDevParserOutput,
        tools=[],
        markdown=False,
        instructions=senior_dev_parser_instructions(),
    )
    prompt = json.dumps(
        {
            'project_id': session.project_id,
            'commit_sha': session.commit_sha,
            'user_message': user_message.text_content,
            'assistant_message': assistant_text,
            'tool_call_summary': tool_call_summary,
        },
        sort_keys=True,
        default=str,
    )
    response = agent.run(prompt)
    return normalize_output(getattr(response, 'content', response))
