from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

DSO_API_URL = "https://api.pre.omgevingswet.overheid.nl/v1/regels"
DSO_API_KEY = os.environ.get("DSO_API_KEY", "234d24da-aa7b-4007-b512-8c077d2e1acc")

@app.route("/dso/vergunningcheck", methods=["POST"])
def vergunningcheck():
    data = request.json
    locatie = data.get("locatie")
    activiteit = data.get("activiteit")

    if not locatie or not activiteit:
        return jsonify({"error": "Locatie en activiteit zijn verplicht"}), 400

    params = {
        "locatie": locatie,
        "activiteit": activiteit
    }

    headers = {
        "Authorization": f"Bearer {DSO_API_KEY}",
        "Accept": "application/json"
    }

    try:
        response = requests.get(DSO_API_URL, headers=headers, params=params)
        response.raise_for_status()
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
