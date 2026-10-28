"""Clinics repository contracts and database-specific implementations."""

from typing import Protocol

from micronaut.context.annotation import Requires
from micronaut.data.annotation import Join, Upsert
from micronaut.data.jdbc.annotation import JdbcRepository
from micronaut.data.model.geo import Geometry
from micronaut.data.model.query.builder.sql import Dialect
from micronaut.data.repository import GenericRepository, CrudRepository
from petclinic.constants import DEFAULT_DIALECT_PROPERTY, DIALECT_H2, DIALECT_MYSQL, DIALECT_ORACLE, DIALECT_POSTGRES
from petclinic.models.clinics import Clinic, ClinicServiceOffering


class ClinicRepository(GenericRepository[Clinic, int], Protocol):
    def findOneById(self, id: int) -> Clinic | None: ...

    def findAllOrderByName(self) -> list[Clinic]: ...

    def findByLocationNear(self, geometry: Geometry, distance: float) -> list[Clinic]: ...

    def findByLocationGeoWithin(self, geometry: Geometry) -> list[Clinic]: ...

    def findByServiceAreaGeoIntersects(self, geometry: Geometry) -> list[Clinic]: ...

    def findByAcceptingNewPatients(self, acceptingNewPatients: bool) -> list[Clinic]: ...

    def findByEmergencyService(self, emergencyService: bool) -> list[Clinic]: ...

    def findByAcceptingNewPatientsAndEmergencyService(self, acceptingNewPatients: bool, emergencyService: bool) -> list[
        Clinic]: ...


class ClinicServiceOfferingRepository(GenericRepository[ClinicServiceOffering, int], Protocol):
    @Upsert(conflictsOn=["clinic", "serviceCode"])
    def upsert(self, offering: ClinicServiceOffering) -> ClinicServiceOffering: ...

    @Join(value="clinic", type=Join.Type.FETCH)
    def findByClinicIdOrderByServiceCode(self, clinicId: int) -> list[ClinicServiceOffering]: ...

    @Join(value="clinic", type=Join.Type.FETCH)
    def findByClinicIdAndServiceCode(self, clinicId: int, serviceCode: str) -> ClinicServiceOffering | None: ...


@Requires(property=DEFAULT_DIALECT_PROPERTY, value=DIALECT_H2)
@JdbcRepository(dialect=Dialect.H2)
class H2ClinicRepository(ClinicRepository, CrudRepository[Clinic, int], Protocol):

    def findOneById(self, id: int) -> Clinic | None: ...

    def findAllOrderByName(self) -> list[Clinic]: ...

    def findByLocationNear(self, geometry: Geometry, distance: float) -> list[Clinic]: ...

    def findByLocationGeoWithin(self, geometry: Geometry) -> list[Clinic]: ...

    def findByServiceAreaGeoIntersects(self, geometry: Geometry) -> list[Clinic]: ...

    def findByAcceptingNewPatients(self, acceptingNewPatients: bool) -> list[Clinic]: ...

    def findByEmergencyService(self, emergencyService: bool) -> list[Clinic]: ...

    def findByAcceptingNewPatientsAndEmergencyService(self, acceptingNewPatients: bool, emergencyService: bool) -> list[
        Clinic]: ...


@Requires(property=DEFAULT_DIALECT_PROPERTY, value=DIALECT_H2)
@JdbcRepository(dialect=Dialect.H2)
class H2ClinicServiceOfferingRepository(ClinicServiceOfferingRepository, CrudRepository[ClinicServiceOffering, int],
                                        Protocol):

    @Upsert(conflictsOn=["clinic", "serviceCode"])
    def upsert(self, offering: ClinicServiceOffering) -> ClinicServiceOffering: ...

    @Join(value="clinic", type=Join.Type.FETCH)
    def findByClinicIdOrderByServiceCode(self, clinicId: int) -> list[ClinicServiceOffering]: ...

    @Join(value="clinic", type=Join.Type.FETCH)
    def findByClinicIdAndServiceCode(self, clinicId: int, serviceCode: str) -> ClinicServiceOffering | None: ...


@Requires(property=DEFAULT_DIALECT_PROPERTY, value=DIALECT_ORACLE)
@JdbcRepository(dialect=Dialect.ORACLE)
class OracleClinicRepository(ClinicRepository, CrudRepository[Clinic, int], Protocol):

    def findOneById(self, id: int) -> Clinic | None: ...

    def findAllOrderByName(self) -> list[Clinic]: ...

    def findByLocationNear(self, geometry: Geometry, distance: float) -> list[Clinic]: ...

    def findByLocationGeoWithin(self, geometry: Geometry) -> list[Clinic]: ...

    def findByServiceAreaGeoIntersects(self, geometry: Geometry) -> list[Clinic]: ...

    def findByAcceptingNewPatients(self, acceptingNewPatients: bool) -> list[Clinic]: ...

    def findByEmergencyService(self, emergencyService: bool) -> list[Clinic]: ...

    def findByAcceptingNewPatientsAndEmergencyService(self, acceptingNewPatients: bool, emergencyService: bool) -> list[
        Clinic]: ...


@Requires(property=DEFAULT_DIALECT_PROPERTY, value=DIALECT_ORACLE)
@JdbcRepository(dialect=Dialect.ORACLE)
class OracleClinicServiceOfferingRepository(ClinicServiceOfferingRepository, CrudRepository[ClinicServiceOffering, int],
                                            Protocol):

    @Upsert(conflictsOn=["clinic", "serviceCode"])
    def upsert(self, offering: ClinicServiceOffering) -> ClinicServiceOffering: ...

    @Join(value="clinic", type=Join.Type.FETCH)
    def findByClinicIdOrderByServiceCode(self, clinicId: int) -> list[ClinicServiceOffering]: ...

    @Join(value="clinic", type=Join.Type.FETCH)
    def findByClinicIdAndServiceCode(self, clinicId: int, serviceCode: str) -> ClinicServiceOffering | None: ...


@Requires(property=DEFAULT_DIALECT_PROPERTY, value=DIALECT_MYSQL)
@JdbcRepository(dialect=Dialect.MYSQL)
class MySqlClinicRepository(ClinicRepository, CrudRepository[Clinic, int], Protocol):

    def findOneById(self, id: int) -> Clinic | None: ...

    def findAllOrderByName(self) -> list[Clinic]: ...

    def findByLocationNear(self, geometry: Geometry, distance: float) -> list[Clinic]: ...

    def findByLocationGeoWithin(self, geometry: Geometry) -> list[Clinic]: ...

    def findByServiceAreaGeoIntersects(self, geometry: Geometry) -> list[Clinic]: ...

    def findByAcceptingNewPatients(self, acceptingNewPatients: bool) -> list[Clinic]: ...

    def findByEmergencyService(self, emergencyService: bool) -> list[Clinic]: ...

    def findByAcceptingNewPatientsAndEmergencyService(self, acceptingNewPatients: bool, emergencyService: bool) -> list[
        Clinic]: ...


@Requires(property=DEFAULT_DIALECT_PROPERTY, value=DIALECT_MYSQL)
@JdbcRepository(dialect=Dialect.MYSQL)
class MySqlClinicServiceOfferingRepository(ClinicServiceOfferingRepository, CrudRepository[ClinicServiceOffering, int],
                                           Protocol):

    @Upsert(conflictsOn=["clinic", "serviceCode"])
    def upsert(self, offering: ClinicServiceOffering) -> ClinicServiceOffering: ...

    @Join(value="clinic", type=Join.Type.FETCH)
    def findByClinicIdOrderByServiceCode(self, clinicId: int) -> list[ClinicServiceOffering]: ...

    @Join(value="clinic", type=Join.Type.FETCH)
    def findByClinicIdAndServiceCode(self, clinicId: int, serviceCode: str) -> ClinicServiceOffering | None: ...


@Requires(property=DEFAULT_DIALECT_PROPERTY, value=DIALECT_POSTGRES)
@JdbcRepository(dialect=Dialect.POSTGRES)
class PostgresClinicRepository(ClinicRepository, CrudRepository[Clinic, int], Protocol):

    def findOneById(self, id: int) -> Clinic | None: ...

    def findAllOrderByName(self) -> list[Clinic]: ...

    def findByLocationNear(self, geometry: Geometry, distance: float) -> list[Clinic]: ...

    def findByLocationGeoWithin(self, geometry: Geometry) -> list[Clinic]: ...

    def findByServiceAreaGeoIntersects(self, geometry: Geometry) -> list[Clinic]: ...

    def findByAcceptingNewPatients(self, acceptingNewPatients: bool) -> list[Clinic]: ...

    def findByEmergencyService(self, emergencyService: bool) -> list[Clinic]: ...

    def findByAcceptingNewPatientsAndEmergencyService(self, acceptingNewPatients: bool, emergencyService: bool) -> list[
        Clinic]: ...


@Requires(property=DEFAULT_DIALECT_PROPERTY, value=DIALECT_POSTGRES)
@JdbcRepository(dialect=Dialect.POSTGRES)
class PostgresClinicServiceOfferingRepository(ClinicServiceOfferingRepository,
                                              CrudRepository[ClinicServiceOffering, int], Protocol):

    @Upsert(conflictsOn=["clinic", "serviceCode"])
    def upsert(self, offering: ClinicServiceOffering) -> ClinicServiceOffering: ...

    @Join(value="clinic", type=Join.Type.FETCH)
    def findByClinicIdOrderByServiceCode(self, clinicId: int) -> list[ClinicServiceOffering]: ...

    @Join(value="clinic", type=Join.Type.FETCH)
    def findByClinicIdAndServiceCode(self, clinicId: int, serviceCode: str) -> ClinicServiceOffering | None: ...
