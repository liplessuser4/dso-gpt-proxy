from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# Zet hier je DSO API key (of gebruik Render environment variable)
DSO_API_KEY = os.environ.get("DSO_API_KEY", "234d24da-aa7b-4007-b512-8c077d2e1acc")

HEADERS = {
    "Authorization": f"Bearer {DSO_API_KEY}",
    "Accept": "application/json"
}

# 1️⃣ Regels op de kaart / Vergunningcheck
@app.route("/dso/vergunningcheck", methods=["POST"])
def vergunningcheck():
    data = request.json
    locatie = data.get("locatie")
    activiteit = data.get("activiteit")

    if not locatie or not activiteit:
        return jsonify({"error": "locatie en activiteit zijn verplicht"}), 400

    try:
        response = requests.get(
            "https://api.pre.omgevingswet.overheid.nl/v1/regels",
            headers=HEADERS,
            params={"locatie": locatie, "activiteit": activiteit}
        )
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

# 2️⃣ Bevoegd gezag
@app.route("/dso/bevoegdgezag", methods=["POST"])
def bevoegd_gezag():
    data = request.json
    locatie = data.get("locatie")
    activiteit = data.get("activiteit")

    if not locatie or not activiteit:
        return jsonify({"error": "locatie en activiteit zijn verplicht"}), 400

    try:
        response = requests.get(
            "https://api.pre.omgevingswet.overheid.nl/v1/bevoegdgezag",
            headers=HEADERS,
            params={"locatie": locatie, "activiteit": activiteit}
        )
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

# 3️⃣ Indieningsvereisten
@app.route("/dso/indieningsvereisten", methods=["POST"])
def indieningsvereisten():
    data = request.json
    activiteit = data.get("activiteit")

    if not activiteit:
        return jsonify({"error": "activiteit is verplicht"}), 400

    try:
        response = requests.get(
            "https://api.pre.omgevingswet.overheid.nl/v1/formulieren/aanvraagvereisten",
            headers=HEADERS,
            params={"activiteit": activiteit}
        )
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

# 4️⃣ Activiteitenzoeker
@app.route("/dso/activiteitenzoeker", methods=["POST"])
def activiteitenzoeker():
    data = request.json
    zoekterm = data.get("zoekterm")

    if not zoekterm:
        return jsonify({"error": "zoekterm is verplicht"}), 400

    try:
        response = requests.get(
            "https://api.pre.omgevingswet.overheid.nl/v1/activiteiten",
            headers=HEADERS,
            params={"zoekterm": zoekterm}
        )
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

# 5️⃣ Locatiehulp
@app.route("/dso/locatiehulp", methods=["POST"])
def locatiehulp():
    data = request.json
    adres = data.get("adres")

    if not adres:
        return jsonify({"error": "adres is verplicht"}), 400

    try:
        response = requests.get(
            "https://api.pre.omgevingswet.overheid.nl/v1/locaties",
            headers=HEADERS,
            params={"adres": adres}
        )
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

# 6️⃣ STTR vragenboom ophalen en omzetten naar JSON
@app.route("/dso/sttr", methods=["POST"])
def sttr_vragenboom():
    data = request.json
    activiteit_id = data.get("activiteit_id")

    if not activiteit_id:
        return jsonify({"error": "activiteit_id is verplicht"}), 400

    try:
        response = requests.get(
            "https://api.pre.omgevingswet.overheid.nl/v1/toepasbare-regels",
            headers=HEADERS,
            params={"activiteitId": activiteit_id}
        )

        if response.status_code != 200:
            return jsonify({"error": "Kon STTR-bestand niet ophalen"}), 500

        xml_data = response.text
        try:
            json_data = xmltodict.parse(xml_data)
            return jsonify({"sttr": json_data})
        except Exception as parse_error:
            return jsonify({
                "xml": xml_data,
                "waarschuwing": "XML kon niet omgezet worden naar JSON",
                "fout": str(parse_error)
            })
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

# 7️⃣ RTR Gegevens raadplegen: Activiteiten en Werkzaamheden
@app.route("/dso/rtr/activiteiten", methods=["GET"])
def rtr_activiteiten():
    try:
        response = requests.get(
            "https://service.pre.omgevingswet.overheid.nl/publiek/toepasbare-regels/api/rtrgegevens/v2/activiteiten",
            headers={"x-api-key": DSO_API_KEY}
        )
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

@app.route("/dso/rtr/werkzaamheden", methods=["GET"])
def rtr_werkzaamheden():
    try:
        response = requests.get(
            "https://service.pre.omgevingswet.overheid.nl/publiek/toepasbare-regels/api/rtrgegevens/v2/werkzaamheden",
            headers={"x-api-key": DSO_API_KEY}
        )
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

# ✅ Start de app
if __name__ == "__main__":
    app.run(debug=True, port=8080)
