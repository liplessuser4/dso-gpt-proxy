@app.route("/dso/assist", methods=["POST"])
def dso_assist():
    """
    Slimme assistent: gebruiker geeft vrije tekst ('Ik wil een dakkapel plaatsen op Oudegracht 200, Utrecht')
    Proxy doet alles: locatiehulp -> RTR -> STTR -> vergunningcheck -> indieningsvereisten
    """
    data = request.json
    vraag = data.get("vraag")

    if not vraag:
        return jsonify({"error": "Geef een vraag mee"}), 400

    try:
        # ⚡️ 1. (Demo) simpele extractie: activiteit + adres
        # TODO: hier kun je NLP toevoegen voor betere parsing
        activiteit_zoekterm = "dakkapel"  
        adres = "Oudegracht 200, Utrecht"

        # ⚡️ 2. Locatiehulp (adres → RD-coördinaten)
        loc_resp = requests.get(
            "https://service.pre.omgevingswet.overheid.nl/publiek/bepalen-locatie/api/locaties",
            headers={"x-api-key": DSO_API_KEY, "Accept": "application/hal+json"},
            params={"adres": adres}
        )
        loc_json = loc_resp.json()
        if not loc_json.get("features"):
            return jsonify({"error": "Geen locatie gevonden"}), 404
        coords = loc_json["features"][0]["geometry"]["coordinates"]  # RD (EPSG:28992)

        # ⚡️ 3. RTR → zoek activiteit
        act_resp = requests.get(
            f"{BASE_URL}/rtrgegevens/v2/activiteiten/_zoek",
            headers=HEADERS,
            params={"zoekterm": activiteit_zoekterm, "datum": "01-01-2025"}
        )
        act_json = act_resp.json()
        if not act_json.get("_embedded"):
            return jsonify({"error": "Geen activiteit gevonden"}), 404
        functioneleStructuurRef = act_json["_embedded"]["activiteiten"][0]["identificatie"]

        # ⚡️ 4. STTR ophalen (XML → JSON)
        sttr_url = f"{BASE_URL}/toepasbareregelsuitvoerengegevens/v1/{functioneleStructuurRef}"
        sttr_resp = requests.get(sttr_url, headers={**HEADERS, "Accept": "application/xml"})
        sttr_xml = sttr_resp.text
        try:
            sttr_json = xmltodict.parse(sttr_xml)
        except Exception:
            sttr_json = {"raw_xml": sttr_xml}

        # ⚡️ 5. Vergunningcheck (conclusie)
        body = {
            "functioneleStructuurRefs": [
                {"functioneleStructuurRef": functioneleStructuurRef, "antwoorden": []}
            ],
            "_geo": {"intersects": {"type": "Point", "coordinates": coords}}
        }
        check_url = f"{BASE_URL}/toepasbareregelsuitvoerenservices/v3/conclusie/_bepaal"
        check_resp = requests.post(check_url, json=body,
                                   headers={**HEADERS, "Content-Crs": "EPSG:28992"})

        # ⚡️ 6. Indieningsvereisten
        req_url = f"{BASE_URL}/toepasbareregelsuitvoerenservices/v3/indieningsvereisten/_bepaal"
        req_resp = requests.post(req_url, json=body,
                                 headers={**HEADERS, "Content-Crs": "EPSG:28992"})

        # ⚡️ 7. Alles combineren
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
