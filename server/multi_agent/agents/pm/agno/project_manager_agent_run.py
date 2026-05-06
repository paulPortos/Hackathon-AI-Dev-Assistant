import json

from django.conf import settings

from multi_agent.agents.ollama_agent_run_with_retry import ollama_agent_run_with_retry
from multi_agent.agents.pm.prompts.project_manager_agent_instructions import project_manager_agent_instructions
from multi_agent.agents.pm.schemas import ProjectManagerAgentOutput


def project_manager_agent_run(*, context):
    def normalize_output(value):
        if isinstance(value, ProjectManagerAgentOutput):
            return value.model_dump()
        if hasattr(value, 'model_dump'):
            return value.model_dump()
        if isinstance(value, dict):
            return ProjectManagerAgentOutput(**value).model_dump()
        if isinstance(value, str):
            return ProjectManagerAgentOutput(**json.loads(value)).model_dump()
        raise ValueError('Project Manager Agent returned an unsupported response')

    try:
        from agno.agent import Agent
        from agno.models.ollama import Ollama
    except ImportError as exc:
        raise ValueError('Agno dependencies are not installed') from exc

    agent = Agent(
        name='Project Manager Agent',
        model=Ollama(
            id=settings.PROJECT_MANAGER_AGENT_MODEL,
            host=settings.OLLAMA_HOST,
            api_key=settings.OLLAMA_API_KEY,
        ),
        output_schema=ProjectManagerAgentOutput,
        tools=[],
        markdown=False,
        instructions=project_manager_agent_instructions(),
    )
    response = ollama_agent_run_with_retry(
        agent,
        json.dumps(context, sort_keys=True, default=str),
        agent_name='Project Manager Agent',
    )
    return normalize_output(getattr(response, 'content', response))
