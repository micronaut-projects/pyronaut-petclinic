"""Oracle loyalty fixtures and independent JDBC/HTTP transaction helpers."""

from types import SimpleNamespace
import json
import pytest
from patient_test_support import patients


@pytest.fixture
def loyalty(patients, application_context):
    import java
    context = application_context.java_ctx
    accounts = context.getBean(java.type('petclinic.repositories.OwnerLoyaltyAccountRepository'))
    vouchers = context.getBean(java.type('petclinic.repositories.OwnerRewardVoucherRepository'))
    service = context.getBean(java.type('petclinic.services.OwnerLoyaltyService'))
    redemption = context.getBean(java.type('petclinic.services.LoyaltyRedemptionService'))
    operations = context.getBean(java.type('io.micronaut.transaction.TransactionOperations'))
    Long = java.type('java.lang.Long')
    source = context.getBean(java.type('javax.sql.DataSource'))
    source = java.type('io.micronaut.data.connection.jdbc.advice.DelegatingDataSource').unwrapDataSource(source)

    def credit(account, points):
        return operations.executeWrite(lambda status: accounts.reserveIncrementPoints(account.id, Long.valueOf(points)))

    def debit(account, points):
        return operations.executeWrite(lambda status: accounts.reserveDecrementPoints(account.id, Long.valueOf(points)))

    def scalar(sql):
        connection = source.getConnection()
        try:
            statement = connection.createStatement()
            try:
                rows = statement.executeQuery(sql)
                try:
                    assert rows.next()
                    return rows.getString(1)
                finally:
                    rows.close()
            finally:
                statement.close()
        finally:
            connection.close()

    def execute(sql):
        connection = source.getConnection()
        try:
            connection.setAutoCommit(True)
            statement = connection.createStatement()
            try:
                return statement.executeUpdate(sql)
            finally:
                statement.close()
        finally:
            connection.close()

    yield SimpleNamespace(patients=patients, accounts=accounts, vouchers=vouchers, service=service,
                          redemption=redemption, operations=operations, source=source, Long=Long,
                          credit=credit, debit=debit, scalar=scalar, execute=execute)


def concurrent_posts(client, paths, bodies=None):
    """Host Java HTTP futures overlap requests without Python thread callbacks."""
    import java
    HttpClient = java.type('java.net.http.HttpClient')
    HttpRequest = java.type('java.net.http.HttpRequest')
    Publishers = java.type('java.net.http.HttpRequest$BodyPublishers')
    Handlers = java.type('java.net.http.HttpResponse$BodyHandlers')
    URI = java.type('java.net.URI')
    Duration = java.type('java.time.Duration')
    TimeUnit = java.type('java.util.concurrent.TimeUnit')
    http = HttpClient.newHttpClient()
    try:
        futures = []
        for index, path in enumerate(paths):
            request = HttpRequest.newBuilder(URI.create(client.base_url.rstrip('/') + path)).timeout(Duration.ofSeconds(30))
            request.header('Accept', 'application/json')
            body = Publishers.noBody()
            if bodies is not None:
                request.header('Content-Type', 'application/json')
                body = Publishers.ofString(json.dumps(bodies[index]))
            futures.append(http.sendAsync(request.POST(body).build(), Handlers.ofString()))
        results = []
        for future in futures:
            response = future.get(35, TimeUnit.SECONDS)
            text = str(response.body())
            results.append((response.statusCode(), json.loads(text) if text.startswith('{') else text))
        return results
    finally:
        http.close()
