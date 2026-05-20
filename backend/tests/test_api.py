"""
Integration tests for the NexGenIQ backend API.

These exercise the API surface end to end through FastAPI's TestClient:
health, auth, the trait library, index building, sensitivity, CSV import,
and authorisation enforcement.
"""

import io


# --- meta / health ---------------------------------------------------------
def test_health(client):
    """The health endpoint reports the app and engine versions."""
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "osit-index" in body["engine"]


# --- auth ------------------------------------------------------------------
def test_register_and_login(client):
    """A user can register and then obtain a token."""
    r = client.post("/api/v1/auth/register", json={
        "email": "alice@example.com", "password": "password123",
        "full_name": "Alice", "role": "producer"})
    assert r.status_code == 201

    r = client.post("/api/v1/auth/token", data={
        "username": "alice@example.com", "password": "password123"})
    assert r.status_code == 200
    assert r.json()["token_type"] == "bearer"


def test_duplicate_registration_rejected(client):
    """Registering the same email twice is a 409 conflict."""
    payload = {"email": "bob@example.com", "password": "password123",
               "role": "producer"}
    assert client.post("/api/v1/auth/register", json=payload).status_code \
        == 201
    assert client.post("/api/v1/auth/register", json=payload).status_code \
        == 409


def test_bad_login_rejected(client):
    """Wrong credentials are rejected with 401."""
    r = client.post("/api/v1/auth/token", data={
        "username": "nobody@example.com", "password": "wrong"})
    assert r.status_code == 401


def test_unknown_role_rejected(client):
    """Registering with an unrecognised role is rejected."""
    r = client.post("/api/v1/auth/register", json={
        "email": "x@example.com", "password": "password123",
        "role": "wizard"})
    assert r.status_code == 422


# --- library ---------------------------------------------------------------
def test_traits_require_auth(client):
    """The trait list is behind authentication."""
    assert client.get("/api/v1/library/traits").status_code == 401


def test_trait_registry(client, auth_headers):
    """The trait registry returns the expected beef traits."""
    r = client.get("/api/v1/library/traits", headers=auth_headers)
    assert r.status_code == 200
    codes = {t["code"] for t in r.json()}
    assert {"WW", "CED", "STAY", "MARB", "CW"} <= codes


def test_consensus_parameters(client, auth_headers):
    """The consensus parameter set is returned with citations."""
    r = client.get("/api/v1/library/parameter-set/consensus",
                    headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["version"]
    assert body["traits"]["WW"]["citation"]


# --- index build -----------------------------------------------------------
def test_build_requires_auth(client, sample_index_request):
    """Building an index without a token is rejected."""
    r = client.post("/api/v1/index/build", json=sample_index_request)
    assert r.status_code == 401


def test_build_index(client, auth_headers, sample_index_request):
    """A valid index build returns a ranked, validated result + ledger."""
    r = client.post("/api/v1/index/build", json=sample_index_request,
                     headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert len(body["scores"]) == 2
    assert body["scores"][0]["rank"] == 1
    assert body["ledger_id"]
    # Every score carries a plain-language explanation.
    assert all(s["explanation"] for s in body["scores"])


def test_build_index_handworked_value(client, auth_headers,
                                      sample_index_request):
    """The economic-weight index value matches the hand calculation.

    AAA-1842: 72*0.85 + 14*12 + 22*6.4 = 370.0.
    """
    r = client.post("/api/v1/index/build", json=sample_index_request,
                     headers=auth_headers)
    top = next(s for s in r.json()["scores"]
               if s["animal_id"] == "AAA-1842")
    assert abs(top["index_value"] - 370.0) < 1e-6


def test_build_index_validation_error(client, auth_headers):
    """An empty goal yields ok=False with an error in the validation list."""
    bad = {"goal": {"name": "empty", "basis": "per_cow_exposed",
                    "components": []},
           "animals": [], "mode": "economic_weight"}
    r = client.post("/api/v1/index/build", json=bad, headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is False
    assert any(v["severity"] == "error" for v in body["validation"])


def test_sensitivity(client, auth_headers, sample_index_request):
    """Sensitivity analysis returns a summary and one entry per trait."""
    req = {**sample_index_request, "variation": 0.2}
    r = client.post("/api/v1/index/sensitivity", json=req,
                     headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["summary"]
    assert len(body["entries"]) == 3


# --- CSV import ------------------------------------------------------------
def test_csv_inspect_and_parse(client, auth_headers):
    """A CSV can be inspected for a column mapping then parsed to animals."""
    csv_text = (
        "Reg #,Breed,WW EPD,WW Acc,CED EPD,CED Acc\n"
        "AAA-1,Angus,72,0.85,14,0.70\n"
        "AAA-2,Angus,60,0.80,8,0.65\n"
    )
    files = {"file": ("sale.csv", io.BytesIO(csv_text.encode()),
                      "text/csv")}
    r = client.post("/api/v1/import/inspect", files=files,
                     headers=auth_headers)
    assert r.status_code == 200
    insp = r.json()
    assert insp["row_count"] == 2
    detected = {c["source_column"]: c["target_field"]
                for c in insp["columns"]}
    assert detected["Reg #"] == "animal_id"
    assert detected["WW EPD"] == "WW"
    assert detected["WW Acc"] == "WW_acc"

    import json
    files = {"file": ("sale.csv", io.BytesIO(csv_text.encode()),
                      "text/csv")}
    r = client.post(
        "/api/v1/import/parse",
        files=files,
        data={"mapping_json": json.dumps(detected)},
        headers=auth_headers,
    )
    assert r.status_code == 200
    parsed = r.json()
    assert parsed["animal_count"] == 2
    a1 = next(a for a in parsed["animals"]
              if a["animal_id"] == "AAA-1")
    ww = next(e for e in a1["epds"] if e["trait_code"] == "WW")
    assert ww["value"] == 72.0
    assert ww["bif_accuracy"] == 0.85


# --- herd simulation (Milestone 2) ----------------------------------------
def _sim_request():
    """A small, fast MEV-derivation request body."""
    return {
        "production_system": {
            "name": "Test herd", "herd_size": 100,
            "conception_rate": 0.92, "calving_loss_rate": 0.06,
            "replacement_rate": 0.18, "heifer_retention": True,
            "cow_breed_composition": [
                {"fraction": 1.0, "breeds": {"Angus": 1.0}}],
            "bull_breed_composition": [
                {"fraction": 1.0, "breeds": {"Angus": 1.0}}],
        },
        "economic_scenario": {
            "name": "Weaning", "sale_endpoint": "weaning",
            "price_bands": [
                {"sex": "S", "low": 0, "high": 9999,
                 "price_per_cwt": 195},
                {"sex": "F", "low": 0, "high": 9999,
                 "price_per_cwt": 178},
            ],
            "cull_cow_price_per_cwt": 110, "aum_cost": 38,
            "fixed_cost_per_cow": 180, "discount_rate": 0.06,
        },
        "controls": {
            "burn_in_years": 3, "planning_horizon_years": 5,
            "replicates": 3, "seed": 20260520,
        },
        "traits": ["WW", "CED", "MW"],
    }


def test_simulation_requires_auth(client):
    """The MEV-derivation endpoint is behind authentication."""
    r = client.post("/api/v1/simulation/derive-mevs",
                     json=_sim_request())
    assert r.status_code == 401


def test_derive_mevs(client, auth_headers):
    """A herd simulation derives an MEV for each requested trait."""
    r = client.post("/api/v1/simulation/derive-mevs",
                     json=_sim_request(), headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert {m["trait_code"] for m in body["mevs"]} == {"WW", "CED", "MW"}
    assert body["replicates"] == 3


def test_derived_mevs_have_correct_signs(client, auth_headers):
    """End to end through the API: weaning weight is positively valued
    and mature cow weight is negatively valued."""
    r = client.post("/api/v1/simulation/derive-mevs",
                     json=_sim_request(), headers=auth_headers)
    by_code = {m["trait_code"]: m["mev"] for m in r.json()["mevs"]}
    assert by_code["WW"] > 0
    assert by_code["MW"] < 0


def test_derived_mevs_feed_an_index(client, auth_headers):
    """The integration seam: MEVs derived by the simulation are used as
    the economic weights of an index build, end to end."""
    sim = client.post("/api/v1/simulation/derive-mevs",
                       json=_sim_request(), headers=auth_headers).json()
    components = [
        {"trait_code": m["trait_code"], "economic_weight": m["mev"]}
        for m in sim["mevs"]
    ]
    index_req = {
        "goal": {"name": "Simulation-derived index",
                 "basis": "per_cow_exposed",
                 "components": components, "source": "simulation"},
        "animals": [
            {"animal_id": "A-1", "breed": "Angus",
             "epds": [{"trait_code": "WW", "value": 60,
                       "bif_accuracy": 0.8},
                      {"trait_code": "CED", "value": 10,
                       "bif_accuracy": 0.7},
                      {"trait_code": "MW", "value": 20,
                       "bif_accuracy": 0.6}]},
            {"animal_id": "A-2", "breed": "Angus",
             "epds": [{"trait_code": "WW", "value": 40,
                       "bif_accuracy": 0.8},
                      {"trait_code": "CED", "value": 6,
                       "bif_accuracy": 0.7},
                      {"trait_code": "MW", "value": 50,
                       "bif_accuracy": 0.6}]},
        ],
        "mode": "economic_weight",
    }
    r = client.post("/api/v1/index/build", json=index_req,
                     headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["ok"] is True
    assert len(r.json()["scores"]) == 2
