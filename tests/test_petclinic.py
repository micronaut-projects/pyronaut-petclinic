"""End-to-end tests for the Pyronaut PetClinic reference app.

These tests are intentionally written as examples for new users. They show how
to start a Micronaut application context from pytest, create an HTTP client,
exercise server-side rendered pages, and verify JSON endpoints.

The Oracle database is supplied by Micronaut Test Resources according to the
test configuration, so the tests exercise the same repository and service code
used by the application.
"""

import re

import pytest

from pyronaut import requests
from pyronaut.test import MicronautTest, micronaut_test_fixture

@pytest.fixture
def application_context(request):
    """Start the Micronaut application for a pytest test.

    ``transactional=False`` keeps each HTTP request behavior close to a real
    running server instead of wrapping the entire test in one transaction.
    """

    fixture = micronaut_test_fixture(
        request,
        MicronautTest(environments=["test"], transactional=False)
    )
    yield fixture
    fixture.stop()


@pytest.fixture
def client(application_context):
    """Create a Pyronaut requests session bound to the test context."""

    return requests.with_context(application_context)


def test_application_starts(application_context):
    """The embedded server is available from the Micronaut context."""

    assert application_context.isRunning()


def test_seed_data_and_main_pages(client):
    assert "Welcome" in client.get("/").text
    css = client.get("/resources/css/petclinic.css")
    assert css.status_code == 200
    assert "text/css" in css.headers["content-type"]
    assert ".navbar" in css.text
    vets = client.get("/vets/json").json()
    assert len(vets) == 6
    assert any(vet["lastName"] == "Douglas" and len(vet["specialities"]) == 2 for vet in vets)
    owners = client.get("/owners/list").text
    assert "George Franklin" in owners
    assert "Betty Davis" in owners


def test_owner_search_flows(client):
    no_match = client.get("/owners?lastName=DoesNotExist", allow_redirects=False)
    assert no_match.status_code in (301, 302, 303)
    assert no_match.headers["location"].endswith("/owners/find?notFound=true")

    one_match = client.get("/owners?lastName=Franklin", allow_redirects=False)
    assert one_match.status_code in (301, 302, 303)
    assert "/owners/" in one_match.headers["location"]

    multiple = client.get("/owners?lastName=Davis")
    assert multiple.status_code == 200
    assert "Betty Davis" in multiple.text
    assert "Harold Davis" in multiple.text


def test_owner_pet_visit_form_flow(client):
    """Exercise the main HTML form workflow.

    This covers body binding, validation, generated mappers, database writes,
    redirects, and rendering persisted data back into HTML.
    """

    created = client.post(
        "/owners/new",
        data={
            "firstName": "Octavia",
            "lastName": "Butler",
            "address": "1 Patternist Way",
            "city": "Pasadena",
            "telephone": "6265551111",
        },
        allow_redirects=False,
    )
    assert created.status_code in (301, 302, 303), created.text
    owner_url = created.headers["location"]

    owner_page = client.get(owner_url)
    assert "Octavia Butler" in owner_page.text

    edited = client.post(
        f"{owner_url}/edit",
        data={
            "firstName": "Octavia",
            "lastName": "Butler",
            "address": "2 Patternist Way",
            "city": "Altadena",
            "telephone": "6265552222",
        },
        allow_redirects=False,
    )
    assert edited.status_code in (301, 302, 303), edited.text
    assert "Altadena" in client.get(owner_url).text

    types_page = client.get(f"{owner_url}/pets/new")
    assert "dog" in types_page.text
    assert len(re.findall(r'<option value="\d+">', types_page.text)) == 6
    dog_type_id = re.search(r'<option value="(\d+)">dog</option>', types_page.text).group(1)

    invalid_pet = client.post(
        f"{owner_url}/pets/new",
        data={"name": "", "birthDate": "", "typeId": ""},
    )
    assert invalid_pet.status_code == 200
    assert "Birth date is required" in invalid_pet.text
    assert "Pet type is required" in invalid_pet.text

    pet_created = client.post(
        f"{owner_url}/pets/new",
        data={"name": "Lauren", "birthDate": "2020-01-02", "typeId": dog_type_id},
        allow_redirects=False,
    )
    assert pet_created.status_code in (301, 302, 303), pet_created.text
    owner_with_pet = client.get(owner_url).text
    assert "Lauren" in owner_with_pet

    owner_id = owner_url.rsplit("/", 1)[-1]
    detail = client.get(owner_url).text
    pet_match = re.search(rf'/owners/{owner_id}/pets/(\d+)/edit', detail)
    assert pet_match, detail
    pet_id = pet_match.group(1)

    invalid_visit = client.post(
        f"{owner_url}/pets/{pet_id}/visits/new",
        data={"date": "", "description": ""},
    )
    assert invalid_visit.status_code == 200
    assert "Visit date is required" in invalid_visit.text

    pet_edited = client.post(
        f"{owner_url}/pets/{pet_id}/edit",
        data={"name": "Parable", "birthDate": "2020-01-02", "typeId": dog_type_id},
        allow_redirects=False,
    )
    assert pet_edited.status_code in (301, 302, 303), pet_edited.text
    assert "Parable" in client.get(owner_url).text

    visit_created = client.post(
        f"{owner_url}/pets/{pet_id}/visits/new",
        data={"date": "2026-06-29", "description": "wellness check"},
        allow_redirects=False,
    )
    assert visit_created.status_code in (301, 302, 303), visit_created.text
    assert "wellness check" in client.get(owner_url).text


def test_vets_html_and_json(client):
    html = client.get("/vets")
    assert html.status_code == 200
    assert "Veterinarians" in html.text
    assert "James Carter" in html.text

    alias = client.get("/vets/html")
    assert alias.status_code == 200
    assert "Veterinarians" in alias.text

    json_response = client.get("/vets/json")
    assert json_response.status_code == 200
    assert any(vet["firstName"] == "Helen" for vet in json_response.json())


def test_missing_owner_and_pet_paths(client):
    assert "Owner not found" in client.get("/owners/999999").text
    assert "Owner not found" in client.get("/owners/999999/pets/new").text
    assert "Pet not found" in client.get("/owners/1/pets/999999/visits/new").text


def test_jinjava_templates_render_inheritance_and_conditionals(client):
    """Jinjava renders the shared layout and Jinja control flow."""

    owners = client.get("/owners/list")
    assert owners.status_code == 200
    assert "Pet Clinic" in owners.text
    assert "George Franklin" in owners.text
    assert "$owner_count" not in owners.text
    assert "{%" not in owners.text

    not_found = client.get("/owners/list?lastName=DoesNotExist")
    assert not_found.status_code == 200
    assert "No Owners Found" in not_found.text
