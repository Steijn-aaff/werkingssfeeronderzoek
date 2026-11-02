from pathlib import Path

TEMPLATE_NAME = "werkingssfeeronderzoek.md"
TEMPLATE = (Path(__file__).parent.parent / "templates" / TEMPLATE_NAME).read_text(encoding="utf-8")

SYSTEM_PROMPT = (
    "Je stelt een werkingssfeeronderzoek op voor een bedrijf vanuit een accountancy bureau. "
    "Vul onderstaande template in en geef als antwoord alleen het ingevulde rapport in Markdown."
    "Volg de instructies in de commentaren van de template, en gebruik de extra informatie en bronnen die zijn meegegeven."
    "Verzin geen feiten en noem per bevinding de bron (specifieke website, kvk register, anders) als deze beschikbaar is. "
    "TEMPLATE:\n" + TEMPLATE) #template in system prompt gets cached (cheaper)
