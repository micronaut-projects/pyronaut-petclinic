"""Generated spatial writes and physical-connection regression contracts."""

import pytest
from petclinic_test_support import DATABASE


def test_clinic_repository_saves_geometry_and_reads_it_back(application_context):
    import java
    from micronaut.data.model.geo import Point
    from petclinic.controllers.clinics import _polygon
    repository = application_context.java_ctx.getBean(java.type('petclinic.repositories.ClinicRepository'))
    Clinic = java.type('petclinic.models.Clinic')
    point = Point(-89.3838, 43.0748)
    area = _polygon([Point(-89.3938, 43.0668), Point(-89.3738, 43.0668),
                     Point(-89.3738, 43.0828), Point(-89.3938, 43.0828)])
    saved = None
    try:
        saved = repository.save(Clinic('Geometry write probe', '15 E Main St.', 'Madison', True, False,
                                       point, area, None, java.type('java.util.ArrayList')()))
        loaded = repository.findOneById(saved.id)
        assert loaded.name == 'Geometry write probe'
        assert loaded.location.x() == pytest.approx(-89.3838)
        assert loaded.location.y() == pytest.approx(43.0748)
        assert loaded.serviceArea is not None
    finally:
        if saved is not None:
            repository.deleteById(saved.id)


@pytest.mark.skipif(DATABASE != 'h2', reason='H2GIS physical-connection regression')
def test_h2_new_connections_preserve_spatial_function_registration(application_context):
    import java
    environment = application_context.java_ctx.getEnvironment()
    String = java.type('java.lang.String')
    values = [environment.getProperty('datasources.default.' + name, String).get()
              for name in ('url', 'username', 'password')]
    DriverManager = java.type('java.sql.DriverManager')
    observer = DriverManager.getConnection(*values)
    original = None
    def comment(connection):
        statement = connection.createStatement()
        try:
            rows = statement.executeQuery("SELECT REMARKS FROM INFORMATION_SCHEMA.ROUTINES WHERE ROUTINE_SCHEMA = 'PUBLIC' AND ROUTINE_NAME = 'ST_GEOMFROMGEOJSON'")
            try:
                assert rows.next()
                return rows.getString(1)
            finally:
                rows.close()
        finally:
            statement.close()
    def set_comment(value):
        statement = observer.prepareStatement('COMMENT ON ALIAS ST_GEOMFROMGEOJSON IS ?')
        try:
            statement.setString(1, value)
            statement.execute()
        finally:
            statement.close()
    try:
        original = comment(observer)
        set_comment('H2GIS initialization regression test')
        other = DriverManager.getConnection(*values)
        try:
            assert comment(other) == 'H2GIS initialization regression test'
        finally:
            other.close()
    finally:
        set_comment(original)
        observer.close()
