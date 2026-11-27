"""One application and fixture database per selected profile test run."""

import pytest
from pyronaut import requests
from pyronaut.test import MicronautTest, micronaut_test_fixture
from petclinic_test_support import DATABASE




@pytest.fixture(scope="session")
def application_context(request):
    """Start the Micronaut application once for the whole test session.

    Keep one application and fixture database for the HTTP workflow suite.
    ``transactional=False`` gives requests their real service transactions.
    Each database profile is run in a separate CLI invocation.
    """

    # The SDK pytest builder does not discover the application context configurer
    # early enough; select H2 explicitly as with the external database profiles.
    fixture = micronaut_test_fixture(
        request,
        MicronautTest(environments=["test", DATABASE], transactional=False)
    )
    yield fixture
    fixture.stop()


@pytest.fixture(scope="session")
def client(application_context):
    """Create a Pyronaut requests session bound to the test context."""

    return requests.with_context(application_context)


@pytest.fixture
def vet_api(client, application_context):
    from petclinic_test_support import VetApi
    api = VetApi(client, application_context)
    try:
        yield api
    finally:
        api.cleanup()
