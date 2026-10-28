"""Exact request/response assertions ported from Java ClinicControllerGeoTest."""

import pytest
from petclinic_test_support import _fixture


@pytest.mark.parametrize('index', range(8), ids=[
    'shouldReturnClinicsWithinBoundingBoxAsJson',
    'shouldReturnClinicsWithinDrawnPolygonAsJson',
    'shouldReturnClinicsWithinConcavePolygonAsJson',
    'shouldReturnClinicsIntersectingLineAsJson',
    'shouldReturnClinicsIntersectingDrawnMultiPointLineAsJson',
    'shouldReturnClinicsIntersectingDrawnLineAsJson',
    'shouldReturnNearbyClinicsAsJson',
    'shouldReturnNearbyClinicsFilteredByBooleanFlags'
])
def test_clinic_java_reference_geometry_contracts(client, application_context, index):
    case = _fixture(application_context, 'reference-geometry-http.json')['cases'][index]
    response = client.post(case['endpoint'], json=case['payload'])
    assert response.status_code == 200, response.text
    for expected in case['contains']:
        assert expected in response.text, (case['name'], expected, response.text)
    for excluded in case['excludes']:
        assert excluded not in response.text, (case['name'], excluded, response.text)
