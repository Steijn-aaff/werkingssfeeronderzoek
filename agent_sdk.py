# Agent SDK: async stream of messages from an agent loop, with optional web search as a tool
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, TextBlock, ToolUseBlock
from prompts.prompt import GENERATOR_SYSTEM_PROMPT, KVK_AGENT_PROMPT, WEBSITE_AGENT_PROMPT, USER_INPUT_AGENT_PROMPT

#later put this in separate json file agents_config.json
kvk_agent = {"system_prompt": KVK_AGENT_PROMPT, "tools": ["WebSearch"], "max_turns": 5}
website_agent = {"system_prompt": WEBSITE_AGENT_PROMPT, "tools": ["WebSearch"], "max_turns": 5}
user_input_agent = {"system_prompt": USER_INPUT_AGENT_PROMPT, "tools": [], "max_turns": 1}
generator_agent = {"system_prompt": GENERATOR_SYSTEM_PROMPT, "tools": [], "max_turns": 1}

def build_prompt(company): #params only
    prompt = ( 
        f"Bedrijf: {company}\n"
    )
    return prompt

async def run_agent(company, agent, user_input):

    options = ClaudeAgentOptions(
        system_prompt=agent["system_prompt"],
        tools=agent["tools"],
        allowed_tools=agent["tools"],
        max_turns=agent["max_turns"]
    )

    prompt = build_prompt(company)

    result = "" #can later be in specific format
    async for msg in query(prompt=prompt, options=options):
        if isinstance(msg, ResultMessage): #last message of the run, holds the final answer
            result = msg.result or ""
    return result

async def run_case(company, user_input, website, kvk):
    sources = {}
    if kvk:
        sources["kvk"] = await run_agent(company=company, agent=kvk_agent)
    
    if website:
        sources["website"] = await run_agent(company=company, agent=website_agent)

    if user_input:
        sources["user_input"] = await run_agent(company=company, agent=user_input_agent, user_input=user_input)

    #Streaming
    async for msg in query(prompt=prompt, options=options):
        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                if isinstance(block, TextBlock):
                    yield "text", block.text
