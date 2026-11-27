"""Integration checks for clinic catalog."""

import json
from petclinic_test_support import _database_sql


def test_catalog_spanish_translation_and_shared_edit_endpoint(client):
    client.get('/locale', params={'lang': 'es', 'backUrl': '/clinics/1/services'}, allow_redirects=False)
    try:
        page = client.get('/clinics/1/services')
        assert page.status_code == 200, page.text
        for text in ('Servicios en Downtown Madison Pet Clinic', 'Nuevo servicio', 'Código del servicio'):
            assert text in page.text
        assert 'New service offering' not in page.text
    finally:
        client.get('/locale', params={'lang': 'en', 'backUrl': '/'}, allow_redirects=False)
    edit = client.get('/clinics/1/services/WELLNESS_CHECK/edit')
    assert edit.status_code == 200 and 'action="/clinics/1/services"' in edit.text
    assert 'readonly' not in edit.text


def test_catalog_accepts_forty_character_service_codes(client, application_context):
    import java
    code = 'REVIEW_' + 'C' * 33
    data = {'serviceCode': code, 'name': 'Long clinic-local code', 'price': 68, 'durationMinutes': 45}
    id = None
    try:
        response = client.post('/clinics/2/services', json=data)
        assert response.status_code == 200, response.text
        id = response.json()['id']
        assert response.json()['serviceCode'] == code
        rejected = client.post('/clinics/2/services', json={**data, 'serviceCode': code + 'X'})
        assert rejected.status_code == 400 and 'serviceCode' in rejected.json()['errors']
    finally:
        if id is not None:
            application_context.java_ctx.getBean(java.type('petclinic.repositories.ClinicServiceOfferingRepository')).deleteById(id)


def test_catalog_description_text_limit_round_trips_unicode(client, application_context):
    import java
    data = {'serviceCode': 'REVIEW_DESCRIPTION_LIMIT', 'name': 'Description limit',
            'description': 'ñ' * 500, 'price': 20, 'durationMinutes': 30}
    id = None
    try:
        saved = client.post('/clinics/1/services', json=data)
        assert saved.status_code == 200, saved.text
        id = saved.json()['id']
        assert saved.json()['description'] == data['description']
        rejected = client.post('/clinics/1/services', json={**data, 'description': data['description'] + 'ñ'})
        assert rejected.status_code == 400 and 'description' in rejected.json()['errors']
    finally:
        if id is not None:
            application_context.java_ctx.getBean(java.type('petclinic.repositories.ClinicServiceOfferingRepository')).deleteById(id)


def test_clinic_catalog_upsert_preserves_identity_and_clinic_scope(client):
    first_catalog = client.get("/clinics/1/services")
    assert first_catalog.status_code == 200, first_catalog.text
    assert "WELLNESS_CHECK" in first_catalog.text and "DENTAL_SPARKLE" in first_catalog.text
    assert "RABIES_EXPRESS" in client.get("/clinics/2/services").text
    assert client.get("/clinics/1/services/new").status_code == 200

    data = {"serviceCode": "PORT_DEMO", "name": "Port demo offering", "description": "Initial description", "price": 45.01, "durationMinutes": 30}
    created = client.post("/clinics/1/services", json=data)
    assert created.status_code == 200, created.text
    first = created.json()
    assert first["id"] and first["clinicId"] == 1 and first["price"] == 45.01
    updated = client.post("/clinics/1/services", json={**data, "name": "Updated <offering>", "price": "65.10", "durationMinutes": 45})
    assert updated.status_code == 200, updated.text
    assert updated.json()["id"] == first["id"]
    assert updated.json()["price"] == 65.1 and updated.json()["durationMinutes"] == 45
    catalog = client.get("/clinics/1/services").text
    assert catalog.count("<code>PORT_DEMO</code>") == 1
    assert "Updated &lt;offering&gt;" in catalog
    edit = client.get("/clinics/1/services/PORT_DEMO/edit")
    assert edit.status_code == 200 and "65.10" in edit.text

    other = client.post("/clinics/2/services", json=data)
    assert other.status_code == 200, other.text
    assert other.json()["id"] != first["id"] and other.json()["clinicId"] == 2
    assert "Updated &lt;offering&gt;" not in client.get("/clinics/2/services").text


def test_clinic_catalog_validates_fields_and_missing_entities(client):
    data = {"serviceCode": "INVALID_DEMO", "name": "Demo", "price": 20, "durationMinutes": 30}
    for changes in ({"price": -1}, {"price": "0.001"}, {"durationMinutes": 0}, {"serviceCode": ""}, {"name": ""}):
        response = client.post("/clinics/1/services", json={**data, **changes})
        assert response.status_code == 400, response.text
        assert response.json()["errors"]
    assert client.post("/clinics/999999/services", json=data).status_code == 404
    assert client.get("/clinics/999999/services").status_code == 404
    assert client.get("/clinics/1/services/DOES_NOT_EXIST/edit").status_code == 404


def test_concurrent_catalog_updates_preserve_one_complete_offering(client, application_context):
    """Concurrent HTTP updates keep the clinic/code identity and a whole submitted row."""

    import java

    code = 'ASYNC-PARITY-CHECK'
    payload = {'serviceCode': code, 'name': 'Concurrent fixture', 'description': 'Concurrent fixture',
               'price': 10, 'durationMinutes': 10}
    seeded = client.post('/clinics/1/services', json=payload)
    assert seeded.status_code == 200, seeded.text
    offering_id = seeded.json()['id']
    http = java.type('java.net.http.HttpClient').newHttpClient()
    JavaRequest = java.type('java.net.http.HttpRequest')
    BodyPublishers = java.type('java.net.http.HttpRequest$BodyPublishers')
    BodyHandlers = java.type('java.net.http.HttpResponse$BodyHandlers')
    TimeUnit = java.type('java.util.concurrent.TimeUnit')
    endpoint = application_context.java_ctx.getBean(java.type('io.micronaut.runtime.server.EmbeddedServer')).getURL().toString()
    submitted = [{**payload, 'name': f'Concurrent {i}', 'description': f'Submission {i}',
                  'price': 20 + i, 'durationMinutes': 30 + i} for i in range(6)]
    futures = []
    source = application_context.java_ctx.getBean(java.type('javax.sql.DataSource'))
    source = java.type('io.micronaut.data.connection.jdbc.advice.DelegatingDataSource').unwrapDataSource(source)
    try:
        for body in submitted:
            request = (JavaRequest.newBuilder(java.type('java.net.URI').create(endpoint + '/clinics/1/services'))
                       .header('Content-Type', 'application/json')
                       .POST(BodyPublishers.ofString(json.dumps(body))).build())
            futures.append(http.sendAsync(request, BodyHandlers.ofString()))
        for future in futures:
            response = future.get(30, TimeUnit.SECONDS)
            assert response.statusCode() == 200, response.body()
            assert json.loads(response.body())['id'] == offering_id
        connection = source.getConnection()
        query = connection.prepareStatement(_database_sql(
            'SELECT ID, NAME, DESCRIPTION, PRICE, DURATION_MINUTES FROM CLINIC_SERVICE_OFFERINGS '
            'WHERE CLINIC_ID = 1 AND SERVICE_CODE = ?'))
        try:
            query.setString(1, code)
            rows = query.executeQuery()
            assert rows.next()
            assert rows.getInt(1) == offering_id
            persisted = (rows.getString(2), rows.getString(3), rows.getInt(4), rows.getInt(5))
            assert persisted in [(v['name'], v['description'], v['price'], v['durationMinutes']) for v in submitted]
            assert not rows.next()
            rows.close()
        finally:
            query.close()
            connection.close()
    finally:
        http.close()
        connection = source.getConnection()
        connection.setAutoCommit(True)
        delete = connection.prepareStatement(_database_sql('DELETE FROM CLINIC_SERVICE_OFFERINGS WHERE ID = ?'))
        try:
            delete.setInt(1, offering_id)
            delete.executeUpdate()
        finally:
            delete.close()
            connection.close()
