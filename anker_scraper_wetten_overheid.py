import requests
from bs4 import BeautifulSoup
import json
import re

def scrape_ankers(besluit_url, besluit_naam, output_json="anker_mapping.json"):
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; LegalBot/1.0)"
    }

    response = requests.get(besluit_url, headers=headers)
    if response.status_code != 200:
        print(f"Fout bij ophalen pagina: {response.status_code}")
        return

    soup = BeautifulSoup(response.text, "html.parser")

    # Zoek alle id's in tags (zoals <h2>, <a>, <div>) die Artikel bevatten
    elementen = soup.find_all(attrs={"id": re.compile("Artikel\d+\.\d+")})
    mapping = {}

    for el in elementen:
        anchor = el.get("id")
        match = re.search(r"Artikel(\d+\.\d+)", anchor)
        if match:
            artikelnummer = match.group(1)
            mapping[artikelnummer] = f"#{anchor}"

    # Sla op als JSON
    bestandsnaam = f"anker_mapping_{besluit_naam.lower()}.json"
    with open(bestandsnaam, "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)

    print(f"✓ {len(mapping)} ankers opgeslagen in: {bestandsnaam}")

# 🔧 Voorbeeldgebruik:
if __name__ == "__main__":
    besluit_naam = "bbl"
    besluit_url = "https://wetten.overheid.nl/BWBR0041297/2025-01-01"
    scrape_ankers(besluit_url, besluit_naam)
