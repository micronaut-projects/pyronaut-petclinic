"""Veterinarian and speciality HTML forms and success feedback."""


def test_vet_crud_forms_and_empty_specialities(client, vet_api):
    vet = vet_api.create([vet_api.speciality()]).json()
    id = vet['id']
    new = client.get('/vets/new')
    assert new.status_code == 200 and 'action="/vets"' in new.text and 'data-is-new="true"' in new.text
    assert '/resources/js/vet-form.js' in new.text
    assert 'Veterinarian saved.' in client.get('/vets?saved=true').text
    edit = client.get(f'/vets/{id}/edit')
    assert edit.status_code == 200, edit.text
    for text in (f'action="/vets/{id}"', 'name="etag"', vet['etag'], 'checked',
                 '/resources/js/vet-form.js', 'id="vet-feedback"', 'id="vet-delete-form"'):
        assert text in edit.text
    assert f'action="/vets/{id}/edit"' not in edit.text and f'action="/vets/{id}/delete"' not in edit.text
    saved = client.put(f'/vets/{id}', json={'firstName': 'Form', 'lastName': 'Updated', 'specialityIds': []},
                       headers={'If-Match': vet['etag']})
    assert saved.status_code == 200 and saved.json()['specialities'] == []
    assert saved.json()['etag'] != vet['etag']
    assert saved.headers['etag'] == '"' + saved.json()['etag'] + '"'


def test_vet_speciality_forms_and_success_notices(client, vet_api):
    speciality = vet_api.speciality()
    id = speciality['id']
    page = client.get('/vets/specialities?created=true')
    assert page.status_code == 200 and 'Speciality created.' in page.text and speciality['name'] in page.text
    assert 'Speciality changed.' in client.get('/vets/specialities?changed=true').text
    new = client.get('/vets/specialities/new')
    assert new.status_code == 200 and 'id="speciality-form"' in new.text
    assert 'action="/vets/specialities"' in new.text and '/resources/js/speciality-form.js' in new.text
    edit = client.get(f'/vets/specialities/{id}/edit?saved=true')
    assert edit.status_code == 200 and f'action="/vets/specialities/{id}"' in edit.text
    assert 'id="speciality-saved-alert"' in edit.text and 'Speciality saved.' in edit.text
    assert speciality['name'] in edit.text and 'id="speciality-feedback"' in edit.text
