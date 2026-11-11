"""The schema-driven care export contracts shared by every database."""

from patient_test_support import patients


def test_care_summary_downloads_owner_pets_visits_and_dates(client, application_context):
    import java
    clinic = application_context.java_ctx.getBean(java.type('petclinic.services.ClinicService'))
    owner = next(o for o in clinic.find_all_owners() if o.firstName == 'Jean' and o.lastName == 'Coleman')
    owner = clinic.find_owner_by_id(owner.id)
    response = client.get(f'/owners/{owner.id}/care-summary')
    assert response.status_code == 200, response.text
    assert 'application/json' in response.headers['content-type']
    assert response.headers['content-disposition'] == f'attachment; filename="owner-{owner.id}-care-summary.json"'
    body = response.json()
    assert body['_id'] == owner.id and body['firstName'] == owner.firstName and body['lastName'] == owner.lastName
    assert body['address'] == owner.address and body['city'] == owner.city and body['telephone'] == owner.telephone
    assert '_metadata' not in body
    assert set(body) == {'_id', 'firstName', 'lastName', 'address', 'city', 'telephone', 'pets'}
    assert len(body['pets']) == len(owner.pets)
    for expected in owner.pets:
        pet = next(p for p in body['pets'] if p['id'] == expected.id)
        assert pet['name'] == expected.name and pet['birthDate'] == str(expected.birthDate)
        assert set(pet) == {'id', 'name', 'birthDate', 'visits'}
        assert len(pet['visits']) == len(expected.visits)
        for expected_visit in expected.visits:
            visit = next(v for v in pet['visits'] if v['id'] == expected_visit.id)
            assert visit == {'id': expected_visit.id, 'description': expected_visit.description, 'date': str(expected_visit.date)}
    page = client.get(f'/owners/{owner.id}')
    assert f'href="/owners/{owner.id}/care-summary"' in page.text


def test_care_summary_preserves_empty_collections_and_optional_telephone(client, patients):
    owner = patients.owner(telephone=None)
    no_pets = client.get(f'/owners/{owner.id}/care-summary')
    assert no_pets.status_code == 200, no_pets.text
    assert no_pets.json()['pets'] == [] and no_pets.json().get('telephone') is None
    pet = patients.pet(owner)
    no_visits = client.get(f'/owners/{owner.id}/care-summary')
    assert no_visits.status_code == 200, no_visits.text
    assert no_visits.json()['pets'] == [{'id': pet.id, 'name': 'Mittens', 'birthDate': '2012-09-04', 'visits': []}]


def test_care_summary_missing_owner_returns_json_not_found(client):
    response = client.get('/owners/2147483647/care-summary')
    assert response.status_code == 404
    assert response.json()['message'] == 'Entity not found.'
