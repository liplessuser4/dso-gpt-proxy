from bs4 import BeautifulSoup
import requests
import json
import re

BESLUITEN = {
    "ow": "https://wetten.overheid.nl/BWBR0037885/2024-01-01",
    "bal": "https://wetten.overheid.nl/BWBR0041330/2025-01-01",
    "bbl": "https://wetten.overheid.nl/BWBR0041297/2025-01-01",
    "bkl": "https://wetten.overheid.nl/BWBR0041313/2024-01-01",
}

def scrape_ankers(besluit_url, besluit_naam):
    print(f"🔍 Scraping {besluit_naam}")
    r = requests.get(besluit_url, headers={"User-Agent": "LegalScraper/1.0"})
    if r.status_code != 200:
        print(f"❌ Fout bij ophalen {besluit_url}")
        return
    soup = BeautifulSoup(r.text, "html.parser")
    elementen = soup.find_all(attrs={"id": re.compile(r"Artikel\d+\.\d+")})
    mapping = {}
    for el in elementen:
        id_ = el.get("id")
        match = re.search(r"Artikel(\d+\.\d+)", id_)
        if match:
            mapping[match.group(1)] = f"#{id_}"
    with open(f"anker_mapping_{besluit_naam}.json", "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2)
    print(f"✅ anker_mapping_{besluit_naam}.json opgeslagen")

def update_alle_besluiten():
    for naam, url in BESLUITEN.items():
        scrape_ankers(url, naam)

if __name__ == "__main__":
    update_alle_besluiten()

