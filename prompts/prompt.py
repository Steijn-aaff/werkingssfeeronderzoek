from pathlib import Path

TEMPLATE_NAME = "werkingssfeeronderzoek_small.md"
TEMPLATE = (Path(__file__).parent.parent / "templates" / TEMPLATE_NAME).read_text(encoding="utf-8")

GENERATOR_SYSTEM_PROMPT = (
    "Je stelt een werkingssfeeronderzoek op voor een bedrijf vanuit een accountancy bureau. "
    "Vul onderstaande template in en geef als antwoord alleen het ingevulde rapport in Markdown."
    "Volg de instructies in de commentaren van de template."
    "Verzin geen feiten en noem per bevinding de bron (specifieke website, kvk register, anders) als deze beschikbaar is. "
    "Je krijgt de bevindingen van onderzoeksagenten per bron aangeleverd om het rapport in te vullen; gebruik UITSLUITEND deze bevindingen."
    "TEMPLATE:\n" + TEMPLATE) #template in system prompt gets cached (cheaper)

KVK_AGENT_PROMPT = (
    "Je verzamelt gegevens uit het KvK-handelsregister voor een werkingssfeeronderzoek. "
    "Zoek op kvk.nl en vergelijkbare registers naar: KvK-nummer, rechtsvorm, statutaire naam, handelsnamen, "
    "vestigingsadres, datum oprichting, SBI-codes en bestuurders. "
    "Geef alleen gevonden feiten als lijst in de vorm '- bevinding (bron: url)'. Verzin niets; meld wat niet gevonden is.")

WEBSITE_AGENT_PROMPT = (
    "Je onderzoekt de website en openbare bronnen van een bedrijf voor een werkingssfeeronderzoek. "
    "Zoek naar de activiteiten, producten/diensten, klanten, markten, locaties en organisatie. "
    "Geef alleen gevonden feiten als lijst in de vorm '- bevinding (bron: url)'. Verzin niets.")

USER_INPUT_AGENT_PROMPT = (
    "Je structureert aanvullende informatie die een accountant over een bedrijf heeft aangeleverd. "
    "Zet de informatie om naar losse feiten als lijst in de vorm '- bevinding (bron: gebruiker)'. "
    "Voeg niets toe dat niet in de tekst staat.")

