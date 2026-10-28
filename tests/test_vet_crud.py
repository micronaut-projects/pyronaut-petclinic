"""Veterinarian HTTP CRUD and optimistic-locking contracts from VetCrudTest."""

from petclinic_test_support import assert_json_error
import pytest


def test_vet_crud_create_read_update_delete(client, vet_api):
    speciality = vet_api.speciality()
    created = vet_api.create([speciality])
    vet = created.json()
    url = '/vets/' + str(vet['id'])
    etag = created.headers['etag']
    assert etag == '"' + vet['etag'] + '"'
    assert created.headers['cache-control'] == 'no-store'
    loaded = client.get(url)
    assert loaded.status_code == 200 and loaded.json() == vet
    assert loaded.headers['etag'] == etag
    assert vet['specialities'] == [speciality]
    updated = client.put(url, json={'firstName': 'Updated', 'lastName': vet['lastName'], 'specialityIds': []},
                         headers={'If-Match': etag})
    assert updated.status_code == 200, updated.text
    assert updated.json()['firstName'] == 'Updated'
    assert updated.json()['specialities'] == []
    assert updated.headers['etag'] != etag
    deleted = client.delete(url, headers={'If-Match': updated.headers['etag']})
    assert deleted.status_code == 204 and not deleted.text
    assert_json_error(client.get(url), 404)
    assert speciality in client.get('/vets/specialities/json').json()


def test_vet_crud_rejects_stale_update_and_delete_without_losing_links(client, vet_api):
    first, second = vet_api.speciality(), vet_api.speciality()
    created = vet_api.create([first])
    vet = created.json()
    url = '/vets/' + str(vet['id'])
    winner = client.put(url, json={'firstName': 'Winner', 'lastName': 'Test', 'specialityIds': [second['id']]},
                        headers={'If-Match': created.headers['etag']})
    assert winner.status_code == 200, winner.text
    assert_json_error(client.put(url, json={'firstName': 'Loser', 'lastName': 'Changed', 'specialityIds': [first['id']]},
                                headers={'If-Match': created.headers['etag']}), 412)
    assert_json_error(client.delete(url, headers={'If-Match': created.headers['etag']}), 412)
    assert client.get(url).json() == winner.json()
    assert winner.json()['specialities'] == [second]


def test_vet_crud_requires_if_match(client, vet_api, application_context):
    vet = vet_api.create().json()
    url = '/vets/' + str(vet['id'])
    assert_json_error(client.put(url, json={'firstName': 'Other', 'lastName': 'Name'}), 428)
    assert_json_error(client.delete(url), 428)
    # The SDK requests client rejects blank header values before sending them.
    # Java's HTTP client lets us exercise the actual server contract.
    import java
    import json
    server = application_context.java_ctx.getBean(java.type('io.micronaut.runtime.server.EmbeddedServer'))
    http = java.type('java.net.http.HttpClient').newHttpClient()
    try:
        for value in ('', '   '):
            for method in ('PUT', 'DELETE'):
                body = json.dumps({'firstName': 'Other', 'lastName': 'Name'})
                request = (java.type('java.net.http.HttpRequest').newBuilder(
                    java.type('java.net.URI').create(server.getURL().toString() + url))
                    .header('Content-Type', 'application/json').header('If-Match', value)
                    .method(method, java.type('java.net.http.HttpRequest$BodyPublishers').ofString(body)).build())
                response = http.sendAsync(request, java.type('java.net.http.HttpResponse$BodyHandlers').ofString()).get(
                    30, java.type('java.util.concurrent.TimeUnit').SECONDS)
                assert response.statusCode() == 428, response.body()
                assert json.loads(response.body())['message'] == 'ETag is missing.'
    finally:
        http.close()
    assert client.get(url).json() == vet


def test_vet_crud_assignment_only_change_updates_etag(client, vet_api):
    first, second = vet_api.speciality(), vet_api.speciality()
    created = vet_api.create([first])
    vet = created.json()
    url = '/vets/' + str(vet['id'])
    saved = client.put(url, json={'firstName': vet['firstName'], 'lastName': vet['lastName'],
                                 'specialityIds': [second['id']]}, headers={'If-Match': created.headers['etag']})
    assert saved.status_code == 200, saved.text
    assert saved.headers['etag'] != created.headers['etag']
    assert saved.json()['specialities'] == [second]
    assert_json_error(client.put(url, json={'firstName': 'Old', 'lastName': 'Request'},
                                headers={'If-Match': created.headers['etag']}), 412)


def test_vet_crud_noop_retains_etag_and_accepts_unquoted_tag(client, vet_api):
    created = vet_api.create([vet_api.speciality()])
    vet = created.json()
    response = client.put('/vets/' + str(vet['id']), json={'firstName': vet['firstName'],
        'lastName': vet['lastName'], 'specialityIds': [s['id'] for s in vet['specialities']]},
        headers={'If-Match': vet['etag']})
    assert response.status_code == 200, response.text
    assert response.json() == vet and response.headers['etag'] == created.headers['etag']


def test_vet_crud_rejects_weak_tag_and_keeps_row(client, vet_api):
    created = vet_api.create([vet_api.speciality()])
    vet = created.json()
    url = '/vets/' + str(vet['id'])
    assert_json_error(client.put(url, json={'firstName': 'Weak', 'lastName': 'Update'},
                                headers={'If-Match': 'W/' + created.headers['etag']}), 412)
    assert client.get(url).json() == vet


@pytest.mark.parametrize('ids,message', [([2147483647], 'One or more specialities were not found.'),
                                       ([None], 'Each speciality must have an id.')])
def test_vet_crud_rejects_invalid_specialities(client, ids, message):
    response = client.post('/vets', json={'firstName': 'Valid', 'lastName': 'Name', 'specialityIds': ids})
    assert_json_error(response, 400)
    assert response.json()['message'] == message


@pytest.mark.parametrize('value', ['1', 1.5, True, {'id': 1}, [1], 2147483648])
def test_vet_crud_rejects_non_integer_identifiers(client, value):
    response = client.post('/vets', json={'firstName': 'Valid', 'lastName': 'Name', 'specialityIds': [value]})
    assert_json_error(response, 400)
    assert response.json()['message'] == 'Invalid request value.'


@pytest.mark.parametrize('selection', [None, []])
def test_vet_crud_null_or_empty_selection_means_no_assignments(client, vet_api, selection):
    response = client.post('/vets', json={'firstName': 'Null', 'lastName': 'Selection', 'specialityIds': selection})
    assert response.status_code == 201, response.text
    vet_api.vets.append(response.json()['id'])
    assert response.json()['specialities'] == [] and response.json()['etag']


def test_vet_crud_name_text_limit_round_trips_unicode(client, vet_api):
    response = client.post('/vets', json={'firstName': 'é' * 255, 'lastName': 'ü' * 255})
    assert response.status_code == 201, response.text
    record = response.json()
    vet_api.vets.append(record['id'])
    assert record['firstName'] == 'é' * 255 and record['lastName'] == 'ü' * 255
    assert client.get('/vets/' + str(record['id'])).json() == record


@pytest.mark.parametrize('field,value', [('firstName', ''), ('firstName', ' '), ('firstName', 'x' * 256),
                                        ('lastName', ''), ('lastName', ' '), ('lastName', 'x' * 256)])
def test_vet_crud_rejects_invalid_names_without_mutation(client, vet_api, field, value):
    created = vet_api.create()
    vet = created.json()
    payload = {'firstName': 'Valid', 'lastName': 'Name', field: value}
    assert_json_error(client.post('/vets', json=payload), 400)
    url = '/vets/' + str(vet['id'])
    assert_json_error(client.put(url, json=payload, headers={'If-Match': created.headers['etag']}), 400)
    assert client.get(url).json() == vet


def test_vet_crud_missing_resources_return_json(client):
    url = '/vets/2147483647'
    for response in (client.get(url), client.put(url, json={'firstName': 'Unknown', 'lastName': 'Vet'},
                                               headers={'If-Match': 'unknown'}),
                     client.delete(url, headers={'If-Match': 'unknown'})):
        assert_json_error(response, 404)
        assert response.json()['message'] == 'Entity not found.'
        assert response.json()['path'] == url


def test_vet_crud_listing_order_and_private_hash(client):
    response = client.get('/vets/json')
    assert response.status_code == 200
    vets = response.json()
    assert [v['lastName'] for v in vets] == sorted(v['lastName'] for v in vets)
    assert all(set(v) == {'id', 'firstName', 'lastName', 'specialities', 'etag'} and v['etag'] for v in vets)
    assert 'specialitiesHash' not in response.text and 'SPECIALITIES_ETAG_HASH' not in response.text

def test_vet_crud_rejects_malformed_json_and_invalid_path(client):
    malformed = client.post('/vets/specialities', data='{"name":', headers={'Content-Type': 'application/json'})
    assert_json_error(malformed, 400)
    assert_json_error(client.get('/vets/not-an-integer'), 400)
