# Agent SDK: research agent collects facts into a markdown dossier, report agent fills the template from it
import re
from datetime import datetime
from pathlib import Path
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, ToolUseBlock, ResultMessage, ResultError
from prompts.prompt import RESEARCH_PROMPT, SYSTEM_PROMPT

RESEARCH_DIR = Path(__file__).parent / "research"

def build_research_prompt(company, user_input, kvk): #params only
    prompt = (
        f"Bedrijf: {company}\n"
        f"Extra informatie van de gebruiker: {user_input or 'geen'}\n"
        f"KvK-gegevens: {kvk}"
    )
    return prompt

def save_research(company, dossier):
    RESEARCH_DIR.mkdir(exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", company.lower()).strip("-") or "bedrijf"
    path = RESEARCH_DIR / f"{slug}_{datetime.now():%Y%m%d_%H%M%S}.md"
    path.write_text(dossier, encoding="utf-8")
    return path

async def finish_dossier(session_id):
    options = ClaudeAgentOptions(system_prompt=RESEARCH_PROMPT, tools=[], max_turns=1, resume=session_id)
    prompt = "Stop met zoeken. Schrijf nu het volledige dossier volgens de template met wat je hebt gevonden."
    async for msg in query(prompt=prompt, options=options):
        if isinstance(msg, ResultMessage):
            if msg.is_error or not msg.result:
                raise RuntimeError(f"Research-agent faalde: {msg.subtype}")
            return msg.result

async def research(company, user_input, website, kvk):

    options = ClaudeAgentOptions(
        system_prompt=RESEARCH_PROMPT,
        tools=["WebSearch", "WebFetch"] if website else [],
        allowed_tools=["WebSearch", "WebFetch"] if website else [],
        max_turns=12 if website else 1,
    )
    prompt = build_research_prompt(company, user_input, kvk)

    try:
        async for msg in query(prompt=prompt, options=options):
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, ToolUseBlock): #remove if we don't want to show web searches
                        value = block.input.get("query") or block.input.get("url")
                        if value:
                            yield "search", value               
            elif isinstance(msg, ResultMessage) and msg.subtype == "success" and msg.result:
                    yield "research", msg.result
    
    except ResultError as e:
        # Out of turns - continue with 1 turn on finish dossier with information it has right now
        if e.subtype != "error_max_turns" or not e.session_id:
            raise
        yield "research", await finish_dossier(e.session_id)

async def build_report(company, research_path):

    options = ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        tools=[],
        max_turns=1,
    )
    dossier = research_path.read_text(encoding="utf-8")
    prompt = f"Bedrijf: {company} ONDERZOEKSDOSSIER: {dossier}"

    async for msg in query(prompt=prompt, options=options):
        if isinstance(msg, ResultMessage):
            if msg.is_error or not msg.result:
                raise RuntimeError(f"Rapport-agent faalde: {msg.subtype}")
            yield "text", msg.result

async def ask(company, user_input, website=True, kvk=False):
    path = None
    async for kind, value in research(company, user_input, website, kvk):
        if kind == "research":
            path = save_research(company, value)
            yield "saved", str(path)
        yield kind, value

    async for kind, value in build_report(company, path):
        yield kind, value
