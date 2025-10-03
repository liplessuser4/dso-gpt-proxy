from __future__ import annotations

import os
from flask import Flask, request, jsonify
import requests
import xmltodict

# ---------------------------------------------------------------------------
# Configuratie
# ---------------------------------------------------------------------------

DEFAULT_BASE_URL = (
    "https://service.pre.omgevingswet.overheid.nl/publiek/toepasbare-regels/api"
)

DSO_API_KEY: str = os.environ.get(
    "DSO_API_KEY", "234d24da-aa7b-4007-b512-8c077d2e1acc"
)
BASE_URL: str = os.environ.get("DSO_BASE_URL", DEFAULT_BASE_URL)

HEADERS: dict[str, str] = {
    "x-api-key": DSO_API_KEY,
    "Accept": "application/hal+json",
}

DEFAULT_DATUM: str = os.environ.get("DSO_DEFAULT_DATUM", "01-01-2025")

# ---------------------------------------------------------------------------
# Flask app
# ---------------------------------------------------------------------------

app = Flask(__name__)

@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"status": "ok", "message": "DSO Proxy draait 🚀"})

@app.route("/dso/rtr/activiteiten", methods=["GET", "POST"])
def rtr_activiteiten() -> tuple[object, int]:
    # In POST lezen we JSON; in GET lezen we querystring.
    data = request.get_json(silent=True) or {} if request.method == "POST" else request.args or {}
    zoekterm: str = data.get("zoekterm", "dakkapel")
    datum: str = data.get("datum", DEFAULT_DATUM)
    params = {"zoekterm": zoekterm, "datum": datum}

    try:
        resp = requests.get(
            f"{BASE_URL}/rtrgegevens/v2/activiteiten",
            headers=HEADERS,
            params=params,
            timeout=30,
        )
        if resp.status_code != 200:
            return jsonify({"error": resp.text, "status": resp.status_code}), resp.status_code
        return jsonify(resp.json())
    except requests.exceptions.RequestException as exc:
        return jsonify({"error": str(exc)}), 500

@app.route("/dso/sttr", methods=["POST"])
def sttr() -> tuple[object, int]:
    data = request.get_json(silent=True) or {}
    functionele_structuur_ref: str | None = data.get("functioneleStructuurRef")
    if not functionele_structuur_ref:
        return jsonify({"error": "functioneleStructuurRef is verplicht"}), 400

    # Wanneer de ref al een volledige URL is (urn of https), gebruik die direct.
    if functionele_structuur_ref.lower().startswith("http"):
        sttr_url = functionele_structuur_ref
    else:
        sttr_url = f"{BASE_URL}/toepasbareregelsuitvoerengegevens/v1/{functionele_structuur_ref}"

    try:
        xml_headers = {**HEADERS, "Accept": "application/xml"}
        resp = requests.get(sttr_url, headers=xml_headers, timeout=30)
        if resp.status_code != 200:
            return jsonify({"error": resp.text, "status": resp.status_code}), resp.status_code
        xml_data: str = resp.text
        try:
            json_data = xmltodict.parse(xml_data)
            return jsonify({"sttr": json_data})
        except Exception:
            return jsonify({"xml": xml_data, "warning": "XML not parsed to JSON"})
    except requests.exceptions.RequestException as exc:
        return jsonify({"error": str(exc)}), 500

def _build_execution_body(functionele_structuur_ref: str, coords: list[float]) -> dict:
    return {
        "functioneleStructuurRefs": [
            {
                "functioneleStructuurRef": functionele_structuur_ref,
                "antwoorden": [],
            }
        ],
        "_geo": {
            "intersects": {
                "type": "Point",
                "coordinates": coords,
            }
        },
    }

@app.route("/dso/vergunningcheck", methods=["POST"])
def vergunningcheck() -> tuple[object, int]:
    data = request.get_json(silent=True) or {}
    functionele_structuur_ref: str | None = data.get("functioneleStructuurRef")
    coords: list | None = data.get("coords")
    if not functionele_structuur_ref or not coords:
        return jsonify({"error": "functioneleStructuurRef en coords zijn verplicht"}), 400

    body = _build_execution_body(functionele_structuur_ref, coords)

    try:
        resp = requests.post(
            f"{BASE_URL}/toepasbareregelsuitvoerenservices/v3/conclusie/_bepaal",
            json=body,
            headers={**HEADERS, "Content-Crs": "EPSG:28992"},
            timeout=30,
        )
        if resp.status_code != 200:
            return jsonify({"error": resp.text, "status": resp.status_code}), resp.status_code
        return jsonify(resp.json())
    except requests.exceptions.RequestException as exc:
        return jsonify({"error": str(exc)}), 500

@app.route("/dso/indieningsvereisten", methods=["POST"])
def indieningsvereisten() -> tuple[object, int]:
    data = request.get_json(silent=True) or {}
    functionele_structuur_ref: str | None = data.get("functioneleStructuurRef")
    coords: list | None = data.get("coords")
    if not functionele_structuur_ref or not coords:
        return jsonify({"error": "functioneleStructuurRef en coords zijn verplicht"}), 400

    body = _build_execution_body(functionele_structuur_ref, coords)

    try:
        resp = requests.post(
            f"{BASE_URL}/toepasbareregelsuitvoerenservices/v3/indieningsvereisten/_bepaal",
            json=body,
            headers={**HEADERS, "Content-Crs": "EPSG:28992"},
            timeout=30,
        )
        if resp.status_code != 200:
            return jsonify({"error": resp.text, "status": resp.status_code}), resp.status_code
        return jsonify(resp.json())
    except requests.exceptions.RequestException as exc:
        return jsonify({"error": str(exc)}), 500

if __name__ == "__main__":
    port_str = os.environ.get("PORT", "8080")
    try:
        port = int(port_str)
    except ValueError:
        port = 8080
    app.run(debug=True, host="0.0.0.0", port=port)

