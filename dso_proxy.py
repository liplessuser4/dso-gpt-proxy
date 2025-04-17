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

# ✅ Start de app
if __name__ == "__main__":
    app.run(debug=True, port=8080)

