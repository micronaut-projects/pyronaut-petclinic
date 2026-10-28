"""Shared reference fixtures and database-specific SQL helpers."""

import json
import os
import re

DATABASE = os.environ.get('PETCLINIC_TEST_DATABASE', 'oracle')


def _reference_http(application_context):
    return _fixture(application_context, 'reference-http.json')


def _fixture(application_context, name):
    import java
    environment = application_context.java_ctx.getEnvironment()
    resource = environment.getResourceAsStream('fixtures/' + name)
    assert resource.isPresent()
    stream = resource.get()
    try:
        return json.loads(bytes((b & 255) for b in stream.readAllBytes()).decode('utf-8'))
    finally:
        stream.close()


def _database_sql(sql):
    if DATABASE != 'postgres':
        return sql
    names = {'VETS', 'LAST_NAME', 'CLINIC_SERVICE_OFFERINGS', 'NAME', 'DESCRIPTION',
             'PRICE', 'DURATION_MINUTES', 'CLINIC_ID', 'SERVICE_CODE'}
    return re.sub(r'\b[A-Z_]+\b', lambda match: '"' + match[0] + '"' if match[0] in names else match[0], sql)


def assert_json_error(response, status):
    assert response.status_code == status, response.text
    assert response.headers['content-type'].startswith('application/json'), response.text
    assert 'location' not in response.headers
    assert response.json()['message']
    assert '<!DOCTYPE html>' not in response.text


class VetApi:
    """Create isolated CRUD fixtures and remove them even after an assertion fails."""

    def __init__(self, client, application_context):
        self.client = client
        self.context = application_context
        self.vets = []
        self.specialities = []

    def speciality(self):
        import uuid
        response = self.client.post('/vets/specialities', json={'name': 'review-' + uuid.uuid4().hex})
        assert response.status_code == 201, response.text
        record = response.json()
        self.specialities.append(record['id'])
        return record

    def create(self, selected=()):
        response = self.client.post('/vets', json={'firstName': 'Review', 'lastName': 'Test',
                                   'specialityIds': [s['id'] for s in selected]})
        assert response.status_code == 201, response.text
        self.vets.append(response.json()['id'])
        return response

    def cleanup(self):
        import java
        repository = self.context.java_ctx.getBean(java.type('petclinic.repositories.VetRepository'))
        for id in self.vets:
            row = repository.findOneById(id)
            if row is not None:
                repository.deleteSpecialityLinks(id)
                repository.delete(row)
        specialities = self.context.java_ctx.getBean(java.type('petclinic.repositories.SpecialityRepository'))
        for id in self.specialities:
            specialities.deleteById(id)
