"""Integration checks for owners."""

import re
from petclinic_test_support import _reference_http


def test_owner_search_flows(client, application_context):
    no_match = client.get("/owners?lastName=DoesNotExist", allow_redirects=False)
    assert no_match.status_code in (301, 302, 303)
    assert no_match.headers["location"].endswith("/owners/find?notFound=true")

    one_match = client.get("/owners?lastName=Franklin", allow_redirects=False)
    assert one_match.status_code in (301, 302, 303)
    assert "/owners/" in one_match.headers["location"]

    multiple = client.get("/owners?lastName=Davis")
    assert multiple.status_code == 200
    assert 'application/json' in multiple.headers['content-type']
    actual = multiple.json()
    expected = _reference_http(application_context)['ownersDavis']
    assert actual['lastName'] == expected['lastName']
    # The source orders only by lastName; tied Davis rows need not match H2 order on Oracle.
    assert sorted(actual['owners'], key=lambda owner: owner['id']) == sorted(expected['owners'], key=lambda owner: owner['id'])


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
    assert "Pet type is required" in invalid_pet.text, invalid_pet.text

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
        json={"date": "", "description": ""},
    )
    assert invalid_visit.status_code == 400
    assert "date" in invalid_visit.json()['errors']

    pet_edited = client.post(
        f"{owner_url}/pets/{pet_id}/edit",
        data={"name": "Parable", "birthDate": "2020-01-02", "typeId": dog_type_id},
        allow_redirects=False,
    )
    assert pet_edited.status_code in (301, 302, 303), pet_edited.text
    assert "Parable" in client.get(owner_url).text

    visit_created = client.post(
        f"{owner_url}/pets/{pet_id}/visits/new",
        json={"date": "2026-06-29", "description": "wellness check", "durationMinutes": 30, "followUpPeriodMonths": 6},
        allow_redirects=False,
    )
    assert visit_created.status_code in (301, 302, 303), visit_created.text
    assert "wellness check" in client.get(owner_url).text


def test_missing_owner_and_pet_paths(client):
    for path in ('/owners/999999', '/owners/999999/pets/new', '/owners/1/pets/999999/visits/new', '/does-not-exist'):
        response = client.get(path)
        assert response.status_code == 404, response.text
        assert '404' in response.text
