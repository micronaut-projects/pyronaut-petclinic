"""Integration checks for care records."""

import pytest
from petclinic_test_support import DATABASE

pytestmark = pytest.mark.skipif(DATABASE != 'oracle', reason='Oracle-only reference feature')

import re


def test_owner_care_document_updates_nested_rows_and_enforces_etags(client):
    import copy
    url = '/owners/1/care-record'
    response = client.get(url)
    assert response.status_code == 200, response.text
    original = response.json()
    assert original['_id'] == 1 and original['_metadata']['etag']
    assert original['pets'] and original['pets'][0]['visits']
    assert re.fullmatch(r'\d{4}-\d{2}-\d{2}', original['pets'][0]['birthDate'])
    assert re.fullmatch(r'\d{4}-\d{2}-\d{2}', original['pets'][0]['visits'][0]['date'])
    changed = copy.deepcopy(original)
    changed['city'] = 'Document city'
    changed['pets'][0]['name'] = 'Document pet'
    changed['pets'][0]['visits'][0]['description'] = 'Document visit'
    saved = client.put(url, json=changed)
    assert saved.status_code == 200, saved.text
    document = saved.json()
    assert document['city'] == changed['city']
    assert document['_metadata']['etag'] != original['_metadata']['etag']
    details = client.get('/owners/1')
    assert details.status_code == 200, details.text
    assert 'Document city' in details.text and 'Document pet' in details.text and 'Document visit' in details.text
    stale = client.put(url, json=changed)
    assert stale.status_code == 409, stale.text
    assert 'Reload it before saving' in stale.json()['message']
    document['city'] = 'Second document save'
    second = client.put(url, json=document)
    assert second.status_code == 200, second.text
    restore = copy.deepcopy(original)
    restore['_metadata'] = second.json()['_metadata']
    assert client.put(url, json=restore).status_code == 200
    before_relational_edit = client.get(url).json()
    fields = {key: before_relational_edit[key] for key in ('firstName', 'lastName', 'address', 'city', 'telephone')}
    fields['city'] = 'Relational edit'
    relational = client.post('/owners/1/edit', data=fields, allow_redirects=False)
    assert relational.status_code in (301, 302, 303), relational.text
    stale_relational = client.put(url, json=before_relational_edit)
    assert stale_relational.status_code == 409, stale_relational.text
    restore['_metadata'] = client.get(url).json()['_metadata']
    assert client.put(url, json=restore).status_code == 200


def test_owner_care_document_rejects_membership_and_invalid_fields(client):
    import copy
    url = '/owners/1/care-record'
    response = client.get(url)
    assert response.status_code == 200, response.text
    original = response.json()
    for change in ('mismatch', 'metadata', 'etag', 'pet-name', 'pet-birth-date', 'visit-date', 'visit-description', 'first-name-null', 'telephone', 'membership', 'insert-pet', 'insert-visit', 'remove-visit'):
        document = copy.deepcopy(original)
        if change == 'mismatch': document['_id'] = 999999
        elif change == 'metadata': document['_metadata'] = None
        elif change == 'etag': document['_metadata']['etag'] = ''
        elif change == 'pet-name': document['pets'][0]['name'] = ''
        elif change == 'pet-birth-date': document['pets'][0]['birthDate'] = None
        elif change == 'visit-date': document['pets'][0]['visits'][0]['date'] = None
        elif change == 'first-name-null': document['firstName'] = None
        elif change == 'telephone': document['telephone'] = 'not a number'
        elif change == 'visit-description': document['pets'][0]['visits'][0]['description'] = ''
        elif change == 'membership': document['pets'] = []
        elif change == 'insert-pet':
            added = copy.deepcopy(document['pets'][0])
            added['id'] = 999999
            added['visits'] = []
            document['pets'].append(added)
        elif change == 'insert-visit':
            added = copy.deepcopy(document['pets'][0]['visits'][0])
            added['id'] = 999999
            document['pets'][0]['visits'].append(added)
        elif change == 'remove-visit': document['pets'][0]['visits'] = []
        rejected = client.put(url, json=document)
        assert rejected.status_code == 400, (change, rejected.text)
        assert rejected.json()['message']
        current = client.get(url).json()
        assert current['city'] == original['city'] and current['pets'] == original['pets']
        assert current['_metadata']['etag'] == original['_metadata']['etag']
    missing = client.get('/owners/999999/care-record', headers={'Accept': 'application/json'})
    assert missing.status_code == 404
    assert missing.json()['message']
    original['_id'] = 999999
    assert client.put('/owners/999999/care-record', json=original).status_code == 404
