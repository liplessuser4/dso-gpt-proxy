from flask import Flask, request, jsonify
import requests
import os
import xmltodict

# ✅ Maak de app
app = Flask(__name__)

# 🔑 API key uit Render environment variables
DSO_API_KEY = os.environ.get("DSO_API_KEY", "VUL_HIER_JE_KEY_IN")

# ✅ Basis headers
HEADERS = {
    "x-api-key": DSO_API_KEY,
    "Accept": "application/hal+json"
}
BASE_URL = "https://service.pre.omgevingswet.overheid.nl/publiek/toepasbare-regels/api"


# ---------------------------
# Test endpoint
# ---------------------------
@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"status": "ok", "message": "DSO Proxy draait 🚀"})


# ---------------------------
# RTR - Activiteiten zoeken
# ---------------------------
@app.route("/dso/rtr/activiteiten", methods=["POST"])
def rtr_activiteiten():
    data = request.json or {}
    zoekterm = data.get("zoekterm", "dakkapel")
    datum = data.get("datum", "01-01-2025")

    params = {"zoekterm": zoekterm, "datum": datum}

    try:
        resp = requests.get(f"{BASE_URL}/rtrgegevens/v2/activiteiten/_zoek",
                            headers=HEADERS, params=params)
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------
# STTR ophalen
# ---------------------------
@app.route("/dso/sttr", methods=["POST"])
def sttr():
    data = request.json or {}
    functionele_structuur_ref = data.get("functioneleStructuurRef")

    if not functionele_structuur_ref:
        return jsonify({"error": "functioneleStructuurRef is verplicht"}), 400

    try:
        url = f"{BASE_URL}/toepasbareregelsuitvoerengegevens/v1/{functionele_structuur_ref}"
        resp = requests.get(url, headers={**HEADERS, "Accept": "application/xml"})

        xml_data = resp.text
        try:
            json_data = xmltodict.parse(xml_data)
            return jsonify({"sttr": json_data})
        except Exception:
            return jsonify({"xml": xml_data, "waarschuwing": "XML niet naar JSON omgezet"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------
# Vergunningcheck (conclusie)
# ---------------------------
@app.route("/dso/vergunningcheck", methods=["POST"])
def vergunningcheck():
    data = request.json or {}
    functionele_structuur_ref = data.get("functioneleStructuurRef")
    coords = data.get("coords")  # RD [x, y]

    if not functionele_structuur_ref or not coords:
        return jsonify({"error": "functioneleStructuurRef en coords zijn verplicht"}), 400

    body = {
        "functioneleStructuurRefs": [
            {"functioneleStructuurRef": functionele_structuur_ref, "antwoorden": []}
        ],
        "_geo": {"intersects": {"type": "Point", "coordinates": coords}}
    }

    try:
        url = f"{BASE_URL}/toepasbareregelsuitvoerenservices/v3/conclusie/_bepaal"
        resp = requests.post(url, json=body,
                             headers={**HEADERS, "Content-Crs": "EPSG:28992"})
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------
# Indieningsvereisten
# ---------------------------
@app.route("/dso/indieningsvereisten", methods=["POST"])
def indieningsvereisten():
    data = request.json or {}
    functionele_structuur_ref = data.get("functioneleStructuurRef")
    coords = data.get("coords")  # RD [x, y]

    if not functionele_structuur_ref or not coords:
        return jsonify({"error": "functioneleStructuurRef en coords zijn verplicht"}), 400

    body = {
        "functioneleStructuurRefs": [
            {"functioneleStructuurRef": functionele_structuur_ref, "antwoorden": []}
        ],
        "_geo": {"intersects": {"type": "Point", "coordinates": coords}}
    }

    try:
        url = f"{BASE_URL}/toepasbareregelsuitvoerenservices/v3/indieningsvereisten/_bepaal"
        resp = requests.post(url, json=body,
                             headers={**HEADERS, "Content-Crs": "EPSG:28992"})
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------
# Slimme assist: alles in één call
# ---------------------------
@app.route("/dso/assist", methods=["POST"])
def dso_assist():
    """
    Gebruiker geeft alleen vrije tekst: 'Ik wil een dakkapel plaatsen op Oudegracht 200, Utrecht'
    Proxy doet alles: locatiehulp -> RTR -> STTR -> vergunningcheck -> indieningsvereisten
    """
    data = request.json or {}
    vraag = data.get("vraag")

    if not vraag:
        return jsonify({"error": "Geef een vraag mee"}), 400

    try:
        # Demo: vaste parsing (je kunt hier NLP toevoegen)
        activiteit_zoekterm = "dakkapel"
        adres = "Oudegracht 200, Utrecht"

        # 1. Locatiehulp
        loc_resp = requests.get(
            "https://service.pre.omgevingswet.overheid.nl/publiek/bepalen-locatie/api/locaties",
            headers={"x-api-key": DSO_API_KEY, "Accept": "application/hal+json"},
            params={"adres": adres}
        )
        loc_json = loc_resp.json()
        if not loc_json.get("features"):
            return jsonify({"error": "Geen locatie gevonden"}), 404
        coords = loc_json["features"][0]["geometry"]["coordinates"]  # RD [x,y]

        # 2. RTR activiteit zoeken
        act_resp = requests.get(
            f"{BASE_URL}/rtrgegevens/v2/activiteiten/_zoek",
            headers=HEADERS,
            params={"zoekterm": activiteit_zoekterm, "datum": "01-01-2025"}
        )
        act_json = act_resp.json()
        if not act_json.get("_embedded"):
            return jsonify({"error": "Geen activiteit gevonden"}), 404
        functioneleStructuurRef = act_json["_embedded"]["activiteiten"][0]["identificatie"]

        # 3. STTR ophalen
        sttr_url = f"{BASE_URL}/toepasbareregelsuitvoerengegevens/v1/{functioneleStructuurRef}"
        sttr_resp = requests.get(sttr_url, headers={**HEADERS, "Accept": "application/xml"})
        try:
            sttr_json = xmltodict.parse(sttr_resp.text)
        except Exception:
            sttr_json = {"raw_xml": sttr_resp.text}

        # 4. Vergunningcheck
        body = {
            "functioneleStructuurRefs": [
                {"functioneleStructuurRef": functioneleStructuurRef, "antwoorden": []}
            ],
            "_geo": {"intersects": {"type": "Point", "coordinates": coords}}
        }
        check_url = f"{BASE_URL}/toepasbareregelsuitvoerenservices/v3/conclusie/_bepaal"
        check_resp = requests.post(check_url, json=body,
                                   headers={**HEADERS, "Content-Crs": "EPSG:28992"})

        # 5. Indieningsvereisten
        req_url = f"{BASE_URL}/toepasbareregelsuitvoerenservices/v3/indieningsvereisten/_bepaal"
        req_resp = requests.post(req_url, json=body,
                                 headers={**HEADERS, "Content-Crs": "EPSG:28992"})

        # Combineer
        return jsonify({
            "input_vraag": vraag,
            "adres": adres,
            "coords_rd": coords,
            "activiteit": activiteit_zoekterm,
            "functioneleStructuurRef": functioneleStructuurRef,
            "sttr": sttr_json,
            "vergunningcheck": check_resp.json(),
            "indieningsvereisten": req_resp.json()
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ✅ Start lokaal (Render gebruikt gunicorn)
if __name__ == "__main__":
    app.run(debug=True, port=8080)
