from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, TextBlock, ToolUseBlock, ResultMessage
from prompts.prompt import GENERATOR_SYSTEM_PROMPT, KVK_AGENT_PROMPT, WEBSITE_AGENT_PROMPT, USER_INPUT_AGENT_PROMPT

#later put this in separate json file agents_config.json
kvk_agent = {"system_prompt": KVK_AGENT_PROMPT, "tools": ["WebSearch"], "max_turns": 5}
website_agent = {"system_prompt": WEBSITE_AGENT_PROMPT, "tools": ["WebSearch"], "max_turns": 5}
user_input_agent = {"system_prompt": USER_INPUT_AGENT_PROMPT, "tools": [], "max_turns": 1}
generator_agent = {"system_prompt": GENERATOR_SYSTEM_PROMPT, "tools": [], "max_turns": 1}

def build_prompt(company, user_input): #params only
    prompt = ( 
        f"Bedrijf: {company}\n"
        f"Extra informatie: {user_input}"
    )
    return prompt

async def run_agent(company, agent, prompt):

    options = ClaudeAgentOptions(
        system_prompt=agent["system_prompt"],
        tools=agent["tools"],
        allowed_tools=agent["tools"],
        max_turns=agent["max_turns"]
    )

    result = "" #can later be in specific format
    async for msg in query(prompt=prompt, options=options):
        if isinstance(msg, ResultMessage): #last message of the run, holds the final answer
            result = msg.result or ""
    return result

async def run_case(company, user_input="", website=False, kvk=False):
    sources = {}
    if kvk:
        yield "search", "KvK-register" #shown in the frontend as a chip while the agent runs
        prompt = build_prompt(company, user_input)
        sources["kvk"] = await run_agent(company=company, agent=kvk_agent, prompt=prompt)

    if website:
        yield "search", "website en openbare bronnen"
        prompt = build_prompt(company, user_input)
        sources["website"] = await run_agent(company=company, agent=website_agent, prompt=prompt)

    if user_input:
        yield "search", "aangeleverde extra informatie"
        prompt = build_prompt(company, user_input)
        sources["user_input"] = await run_agent(company=company, agent=user_input_agent, prompt=prompt)

    # print(sources)

    generator_prompt = f"Bedrijf: {company}\n\n"
    for name, findings in sources.items():
        generator_prompt += f"## Bron: {name}\n{findings}\n\n"

    report_text = await run_agent(company=company, agent=generator_agent, prompt=generator_prompt)

    yield "text", report_text
