"""Integration checks for priority."""

import pytest
from petclinic_test_support import DATABASE

pytestmark = pytest.mark.skipif(DATABASE != 'oracle', reason='Oracle-only reference feature')

import re
import json
from html import unescape


def test_priority_page_serves_browser_scripts(client):
    page = client.get('/oracle/transaction-priority')
    assert page.status_code == 200, page.text
    scripts = re.findall(r'<script[^>]+src="(/resources/[^\"]+)"', page.text)
    assert scripts, 'The priority page must load its browser controls'
    for path in scripts:
        script = client.get(path)
        assert script.status_code == 200, path
        assert 'javascript' in script.headers['content-type'], path


@pytest.mark.parametrize('language,committed', [
    ('en', 'Booking committed.'),
    ('es', 'Reserva confirmada.'),
    ('de', 'Buchung festgeschrieben.'),
])
def test_priority_page_supplies_localized_booking_statuses(client, language, committed):
    client.get('/locale', params={'lang': language}, allow_redirects=False)
    try:
        page = client.get('/oracle/transaction-priority')
        assert page.status_code == 200, page.text
        assert '<html lang="' + language + '">' in page.text, language
        labels = {key: unescape(value).strip() for key, value in
                  re.findall(r'<span data-key="([^\"]+)">([^<]*)</span>', page.text)}
        expected = {
            'error', 'noAvailable', 'ready', 'confirmed', 'emergencyPending',
            'emergencyWon', 'regularWon', 'taken', 'working', 'timedOut',
            'countdown', 'completing', 'finished', 'outcome.NOT_STARTED',
            'outcome.RUNNING', 'outcome.COMMITTED', 'outcome.PRIORITY_ROLLED_BACK',
            'outcome.TAKEN', 'outcome.TIMED_OUT', 'outcome.FAILED',
        }
        assert labels.keys() == expected
        for key, value in labels.items():
            assert value and not value.startswith('transactionPriority.'), (language, key, value)
        assert labels['outcome.COMMITTED'] == committed, (language, labels['outcome.COMMITTED'])
    finally:
        client.get('/locale', params={'lang': 'en'}, allow_redirects=False)


def test_priority_booking_commits_and_reports_taken_appointments(client):
    prefix = '/oracle/transaction-priority'
    page = client.get(prefix, timeout=40)
    assert page.status_code == 200, page.text
    assert 'transaction-priority-page' in page.text and 'data-reservation-seconds="15"' in page.text
    choices = re.findall(r'<option value="(\d+)">', page.text)
    assert len(choices) == 2
    appointment = int(choices[0])
    response = client.post(prefix + '/book', params={'appointmentId': appointment, 'type': 'regular'}, timeout=40)
    assert response.status_code == 200, response.text
    assert response.json()['outcome'] == 'COMMITTED'
    assert response.json()['databaseStatus'] == 'BOOKED_FOR_REGULAR'
    taken = client.post(prefix + '/book', params={'appointmentId': appointment, 'type': 'emergency'}, timeout=40)
    assert taken.status_code == 409, taken.text
    assert taken.json()['outcome'] == 'TAKEN'
    assert taken.json()['databaseStatus'] == 'BOOKED_FOR_REGULAR'
    missing = client.post(prefix + '/book', params={'appointmentId': 999999, 'type': 'emergency'}, timeout=40)
    assert missing.status_code == 404 and missing.json()['message'] == 'Appointment not found.'
    reset = client.post(prefix + '/reset', timeout=40)
    assert reset.status_code == 200 and reset.json() == {'status': 'reset'}
    assert len(re.findall(r'<option value="(\d+)">', client.get(prefix).text)) == 2


@pytest.mark.parametrize('attempt', range(3))
def test_priority_emergency_displaces_a_regular_transaction(client, application_context, attempt):
    import java
    import json
    import time

    prefix = '/oracle/transaction-priority'
    assert client.post(prefix + '/reset', timeout=40).status_code == 200
    page = client.get(prefix)
    appointment = int(re.search(r'<option value="(\d+)">', page.text).group(1))
    data_source = application_context.java_ctx.getBean(java.type('javax.sql.DataSource'))
    data_source = java.type('io.micronaut.data.connection.jdbc.advice.DelegatingDataSource').unwrapDataSource(data_source)
    # The embedded pytest context forbids Python thread creation. A host Java
    # HTTP client starts the request asynchronously without a Python callback.
    HttpClient = java.type('java.net.http.HttpClient')
    HttpRequest = java.type('java.net.http.HttpRequest')
    BodyPublishers = java.type('java.net.http.HttpRequest$BodyPublishers')
    BodyHandlers = java.type('java.net.http.HttpResponse$BodyHandlers')
    URI = java.type('java.net.URI')
    Duration = java.type('java.time.Duration')
    TimeUnit = java.type('java.util.concurrent.TimeUnit')
    SQLException = java.type('java.sql.SQLException')
    http = HttpClient.newHttpClient()
    try:
        uri = client.base_url.rstrip('/') + prefix + '/book?appointmentId=' + str(appointment) + '&type=regular'
        request = HttpRequest.newBuilder(URI.create(uri)).timeout(Duration.ofSeconds(40)).header('Accept', 'application/json').POST(BodyPublishers.noBody()).build()
        regular = http.sendAsync(request, BodyHandlers.ofString())
        deadline = time.monotonic() + 5
        locked = False
        while time.monotonic() < deadline:
            if regular.isDone():
                response = regular.get()
                raise AssertionError('LOW finished before its row lock was observed: ' + str(response.body()))
            connection = data_source.getConnection()
            try:
                connection.setAutoCommit(False)
                statement = connection.prepareStatement('SELECT ID FROM APPOINTMENTS WHERE ID = ? FOR UPDATE NOWAIT')
                try:
                    statement.setInt(1, appointment)
                    rows = statement.executeQuery()
                    rows.close()
                finally:
                    statement.close()
            except SQLException as error:
                if error.getErrorCode() == 54:
                    locked = True
                    break
                raise
            finally:
                connection.rollback()
                connection.close()
            time.sleep(0.025)
        assert locked, 'LOW did not acquire its actual Oracle row lock within five seconds'
        emergency = client.post(prefix + '/book', params={'appointmentId': appointment, 'type': 'emergency'}, timeout=40)
        displaced = regular.get(35, TimeUnit.SECONDS)
        assert emergency.status_code == 200, emergency.text
        assert emergency.json()['outcome'] == 'COMMITTED'
        assert emergency.json()['databaseStatus'] == 'BOOKED_FOR_EMERGENCY'
        assert displaced.statusCode() == 409, displaced.body()
        result = json.loads(str(displaced.body()))
        assert result['outcome'] == 'PRIORITY_ROLLED_BACK'
        assert result['databaseStatus'] == 'BOOKED_FOR_EMERGENCY'
        repository = application_context.java_ctx.getBean(java.type('petclinic.repositories.AppointmentRepository'))
        from petclinic.models.appointments import status_name
        assert status_name(repository.findOneById(appointment).status) == 'BOOKED_FOR_EMERGENCY', attempt
    finally:
        http.close()
    assert client.post(prefix + '/reset', timeout=40).status_code == 200


def test_priority_outcomes_distinguish_rollback_timeout_and_other_failures():
    import java
    from petclinic.models.appointments import BookingOutcome, BookingTaken
    from petclinic.controllers.transaction_priority import booking_outcome
    PriorityError = java.type('io.micronaut.transaction.exceptions.OracleTransactionPriorityException')
    TimeoutError = java.type('io.micronaut.transaction.exceptions.TransactionTimedOutException')
    DataError = java.type('io.micronaut.data.exceptions.DataAccessException')
    SQLException = java.type('java.sql.SQLException')
    RuntimeException = java.type('java.lang.RuntimeException')
    priority_error = PriorityError('Priority rollback')
    assert booking_outcome(priority_error) == BookingOutcome.PRIORITY_ROLLED_BACK
    assert booking_outcome(RuntimeException(priority_error)) == BookingOutcome.FAILED
    assert booking_outcome(TimeoutError('Expired')) == BookingOutcome.TIMED_OUT
    for code in (54, 30006, 1013):
        assert booking_outcome(DataError('Lock failure', SQLException('Lock wait', '', code))) == BookingOutcome.TIMED_OUT
    assert booking_outcome(BookingTaken('Taken')) == BookingOutcome.TAKEN
    assert booking_outcome(RuntimeError('ORA-63300')) == BookingOutcome.FAILED
    assert booking_outcome(DataError('Other failure', SQLException('Other', '', 1))) == BookingOutcome.FAILED


def test_priority_equal_priority_lock_wait_reports_timeout(client, application_context):
    import java
    prefix = '/oracle/transaction-priority'
    assert client.post(prefix + '/reset', timeout=40).status_code == 200
    appointment = int(re.search(r'<option value="(\d+)">', client.get(prefix).text).group(1))
    source = application_context.java_ctx.getBean(java.type('javax.sql.DataSource'))
    source = java.type('io.micronaut.data.connection.jdbc.advice.DelegatingDataSource').unwrapDataSource(source)
    holder = source.getConnection()
    try:
        holder.setAutoCommit(False)
        statement = holder.prepareStatement('SELECT ID FROM APPOINTMENTS WHERE ID = ? FOR UPDATE')
        try:
            statement.setInt(1, appointment)
            rows = statement.executeQuery()
            assert rows.next()
            rows.close()
            response = client.post(prefix + '/book', params={'appointmentId': appointment, 'type': 'emergency'}, timeout=40)
            assert response.status_code == 503, response.text
            assert response.json()['outcome'] == 'TIMED_OUT'
            assert response.json()['databaseStatus'] == 'AVAILABLE'
        finally:
            statement.close()
    finally:
        holder.rollback()
        holder.close()
    assert client.post(prefix + '/reset', timeout=40).status_code == 200
