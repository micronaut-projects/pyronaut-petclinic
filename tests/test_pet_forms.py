"""Pet validation preserves route context and rejects invalid forms without writes."""

import re
import pytest


@pytest.mark.parametrize('editing', [False, True])
def test_invalid_pet_form_preserves_owner_values_and_route(client, application_context, editing):
    import java
    service = application_context.java_ctx.getBean(java.type('petclinic.services.ClinicService'))
    pet = service.find_all_pets()[0]
    owner_id = pet.owner.id
    action = f'/owners/{owner_id}/pets/{pet.id}/edit' if editing else f'/owners/{owner_id}/pets/new'
    selected_type = next(t for t in service.find_pet_types() if t.id != pet.type.id)
    response = client.post(action + '?ownerId=2147483647&petId=2147483647', data={'id': '2147483647', 'name': '', 'birthDate': '2024-02-03',
                          'typeId': str(selected_type.id)}, allow_redirects=False)
    assert response.status_code == 400, response.text
    assert 'text/html' in response.headers['content-type']
    assert f'action="{action}"' in response.text
    assert 'value="2024-02-03"' in response.text
    assert re.search(r'<option value="' + str(selected_type.id) + r'"\s+selected', response.text)
    assert pet.owner.firstName in response.text
    unchanged = service.find_pet_by_id(pet.id)
    assert unchanged.name == pet.name and str(unchanged.birthDate) == str(pet.birthDate)
    assert unchanged.type.id == pet.type.id
    assert 'value="2147483647"' not in response.text


def test_invalid_pet_for_missing_owner_renders_not_found(client):
    response = client.post('/owners/2147483647/pets/new', data={
        'name': '', 'birthDate': '2024-02-03', 'typeId': '1'})
    assert response.status_code == 404, response.text
    assert 'text/html' in response.headers['content-type']


def test_visit_routes_require_the_pets_owner(client, application_context):
    import java
    service = application_context.java_ctx.getBean(java.type('petclinic.services.ClinicService'))
    pet = service.find_all_pets()[0]
    wrong_owner = next(o for o in service.find_all_owners() if o.id != pet.owner.id)
    path = f'/owners/{wrong_owner.id}/pets/{pet.id}/visits/new'
    before = len(service.find_visits_by_pet_id(pet.id))
    assert client.get(path).status_code == 404
    response = client.post(path, json={'date': '2026-11-11', 'description': 'Wrong owner',
                           'durationMinutes': 30, 'followUpPeriodMonths': 6}, allow_redirects=False)
    assert response.status_code == 404, response.text
    assert response.json()['message'] == 'Entity not found.'
    assert len(service.find_visits_by_pet_id(pet.id)) == before


def test_invalid_edit_of_missing_pet_still_preserves_validation_context(client):
    path = '/owners/1/pets/2147483647/edit'
    response = client.post(path, data={'name': '', 'birthDate': '2024-02-03', 'typeId': '1'})
    assert response.status_code == 400, response.text
    assert 'text/html' in response.headers['content-type']
    assert f'action="{path}"' in response.text
    assert 'value="2024-02-03"' in response.text
