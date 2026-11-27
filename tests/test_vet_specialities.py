"""Speciality CRUD, assignments and forms from the Java VetCrudTest."""

import pytest

from petclinic_test_support import assert_json_error


def test_vet_speciality_multiple_assignments_and_shared_delete(client, vet_api):
    first, second = vet_api.speciality(), vet_api.speciality()
    created = vet_api.create([first, second])
    other = vet_api.create([first]).json()
    assert sorted(created.json()['specialities'], key=lambda s: s['id']) == sorted([first, second], key=lambda s: s['id'])
    deleted = client.delete('/vets/' + str(created.json()['id']), headers={'If-Match': created.headers['etag']})
    assert deleted.status_code == 204 and not deleted.text
    assert 'location' not in deleted.headers
    assert client.get('/vets/' + str(other['id'])).json()['specialities'] == [first]
    assert first in client.get('/vets/specialities/json').json()
    assert second in client.get('/vets/specialities/json').json()


def test_vet_speciality_rename_preserves_links_and_does_not_change_assignment_etag(client, vet_api):
    speciality = vet_api.speciality()
    vet = vet_api.create([speciality]).json()
    url = '/vets/specialities/' + str(speciality['id'])
    assert client.put(url, json=speciality).json() == speciality
    renamed = {**speciality, 'name': speciality['name'] + ' renamed'}
    response = client.put(url, json=renamed)
    assert response.status_code == 200 and response.json() == renamed
    current = client.get('/vets/' + str(vet['id'])).json()
    assert current['specialities'] == [renamed] and current['etag'] == vet['etag']
    saved = client.put('/vets/' + str(vet['id']), json={'firstName': 'Updated', 'lastName': vet['lastName'],
        'specialityIds': [speciality['id']]}, headers={'If-Match': vet['etag']})
    assert saved.status_code == 200 and saved.json()['specialities'] == [renamed]
    assert renamed in client.get('/vets/specialities/json').json()


def test_vet_speciality_rejects_duplicate_create_and_rename(client, vet_api):
    first, second = vet_api.speciality(), vet_api.speciality()
    duplicate = client.post('/vets/specialities', json=first)
    assert_json_error(duplicate, 400)
    assert duplicate.json()['message'] == 'Speciality name already exists.'
    renamed = client.put('/vets/specialities/' + str(second['id']), json={**second, 'name': first['name']})
    assert_json_error(renamed, 400)
    assert second in client.get('/vets/specialities/json').json()


@pytest.mark.parametrize('name', ['', ' ', 'x' * 256, None])
def test_vet_speciality_rejects_invalid_names(client, vet_api, name):
    speciality = vet_api.speciality()
    for response in (client.post('/vets/specialities', json={'name': name}),
                     client.put('/vets/specialities/' + str(speciality['id']), json={'name': name})):
        assert_json_error(response, 400)
        assert response.json()['message'] == 'Invalid request.'
    assert speciality in client.get('/vets/specialities/json').json()


def test_vet_speciality_rejects_mismatched_and_missing_ids(client, vet_api):
    speciality = vet_api.speciality()
    assert_json_error(client.put('/vets/specialities/' + str(speciality['id']),
                                json={'id': 2147483647, 'name': 'Mismatch'}), 400)
    assert_json_error(client.put('/vets/specialities/2147483647', json={'name': 'Missing'}), 404)
    assert speciality in client.get('/vets/specialities/json').json()


def test_vet_speciality_unicode_name_text_limit(client, vet_api):
    response = client.post('/vets/specialities', json={'name': 'ñ' * 255})
    assert response.status_code == 201, response.text
    record = response.json()
    vet_api.specialities.append(record['id'])
    assert record['name'] == 'ñ' * 255
    assert record in client.get('/vets/specialities/json').json()
