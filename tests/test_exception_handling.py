"""Global JSON domain errors remain distinct from HTML page failures."""

import pytest
from petclinic_test_support import assert_json_error


def test_missing_pet_visit_submission_returns_json_entity_not_found(client):
    path = '/owners/2147483647/pets/2147483647/visits/new'
    response = client.post(path, json={'date': '2025-01-01', 'description': 'Routine checkup',
                                     'durationMinutes': 30, 'followUpPeriodMonths': 6})
    assert_json_error(response, 404)
    assert response.json() == {'path': path, 'message': 'Entity not found.'}


@pytest.mark.parametrize('path', ['/owners/2147483647', '/owners/2147483647/edit',
    '/owners/1/pets/2147483647/edit', '/clinics/2147483647/services',
    '/clinics/2147483647/services/new', '/clinics/1/services/UNKNOWN/edit',
    '/vets/2147483647/edit', '/vets/specialities/2147483647/edit'])
def test_missing_html_pages_render_not_found_view(client, path):
    response = client.get(path)
    assert response.status_code == 404
    assert response.headers['content-type'].startswith('text/html')
    assert 'Page Not Found' in response.text


def test_missing_clinic_json_save_returns_domain_error(client):
    path = '/clinics/2147483647/services'
    response = client.post(path, json={'serviceCode': 'MISSING', 'name': 'Missing', 'price': 1, 'durationMinutes': 30})
    assert_json_error(response, 404)
    assert response.json() == {'path': path, 'message': 'Entity not found.'}


def test_duality_rejection_checks_nested_and_chained_sql_errors():
    from java.sql import SQLException
    from micronaut.data.exceptions import DataAccessException
    from petclinic.controllers.care_records import disallowed_operation
    chained = SQLException('outer SQL failure', 'state', 0)
    chained.setNextException(SQLException('disallowed duality operation', 'state', 40937))
    assert disallowed_operation(DataAccessException('wrapped', chained))
    assert not disallowed_operation(DataAccessException('unrelated', SQLException('ordinary failure', 'state', 0)))
