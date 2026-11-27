"""Vets repository contracts and database-specific implementations."""

from typing import Protocol

from micronaut.context.annotation import Requires
from micronaut.data.annotation import Query
from micronaut.data.jdbc.annotation import JdbcRepository
from micronaut.data.model.query.builder.sql import Dialect
from micronaut.data.repository import CrudRepository
from micronaut.data.repository import GenericRepository
from petclinic.constants import DEFAULT_DIALECT_PROPERTY, DIALECT_H2, DIALECT_MYSQL, DIALECT_ORACLE, DIALECT_POSTGRES
from petclinic.models.vets import Speciality
from petclinic.models.vets import Vet
from petclinic.models.vets import VetSpeciality
from petclinic.models.vets import VetWithSpecialities


class VetRepository(GenericRepository[Vet, int], Protocol):
    """Veterinarian list queries."""

    def findOneById(self, id: int) -> Vet | None: ...

    def findAllWithSpecialities(self) -> list[VetWithSpecialities]: ...

    def findAllOrderByLastName(self) -> list[Vet]: ...

    def deleteSpecialityLinks(self, id: int) -> None: ...

    def insertSpecialityLink(self, vetId: int, specialityId: int) -> None: ...


class SpecialityRepository(GenericRepository[Speciality, int], Protocol):
    """Lookup repository for specialities."""

    def findOneById(self, id: int) -> Speciality | None: ...

    @Query("SELECT * FROM SPECIALTIES ORDER BY NAME", nativeQuery=True)
    def findAllOrderByName(self) -> list[Speciality]: ...

    def findByName(self, name: str) -> Speciality | None: ...

    def findAllByIdIn(self, ids: list[int]) -> list[Speciality]: ...

    def existsByName(self, name: str) -> bool: ...


class VetSpecialityRepository(GenericRepository[VetSpeciality, VetSpeciality], Protocol):
    """Join-table repository used to persist vet speciality links."""

    def save(self, entity: VetSpeciality) -> None: ...

    @Query("SELECT s.* FROM SPECIALTIES s JOIN VET_SPECIALTIES vs ON s.ID = vs.SPECIALTY_ID WHERE vs.VET_ID = :vetId",
           nativeQuery=True)
    def findSpecialitiesByVetId(self, vetId: int) -> list[Speciality]: ...


@Requires(property=DEFAULT_DIALECT_PROPERTY, value=DIALECT_H2)
@JdbcRepository(dialect=Dialect.H2)
class H2VetRepository(VetRepository, CrudRepository[Vet, int], Protocol):
    @Query(
        value="SELECT\nv.id,\nv.FIRST_NAME AS first_name,\nv.LAST_NAME AS last_name,\nLISTAGG(\nCASE WHEN s.id IS NOT NULL THEN s.id || ':' || s.NAME END,\n'|'\n) WITHIN GROUP (ORDER BY s.NAME) AS speciality_rows\nFROM VETS v\nLEFT JOIN VET_SPECIALTIES vs ON vs.VET_ID = v.id\nLEFT JOIN SPECIALTIES s ON s.id = vs.SPECIALTY_ID\nGROUP BY v.id, v.FIRST_NAME, v.LAST_NAME\nORDER BY v.LAST_NAME",
        nativeQuery=True)
    def findAllWithSpecialities(self) -> list[VetWithSpecialities]: ...

    def findOneById(self, id: int) -> Vet | None: ...

    def findAllOrderByLastName(self) -> list[Vet]: ...

    @Query(value='DELETE FROM VET_SPECIALTIES WHERE VET_ID = :id', nativeQuery=True)
    def deleteSpecialityLinks(self, id: int) -> None: ...

    @Query(value='INSERT INTO VET_SPECIALTIES (VET_ID, SPECIALTY_ID) VALUES (:vetId, :specialityId)', nativeQuery=True)
    def insertSpecialityLink(self, vetId: int, specialityId: int) -> None: ...


@Requires(property=DEFAULT_DIALECT_PROPERTY, value=DIALECT_H2)
@JdbcRepository(dialect=Dialect.H2)
class H2SpecialityRepository(SpecialityRepository, CrudRepository[Speciality, int], Protocol):

    def findOneById(self, id: int) -> Speciality | None: ...

    @Query("SELECT * FROM SPECIALTIES ORDER BY NAME", nativeQuery=True)
    def findAllOrderByName(self) -> list[Speciality]: ...

    def findByName(self, name: str) -> Speciality | None: ...

    def findAllByIdIn(self, ids: list[int]) -> list[Speciality]: ...

    def existsByName(self, name: str) -> bool: ...


@Requires(property=DEFAULT_DIALECT_PROPERTY, value=DIALECT_H2)
@JdbcRepository(dialect=Dialect.H2)
class H2VetSpecialityRepository(VetSpecialityRepository, Protocol):
    @Query(
        value="SELECT s.* FROM SPECIALTIES s JOIN VET_SPECIALTIES vs ON vs.SPECIALTY_ID = s.id WHERE vs.VET_ID = :vetId ORDER BY s.NAME",
        nativeQuery=True)
    def findSpecialitiesByVetId(self, vetId: int) -> list[Speciality]: ...

    def save(self, entity: VetSpeciality) -> None: ...


@Requires(property=DEFAULT_DIALECT_PROPERTY, value=DIALECT_ORACLE)
@JdbcRepository(dialect=Dialect.ORACLE)
class OracleVetRepository(VetRepository, CrudRepository[Vet, int], Protocol):
    @Query(
        value="SELECT\nv.id,\nv.FIRST_NAME AS first_name,\nv.LAST_NAME AS last_name,\nLISTAGG(\nCASE WHEN s.id IS NOT NULL THEN s.id || ':' || s.NAME END,\n'|'\n) WITHIN GROUP (ORDER BY s.NAME) AS speciality_rows\nFROM VETS v\nLEFT JOIN VET_SPECIALTIES vs ON vs.VET_ID = v.id\nLEFT JOIN SPECIALTIES s ON s.id = vs.SPECIALTY_ID\nGROUP BY v.id, v.FIRST_NAME, v.LAST_NAME\nORDER BY v.LAST_NAME",
        nativeQuery=True)
    def findAllWithSpecialities(self) -> list[VetWithSpecialities]: ...

    def findOneById(self, id: int) -> Vet | None: ...

    def findAllOrderByLastName(self) -> list[Vet]: ...

    @Query(value='DELETE FROM VET_SPECIALTIES WHERE VET_ID = :id', nativeQuery=True)
    def deleteSpecialityLinks(self, id: int) -> None: ...

    @Query(value='INSERT INTO VET_SPECIALTIES (VET_ID, SPECIALTY_ID) VALUES (:vetId, :specialityId)', nativeQuery=True)
    def insertSpecialityLink(self, vetId: int, specialityId: int) -> None: ...


@Requires(property=DEFAULT_DIALECT_PROPERTY, value=DIALECT_ORACLE)
@JdbcRepository(dialect=Dialect.ORACLE)
class OracleSpecialityRepository(SpecialityRepository, CrudRepository[Speciality, int], Protocol):

    def findOneById(self, id: int) -> Speciality | None: ...

    @Query("SELECT * FROM SPECIALTIES ORDER BY NAME", nativeQuery=True)
    def findAllOrderByName(self) -> list[Speciality]: ...

    def findByName(self, name: str) -> Speciality | None: ...

    def findAllByIdIn(self, ids: list[int]) -> list[Speciality]: ...

    def existsByName(self, name: str) -> bool: ...


@Requires(property=DEFAULT_DIALECT_PROPERTY, value=DIALECT_ORACLE)
@JdbcRepository(dialect=Dialect.ORACLE)
class OracleVetSpecialityRepository(VetSpecialityRepository, Protocol):
    @Query(
        value="SELECT s.* FROM SPECIALTIES s JOIN VET_SPECIALTIES vs ON vs.SPECIALTY_ID = s.id WHERE vs.VET_ID = :vetId ORDER BY s.NAME",
        nativeQuery=True)
    def findSpecialitiesByVetId(self, vetId: int) -> list[Speciality]: ...

    def save(self, entity: VetSpeciality) -> None: ...


@Requires(property=DEFAULT_DIALECT_PROPERTY, value=DIALECT_MYSQL)
@JdbcRepository(dialect=Dialect.MYSQL)
class MySqlVetRepository(VetRepository, CrudRepository[Vet, int], Protocol):
    @Query(
        value="SELECT\nv.id,\nv.FIRST_NAME AS first_name,\nv.LAST_NAME AS last_name,\nGROUP_CONCAT(\nCASE WHEN s.id IS NOT NULL THEN CONCAT(s.id, ':', s.NAME) END\nORDER BY s.NAME SEPARATOR '|'\n) AS speciality_rows\nFROM VETS v\nLEFT JOIN VET_SPECIALTIES vs ON vs.VET_ID = v.id\nLEFT JOIN SPECIALTIES s ON s.id = vs.SPECIALTY_ID\nGROUP BY v.id, v.FIRST_NAME, v.LAST_NAME\nORDER BY v.LAST_NAME",
        nativeQuery=True)
    def findAllWithSpecialities(self) -> list[VetWithSpecialities]: ...

    def findOneById(self, id: int) -> Vet | None: ...

    def findAllOrderByLastName(self) -> list[Vet]: ...

    @Query(value='DELETE FROM VET_SPECIALTIES WHERE VET_ID = :id', nativeQuery=True)
    def deleteSpecialityLinks(self, id: int) -> None: ...

    @Query(value='INSERT INTO VET_SPECIALTIES (VET_ID, SPECIALTY_ID) VALUES (:vetId, :specialityId)', nativeQuery=True)
    def insertSpecialityLink(self, vetId: int, specialityId: int) -> None: ...


@Requires(property=DEFAULT_DIALECT_PROPERTY, value=DIALECT_MYSQL)
@JdbcRepository(dialect=Dialect.MYSQL)
class MySqlSpecialityRepository(SpecialityRepository, CrudRepository[Speciality, int], Protocol):

    def findOneById(self, id: int) -> Speciality | None: ...

    @Query("SELECT * FROM SPECIALTIES ORDER BY NAME", nativeQuery=True)
    def findAllOrderByName(self) -> list[Speciality]: ...

    def findByName(self, name: str) -> Speciality | None: ...

    def findAllByIdIn(self, ids: list[int]) -> list[Speciality]: ...

    def existsByName(self, name: str) -> bool: ...


@Requires(property=DEFAULT_DIALECT_PROPERTY, value=DIALECT_MYSQL)
@JdbcRepository(dialect=Dialect.MYSQL)
class MySqlVetSpecialityRepository(VetSpecialityRepository, Protocol):
    @Query(
        value="SELECT s.* FROM SPECIALTIES s JOIN VET_SPECIALTIES vs ON vs.SPECIALTY_ID = s.id WHERE vs.VET_ID = :vetId ORDER BY s.NAME",
        nativeQuery=True)
    def findSpecialitiesByVetId(self, vetId: int) -> list[Speciality]: ...

    def save(self, entity: VetSpeciality) -> None: ...


@Requires(property=DEFAULT_DIALECT_PROPERTY, value=DIALECT_POSTGRES)
@JdbcRepository(dialect=Dialect.POSTGRES)
class PostgresVetRepository(VetRepository, CrudRepository[Vet, int], Protocol):
    @Query(
        value='SELECT\nv.id,\nv."FIRST_NAME" AS first_name,\nv."LAST_NAME" AS last_name,\nSTRING_AGG(\nCASE WHEN s.id IS NOT NULL THEN s.id::text || \':\' || s."NAME" END,\n\'|\' ORDER BY s."NAME"\n) AS speciality_rows\nFROM "VETS" v\nLEFT JOIN "VET_SPECIALTIES" vs ON vs."VET_ID" = v.id\nLEFT JOIN "SPECIALTIES" s ON s.id = vs."SPECIALTY_ID"\nGROUP BY v.id, v."FIRST_NAME", v."LAST_NAME"\nORDER BY v."LAST_NAME"',
        nativeQuery=True)
    def findAllWithSpecialities(self) -> list[VetWithSpecialities]: ...

    def findOneById(self, id: int) -> Vet | None: ...

    def findAllOrderByLastName(self) -> list[Vet]: ...

    @Query(value='DELETE FROM "VET_SPECIALTIES" WHERE "VET_ID" = :id', nativeQuery=True)
    def deleteSpecialityLinks(self, id: int) -> None: ...

    @Query(value='INSERT INTO "VET_SPECIALTIES" ("VET_ID", "SPECIALTY_ID") VALUES (:vetId, :specialityId)',
           nativeQuery=True)
    def insertSpecialityLink(self, vetId: int, specialityId: int) -> None: ...


@Requires(property=DEFAULT_DIALECT_PROPERTY, value=DIALECT_POSTGRES)
@JdbcRepository(dialect=Dialect.POSTGRES)
class PostgresSpecialityRepository(SpecialityRepository, CrudRepository[Speciality, int], Protocol):
    @Query(value='SELECT * FROM "SPECIALTIES" ORDER BY "NAME"', nativeQuery=True)
    def findAllOrderByName(self) -> list[Speciality]: ...

    def findOneById(self, id: int) -> Speciality | None: ...

    def findByName(self, name: str) -> Speciality | None: ...

    def findAllByIdIn(self, ids: list[int]) -> list[Speciality]: ...

    def existsByName(self, name: str) -> bool: ...


@Requires(property=DEFAULT_DIALECT_PROPERTY, value=DIALECT_POSTGRES)
@JdbcRepository(dialect=Dialect.POSTGRES)
class PostgresVetSpecialityRepository(VetSpecialityRepository, Protocol):
    @Query(
        value='SELECT s.* FROM "SPECIALTIES" s JOIN "VET_SPECIALTIES" vs ON vs."SPECIALTY_ID" = s.id WHERE vs."VET_ID" = :vetId ORDER BY s."NAME"',
        nativeQuery=True)
    def findSpecialitiesByVetId(self, vetId: int) -> list[Speciality]: ...

    def save(self, entity: VetSpeciality) -> None: ...
