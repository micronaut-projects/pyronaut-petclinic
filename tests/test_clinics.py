"""Integration checks for clinics."""



def test_clinic_spatial_queries_and_boolean_filters(client):
    page = client.get("/clinics")
    assert page.status_code == 200, page.text
    assert 'id="clinic-search-form"' in page.text
    assert "clinic-map" in page.text
    origin = {"longitude": -89.3840, "latitude": 43.0745, "radiusMeters": 350}
    nearby = client.post("/clinics/nearby", json=origin)
    assert nearby.status_code == 200, nearby.text
    assert {c["name"] for c in nearby.json()} == {"Downtown Madison Pet Clinic", "Capitol Square Pet Clinic"}
    expanded = client.post("/clinics/nearby", json={**origin, "radiusMeters": 5000, "acceptingNewPatients": True, "emergencyService": True})
    assert expanded.status_code == 200, expanded.text
    assert all(c["acceptingNewPatients"] and c["emergencyService"] for c in expanded.json())
    assert {c["name"] for c in expanded.json()} >= {"Downtown Madison Pet Clinic", "East Madison Pet Clinic"}

    polygon = [{"latitude": 43.00, "longitude": -89.55}, {"latitude": 43.20, "longitude": -89.55},
               {"latitude": 43.20, "longitude": -89.20}, {"latitude": 43.00, "longitude": -89.20}]
    within = client.post("/clinics/within", json={"coordinates": polygon, "acceptingNewPatients": False})
    assert within.status_code == 200, within.text
    names = {c["name"] for c in within.json()}
    assert {"University Pet Clinic", "South Madison Pet Clinic"} <= names
    assert "Downtown Madison Pet Clinic" not in names
    assert all(not c["acceptingNewPatients"] for c in within.json())

    line = [{"latitude": 43.0650, "longitude": -89.5500}, {"latitude": 43.1100, "longitude": -89.3300},
            {"latitude": 43.1900, "longitude": -89.2000}]
    intersects = client.post("/clinics/intersects", json={"coordinates": line})
    assert intersects.status_code == 200, intersects.text
    names = {c["name"] for c in intersects.json()}
    assert {"West Madison Pet Clinic", "East Madison Pet Clinic", "Sun Prairie Pet Clinic"} <= names
    assert "Downtown Madison Pet Clinic" not in names


def test_clinic_search_rejects_invalid_geometry(client):
    for endpoint, data in (
        ("nearby", {"longitude": -89.38, "latitude": 91, "radiusMeters": 500}),
        ("nearby", {"longitude": -89.38, "latitude": 43.07, "radiusMeters": 0}),
        ("within", {"coordinates": []}),
        ("intersects", {"coordinates": [{"latitude": 43, "longitude": -89}]}),
        ("within", {"coordinates": [{"latitude": 43.0, "longitude": -89.5}, {"latitude": 43.2, "longitude": -89.2},
                                    {"latitude": 43.2, "longitude": -89.5}, {"latitude": 43.0, "longitude": -89.2}]}),
    ):
        response = client.post("/clinics/" + endpoint, json=data)
        assert response.status_code == 400, response.text
