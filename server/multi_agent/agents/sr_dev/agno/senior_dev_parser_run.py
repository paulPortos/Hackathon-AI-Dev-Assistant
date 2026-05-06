from agno.agent import Agent
from agno.models.ollama import Ollama
import json

from django.conf import settings

from multi_agent.agents.ollama_agent_run_with_retry import ollama_agent_run_with_retry
from multi_agent.agents.sr_dev.prompts.senior_dev_parser_instructions import senior_dev_parser_instructions
from multi_agent.agents.sr_dev.schemas import SeniorDevParserOutput


def senior_dev_parser_run(*, session, user_message, assistant_text, tool_call_summary):
    """Executes a structured parser agent to extract data from a conversation turn."""
    def normalize_output(value):
        def classify_item(item):
            item_type = str(item.get('type') or item.get('kind') or '').strip().lower()
            if item_type.startswith('finding'):
                return 'finding'
            if item_type.startswith('claim'):
                return 'claim'

            if any(key in item for key in ('severity', 'confidence_score', 'confidence_reason', 'finding_type')):
                return 'finding'
            if 'title' in item and 'text' not in item and 'claim' not in item:
                return 'finding'
            return 'claim'

        def wrap_list(items):
            claims = []
            findings = []
            for item in items:
                if isinstance(item, dict):
                    bucket = classify_item(item)
                    if bucket == 'finding':
                        findings.append(item)
                    else:
                        claims.append(item)
                else:
                    claims.append({'text': str(item or '').strip()})
            return {
                'assistant_message': '',
                'check_in_question': '',
                'choices': [],
                'allow_free_text': True,
                'conversation_summary': '',
                'claims': claims,
                'findings': findings,
            }

        if isinstance(value, SeniorDevParserOutput):
            return value.model_dump()
        if hasattr(value, 'model_dump'):
            return value.model_dump()

        parsed = value
        if isinstance(parsed, str):
            parsed = json.loads(parsed)

        if isinstance(parsed, list):
            parsed = wrap_list(parsed)

        if isinstance(parsed, dict):
            return SeniorDevParserOutput(**parsed).model_dump()

        raise ValueError('Senior Dev parser returned an unsupported response')

    agent = Agent(
        name='Senior Dev Structured Parser',
        model=Ollama(
            id=settings.SR_DEV_AGENT_MODEL,
            host=settings.OLLAMA_HOST,
            api_key=settings.OLLAMA_API_KEY,
        ),
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
    response = ollama_agent_run_with_retry(agent, prompt, agent_name='Senior Dev Structured Parser')
    return normalize_output(getattr(response, 'content', response))
