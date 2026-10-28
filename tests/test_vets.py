"""Integration checks for vets."""

from petclinic_test_support import _reference_http, _database_sql


def test_vets_html_and_json(client, application_context):
    html = client.get("/vets")
    assert html.status_code == 200
    assert "Veterinarians" in html.text
    assert "James Carter" in html.text

    alias = client.get("/vets/html")
    assert alias.status_code == 200
    assert "Veterinarians" in alias.text

    json_response = client.get("/vets/json")
    assert json_response.status_code == 200
    assert [{key: vet[key] for key in ('id', 'firstName', 'lastName')}
            for vet in json_response.json()] == _reference_http(application_context)['vets']
    assert all(vet['etag'] and isinstance(vet['specialities'], list) for vet in json_response.json())


def test_vet_cache_reuses_values_until_invalidation(client, application_context):
    """ClinicService remains cached; the newer VetService CRUD reads stay fresh."""

    import java

    cache = application_context.java_ctx.getBean(java.type('io.micronaut.cache.CacheManager')).getCache('vets')
    source = application_context.java_ctx.getBean(java.type('javax.sql.DataSource'))
    source = java.type('io.micronaut.data.connection.jdbc.advice.DelegatingDataSource').unwrapDataSource(source)
    connection = source.getConnection()
    connection.setAutoCommit(True)
    update = connection.prepareStatement(_database_sql('UPDATE VETS SET LAST_NAME = ? WHERE ID = 1'))
    original = None
    try:
        cache.invalidateAll()
        service = application_context.java_ctx.getBean(java.type('petclinic.services.ClinicService'))
        warm = service.find_all_vets()
        original = next(vet.lastName for vet in warm if vet.id == 1)
        update.setString(1, 'CacheProbe')
        assert update.executeUpdate() == 1
        assert next(v['lastName'] for v in client.get('/vets/json').json() if v['id'] == 1) == 'CacheProbe'
        assert 'James CacheProbe' in client.get('/vets').text
        assert next(v.lastName for v in service.find_all_vets() if v.id == 1) == original
        cache.invalidateAll()
        refreshed = client.get('/vets/json').json()
        assert next(vet['lastName'] for vet in refreshed if vet['id'] == 1) == 'CacheProbe'
        assert next(v.lastName for v in service.find_all_vets() if v.id == 1) == 'CacheProbe'
        assert 'James CacheProbe' in client.get('/vets').text
    finally:
        if original is not None:
            update.setString(1, original)
            update.executeUpdate()
        update.close()
        connection.close()
        cache.invalidateAll()
