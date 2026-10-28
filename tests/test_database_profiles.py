"""Integration checks for database profiles."""

import pytest

from petclinic.constants import (
    DEFAULT_DIALECT_PROPERTY, DIALECT_H2, DIALECT_MYSQL, DIALECT_ORACLE, DIALECT_POSTGRES,
)
from petclinic_test_support import DATABASE


def test_database_profile_and_oracle_feature_gates(client, application_context):
    import java

    source = application_context.java_ctx.getBean(java.type('javax.sql.DataSource'))
    source = java.type('io.micronaut.data.connection.jdbc.advice.DelegatingDataSource').unwrapDataSource(source)
    connection = source.getConnection()
    try:
        metadata = connection.getMetaData()
        assert metadata.getDatabaseProductName() == {
            'h2': 'H2', 'mysql': 'MySQL', 'postgres': 'PostgreSQL', 'oracle': 'Oracle'}[DATABASE]
        assert metadata.getURL().startswith({
            'h2': 'jdbc:h2:', 'mysql': 'jdbc:mysql:',
            'postgres': 'jdbc:postgresql:', 'oracle': 'jdbc:oracle:'}[DATABASE])
    finally:
        connection.close()
    if DATABASE != 'oracle':
        for path in ('/visits', '/visits/search?fromDate=2026-01-01&toDate=2026-12-31',
                     '/knowledge', '/owners/1/care-record', '/oracle/transaction-priority'):
            assert client.get(path).status_code == 404, path
        for name in ('PetCareKnowledgeService', 'OwnerCareViewService', 'OracleTransactionPriorityService'):
            assert not application_context.java_ctx.containsBean(java.type('petclinic.services.' + name))


@pytest.mark.parametrize('dialect,prefix,source_kind,profile', [
    (None, 'H2', 'default', 'custom-database'),
    (DIALECT_H2, 'H2', 'flat', 'custom-database'),
    (DIALECT_MYSQL, 'MySql', 'environment', 'custom-database'),
    (DIALECT_ORACLE, 'Oracle', 'nested', 'custom-database'),
    (DIALECT_POSTGRES, 'Postgres', 'flat', 'custom-database'),
    (DIALECT_H2, 'H2', 'flat', 'oracle'),
])
def test_dialect_selects_beans_independently_of_profile(
        application_context, dialect, prefix, source_kind, profile):
    import java

    HashMap = java.type('java.util.HashMap')
    ApplicationContext = java.type('io.micronaut.context.ApplicationContext')
    PropertySource = java.type('io.micronaut.context.env.PropertySource')
    properties = HashMap()
    builder = (ApplicationContext.builder(application_context.java_ctx.getClassLoader())
               .deduceEnvironment(False).environments('test', profile))
    if source_kind == 'environment':
        properties.put('DATASOURCES_DEFAULT_DIALECT', dialect)
        convention = java.type('io.micronaut.context.env.PropertySource$PropertyConvention')
        builder.propertySources(PropertySource.of(
            'test-dialect-env', properties, convention.ENVIRONMENT_VARIABLE, None))
    elif source_kind != 'default':
        if source_kind == 'nested':
            datasource = HashMap()
            datasource.put('dialect', dialect)
            datasources = HashMap()
            datasources.put('default', datasource)
            properties.put('datasources', datasources)
        else:
            properties.put(DEFAULT_DIALECT_PROPERTY, dialect)
        builder.properties(properties)
    context = builder.build()
    environment = context.getEnvironment()
    try:
        # Resolve conditions without starting servers, migrations or connections.
        environment.start()
        context.configure()
        String = java.type('java.lang.String')
        assert environment.getProperty(DEFAULT_DIALECT_PROPERTY, String).get() == (dialect or DIALECT_H2)
        if profile == 'custom-database':
            # Flyway locations are stored configuration, not lazily provisioned
            # connection properties supplied by Test Resources.
            assert environment.containsProperty('flyway.datasources.default.locations') == (source_kind == 'default')
        definitions = context.getBeanDefinitions(java.type('petclinic.repositories.OwnerRepository'))
        names = [str(bean.getBeanType().getSimpleName()) for bean in definitions]
        assert names == [prefix + 'OwnerRepository$Intercepted'], names
        for layer, name in (
                ('services', 'PetCareKnowledgeService'),
                ('services', 'OwnerCareViewService'),
                ('services', 'OracleTransactionPriorityService'),
                ('controllers', 'OwnerCareRecordController')):
            assert context.containsBean(java.type('petclinic.' + layer + '.' + name)) == (dialect == DIALECT_ORACLE), name
    finally:
        context.close()
        environment.stop()
