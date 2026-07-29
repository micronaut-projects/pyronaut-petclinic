"""End-to-end tests for the PetClinic REST API and React SSR application."""

import pytest

from micronaut.runtime.server import EmbeddedServer
from pyronaut import requests
from pyronaut.test import MicronautTest, micronaut_test_fixture


@pytest.fixture
def application_context(request):
    fixture = micronaut_test_fixture(
        request,
        MicronautTest(environments=["test"], transactional=False),
    )
    yield fixture
    fixture.stop()


@pytest.fixture
def client(application_context):
    return requests.with_context(application_context)


def test_application_starts_and_ssr_routes_hydrate(client, application_context):
    assert application_context[EmbeddedServer].isRunning()
    home = client.get("/")
    assert home.status_code == 200
    assert "Welcome to PetClinic" in home.text
    assert "/static/client.js" in home.text
    assert "Micronaut" in home.text
    assert client.get("/static/css/petclinic.css").status_code == 200

    vets = client.get("/vets")
    assert "Veterinarians" in vets.text
    assert "James Carter" in vets.text
    assert "James Carter" in client.get("/vets/html").text


def test_seed_data_and_compatibility_routes(client):
    vets = client.get("/api/vets").json()
    assert len(vets) == 6
    assert any(vet["lastName"] == "Douglas" and len(vet["specialities"]) == 2 for vet in vets)
    assert client.get("/vets/json").json() == vets

    owners = client.get("/api/owners").json()
    assert any(owner["firstName"] == "George" and owner["lastName"] == "Franklin" for owner in owners)
    assert "Betty Davis" in client.get("/owners/list").text


def test_owner_search_redirect_behavior(client):
    no_match = client.get("/owners?lastName=DoesNotExist", allow_redirects=False)
    assert no_match.status_code in (301, 302, 303)
    assert no_match.headers["location"].endswith("/owners/find?notFound=true")

    one_match = client.get("/owners?lastName=Franklin", allow_redirects=False)
    assert one_match.status_code in (301, 302, 303)
    assert "/owners/" in one_match.headers["location"]

    multiple = client.get("/owners?lastName=Davis")
    assert "Betty Davis" in multiple.text
    assert "Harold Davis" in multiple.text


def test_owner_pet_visit_json_workflow(client):
    owner_response = client.post("/api/owners", json={
        "firstName": "Octavia",
        "lastName": "Butler",
        "address": "1 Patternist Way",
        "city": "Pasadena",
        "telephone": "6265551111",
    })
    assert owner_response.status_code == 201, owner_response.text
    assert owner_response.headers["location"].endswith(f"/api/owners/{owner_response.json()['id']}")
    owner = owner_response.json()

    update = client.put(f"/api/owners/{owner['id']}", json={
        **owner,
        "address": "2 Patternist Way",
        "city": "Altadena",
        "telephone": "6265552222",
    })
    assert update.status_code == 200
    assert update.json()["city"] == "Altadena"

    pet_types = client.get("/api/pet-types").json()
    dog = next(pet_type for pet_type in pet_types if pet_type["name"] == "dog")
    pet_response = client.post(f"/api/owners/{owner['id']}/pets", json={
        "name": "Lauren",
        "birthDate": "2020-01-02",
        "typeId": dog["id"],
    })
    assert pet_response.status_code == 201, pet_response.text
    pet = pet_response.json()

    pet_update = client.put(f"/api/owners/{owner['id']}/pets/{pet['id']}", json={
        "name": "Parable",
        "birthDate": "2020-01-02",
        "typeId": dog["id"],
    })
    assert pet_update.json()["name"] == "Parable"

    visit = client.post(f"/api/owners/{owner['id']}/pets/{pet['id']}/visits", json={
        "date": "2026-06-29",
        "description": "wellness check",
    })
    assert visit.status_code == 201, visit.text
    detail = client.get(f"/api/owners/{owner['id']}").json()
    assert detail["pets"][0]["visits"][0]["description"] == "wellness check"
    assert "Parable" in client.get(f"/owners/{owner['id']}").text


def test_validation_nested_ownership_and_not_found(client):
    invalid = client.post("/api/owners", json={
        "firstName": "",
        "lastName": "",
        "address": "",
        "city": "",
        "telephone": "bad",
    })
    assert invalid.status_code == 422
    body = invalid.json()
    assert body["message"] == "Validation failed"
    assert "firstName" in body["errors"]
    assert "telephone" in body["errors"]

    owners = client.get("/api/owners").json()
    owner_ids = [owner["id"] for owner in owners[:2]]
    detail = client.get(f"/api/owners/{owner_ids[0]}").json()
    if detail["pets"]:
        pet_id = detail["pets"][0]["id"]
        assert client.get(f"/api/owners/{owner_ids[1]}/pets/{pet_id}").status_code == 404

    assert client.get("/api/owners/999999").status_code == 404
    missing = client.get("/owners/999999")
    assert missing.status_code == 404
    assert "Owner not found" in missing.text
