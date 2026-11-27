"""Management endpoint contracts from the Java HealthTest."""


def test_health_endpoint_is_exposed(client):
    response = client.get('/health')
    assert response.status_code == 200, response.text
    assert response.json()['status'] == 'UP'


def test_info_endpoint_reports_application_name(client, application_context):
    import java
    response = client.get('/info')
    assert response.status_code == 200, response.text
    environment = application_context.java_ctx.getEnvironment()
    name = environment.getProperty('micronaut.application.name', java.type('java.lang.String')).get()
    assert response.json()['application']['name'] == name
