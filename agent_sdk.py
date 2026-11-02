# Agent SDK: async stream of messages from an agent loop, with optional web search as a tool
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, TextBlock, ToolUseBlock
from prompts.prompt import SYSTEM_PROMPT

def build_prompt(company, user_input): #params only
    prompt = ( 
        f"Bedrijf: {company}\n"
        f"Extra informatie: {user_input}\n"
        f"Kvk: de KvK-bron is nog niet gekoppeld"
    )
    return prompt

async def ask(company, user_input, website=True, kvk=False):

    options = ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        tools=["WebSearch"] if website else [],
        allowed_tools=["WebSearch"] if website else [],
        max_turns= 5 if website else 1
    )
    prompt = build_prompt(company, user_input)

    async for msg in query(prompt=prompt, options=options):
        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                if isinstance(block, ToolUseBlock): #remove if we don't want to show web searches
                    yield "search", block.input.get("query")
                elif isinstance(block, TextBlock):
                    yield "text", block.text

