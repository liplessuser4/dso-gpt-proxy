# artikel_linker.py
import re

BESLUIT_URLS = {
    "Ow": "BWBR0037885",     # Omgevingswet
    "Bal": "BWBR0041330",    # Besluit activiteiten leefomgeving
    "Bbl": "BWBR0041297",    # Besluit bouwwerken leefomgeving
    "Bkl": "BWBR0041313",    # Besluit kwaliteit leefomgeving
}

def link_artikelen(text):
    def vervang_link(match):
        artikel = match.group(1)
        besluit = match.group(2)
        besluit_code = BESLUIT_URLS.get(besluit)
        if besluit_code:
            url = f"https://wetten.overheid.nl/jci1.3:{besluit_code}&z=2024-01-01&g=2024-01-01"
            return f"[art. {artikel} {besluit}]({url})"
        return match.group(0)
    
    patroon = r"art\. (\d+(?:\.\d+)?) (Ow|Bal|Bbl|Bkl)"
    return re.sub(patroon, vervang_link, text)
