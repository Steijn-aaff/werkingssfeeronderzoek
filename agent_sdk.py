# Agent SDK: async stream of messages from an agent loop, with optional web search as a tool
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, TextBlock, ToolUseBlock
from pathlib import Path


TEMPLATE_NAME = "werkingssfeeronderzoek_small.md"
TEMPLATE = (Path(__file__).parent / "templates" / TEMPLATE_NAME).read_text(encoding="utf-8")

SYSTEM_PROMPT = (
    "Je stelt een werkingssfeeronderzoek op voor een bedrijf. "
    "Vul onderstaande template in en geef als antwoord alleen het ingevulde rapport in Markdown. "
    "Volg de instructies in de commentaren van de template. "
    "Verzin geen feiten en noem per bevinding de bron. "
    "Is een bron uitgeschakeld of niet beschikbaar, schrijf dan 'Niet beschikbaar: <reden>' onder de betreffende kop.\n\n"
    "TEMPLATE:\n" + TEMPLATE)

async def ask(company, website=True, kvk=False):

    options = ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        tools=["WebSearch"] if website else [],
        allowed_tools=["WebSearch"] if website else [],
        max_turns= 5 if website else 1, 
    )
    prompt = (
        f"Bedrijf: {company}\n"
        "(de KvK-bron is nog niet gekoppeld, dus sectie 2.1 kun je niet invullen)."
    )

    async for msg in query(prompt=prompt, options=options):
        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                if isinstance(block, ToolUseBlock): #remove if we don't want to show web searches
                    yield "search", block.input.get("query")
                elif isinstance(block, TextBlock):
                    yield "text", block.text

