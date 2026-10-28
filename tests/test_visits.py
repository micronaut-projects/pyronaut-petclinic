"""Integration checks for visits."""

import pytest
from petclinic_test_support import DATABASE

pytestmark = pytest.mark.skipif(DATABASE != 'oracle', reason='Oracle-only reference feature')

import re


def test_visit_interval_search_uses_inclusive_database_filters(client):
    page = client.get("/visits")
    assert page.status_code == 200
    assert 'id="maxFollowUpMonths"' in page.text

    search = "/visits/search?fromDate=2026-01-01&toDate=2026-01-31"
    response = client.get(search + "&maxDurationMinutes=30&maxFollowUpMonths=6")
    assert response.status_code == 200, response.text
    visits = response.json()
    assert sorted([(v["date"], v["petName"], v["durationInMinutes"], v["periodInMonths"]) for v in visits], reverse=True) == [
        ("2026-01-09", "Max", 15, 3),
        ("2026-01-05", "Samantha", 30, 6),
    ]
    assert all(v["ownerName"] == "Jean Coleman" for v in visits)

    exact_date = client.get("/visits/search?fromDate=2026-01-05&toDate=2026-01-05&maxDurationMinutes=30&maxFollowUpMonths=6")
    assert len(exact_date.json()) == 1
    assert exact_date.json()[0]["petName"] == "Samantha"
    narrower = client.get(search + "&maxDurationMinutes=15&maxFollowUpMonths=3").json()
    assert len(narrower) == 1 and narrower[0]["petName"] == "Max"

    default_bounds = client.get(search).json()
    assert sorted([v["date"] for v in default_bounds], reverse=True) == ["2026-01-15", "2026-01-12", "2026-01-09", "2026-01-05"]


def test_visit_interval_json_creation_matches_reference_pet_lookup(client):
    details = client.get("/owners/1").text
    pet_id = re.search(r'/owners/1/pets/(\d+)/edit', details).group(1)
    url = f"/owners/1/pets/{pet_id}/visits/new"
    data = {"date": "2031-02-03", "description": "Interval follow-up <check>", "durationMinutes": 45, "followUpPeriodMonths": 15}

    invalid = client.post(url, json={**data, "durationMinutes": 0}, allow_redirects=False)
    assert invalid.status_code == 400, invalid.text
    assert "durationMinutes" in invalid.json()["errors"]
    # The reference resolves the pet independently of ownerId, including these URLs.
    assert client.get(f"/owners/2/pets/{pet_id}/edit").status_code == 200
    assert client.get(f"/owners/2/pets/{pet_id}/visits/new").status_code == 200
    created = client.post(f"/owners/2/pets/{pet_id}/visits/new", json=data, allow_redirects=False)
    assert created.status_code in (301, 302, 303), created.text
    assert created.headers['location'].endswith('/owners/2')
    assert "Interval follow-up &lt;check&gt;" in client.get("/owners/1").text
    search = "/visits/search?fromDate=2031-02-03&toDate=2031-02-03&maxDurationMinutes=45&maxFollowUpMonths=15"
    reloaded = client.get(search).json()
    assert len(reloaded) == 1
    assert reloaded[0]["durationInMinutes"] == 45
    assert reloaded[0]["periodInMonths"] == 15
    assert reloaded[0]["description"] == data["description"]
    assert client.get(search.replace("maxDurationMinutes=45", "maxDurationMinutes=44")).json() == []
    assert client.get(search.replace("maxFollowUpMonths=15", "maxFollowUpMonths=14")).json() == []


def test_visit_search_matches_reference_criteria_behavior(client):
    invalid = client.get('/visits/search?fromDate=2026-02-30&toDate=2026-12-31')
    assert invalid.status_code == 400, invalid.text
    for query in (
        "fromDate=2026-12-31&toDate=2026-01-01",
        "fromDate=2026-01-01&toDate=2026-12-31&maxDurationMinutes=0",
        "fromDate=2026-01-01&toDate=2026-12-31&maxFollowUpMonths=-1",
    ):
        response = client.get("/visits/search?" + query)
        assert response.status_code == 200, response.text
        assert response.json() == []
