# artikel_linker.py
import re

BESLUIT_URLS = {
    "Ow": "https://wetten.overheid.nl/BWBR0037885/2024-01-01",
    "Bal": "https://wetten.overheid.nl/BWBR0041330/2025-01-01",
    "Bbl": "https://wetten.overheid.nl/BWBR0041297/2025-01-01",
    "Bkl": "https://wetten.overheid.nl/BWBR0041313/2024-01-01",
}

def link_artikelen(text):
    def vervang_link(match):
        artikel = match.group(1)         # bijvoorbeeld: "5.1"
        besluit = match.group(2)         # bijvoorbeeld: "Ow"
        besluit_code = BESLUIT_URLS.get(besluit)
         if url:
            anchor = ""
            if "." in artikel:
                hoofdstuk, afdeling = artikel.split(".")
                anchor = f"#Hoofdstuk{hoofdstuk}_Afdeling{afdeling}"
            return f"[art. {artikel} {besluit}]({url}{anchor})"

        return match.group(0)

    patroon = r"art\. (\d+(?:\.\d+)?) (Ow|Bal|Bbl|Bkl)"
    return re.sub(patroon, vervang_link, text)
