from django.conf import settings

from multi_agent.agents.sr_dev.prompts.senior_dev_agent_instructions import senior_dev_agent_instructions


def senior_dev_agent_run(*, session, user_message, tools):
    try:
        from agno.agent import Agent
        from agno.models.google import Gemini
    except ImportError as exc:
        raise ValueError('Agno dependencies are not installed') from exc

    agent = Agent(
        name='Senior Dev Agent',
        model=Gemini(id=settings.SR_DEV_AGENT_MODEL),
        tools=tools,
        markdown=False,
        tool_call_limit=settings.SR_DEV_TOOL_CALL_LIMIT,
        instructions=senior_dev_agent_instructions(),
    )
    prompt = (
        f'Project ID: {session.project_id}\n'
        f'Git commit SHA: {session.commit_sha}\n'
        f'Branch label: {session.branch_name or "not provided"}\n'
        f'User message:\n{user_message.text_content}'
    )
    response = agent.run(prompt)
    return str(getattr(response, 'content', response) or '').strip()
