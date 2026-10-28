"""Pets repository contracts and database-specific implementations."""

from typing import Protocol

from micronaut.context.annotation import Requires
from micronaut.data.annotation import Join
from micronaut.data.annotation import Query
from micronaut.data.jdbc.annotation import JdbcRepository
from micronaut.data.model.query.builder.sql import Dialect
from micronaut.data.repository import CrudRepository
from micronaut.data.repository import GenericRepository
from petclinic.constants import DEFAULT_DIALECT_PROPERTY, DIALECT_H2, DIALECT_MYSQL, DIALECT_ORACLE, DIALECT_POSTGRES
from petclinic.models.patients import Pet
from petclinic.models.patients import PetType


class PetRepository(GenericRepository[Pet, int], Protocol):
    """Pet queries that eagerly fetch owner and type relationships."""

    @Join(value="type", type=Join.Type.FETCH)
    @Join(value="owner", type=Join.Type.FETCH)
    @Join(value="visits", type=Join.Type.LEFT_FETCH)
    def findOneById(self, id: int) -> Pet | None: ...

    def findByOwnerId(self, ownerId: int) -> list[Pet]: ...


class PetTypeRepository(GenericRepository[PetType, int], Protocol):
    """Lookup repository for pet types shown in form select boxes."""

    def findOneById(self, id: int) -> PetType | None: ...

    @Query("SELECT * FROM TYPES ORDER BY NAME", nativeQuery=True)
    def findAllOrderByName(self) -> list[PetType]: ...


@Requires(property=DEFAULT_DIALECT_PROPERTY, value=DIALECT_H2)
@JdbcRepository(dialect=Dialect.H2)
class H2PetRepository(PetRepository, CrudRepository[Pet, int], Protocol):
    @Query(value="SELECT p.* FROM PETS p WHERE p.OWNER_ID = :ownerId ORDER BY p.NAME", nativeQuery=True)
    def findByOwnerId(self, ownerId: int) -> list[Pet]: ...

    @Join(value="type", type=Join.Type.FETCH)
    @Join(value="owner", type=Join.Type.FETCH)
    @Join(value="visits", type=Join.Type.LEFT_FETCH)
    def findOneById(self, id: int) -> Pet | None: ...


@Requires(property=DEFAULT_DIALECT_PROPERTY, value=DIALECT_H2)
@JdbcRepository(dialect=Dialect.H2)
class H2PetTypeRepository(PetTypeRepository, CrudRepository[PetType, int], Protocol):

    def findOneById(self, id: int) -> PetType | None: ...

    @Query("SELECT * FROM TYPES ORDER BY NAME", nativeQuery=True)
    def findAllOrderByName(self) -> list[PetType]: ...


@Requires(property=DEFAULT_DIALECT_PROPERTY, value=DIALECT_ORACLE)
@JdbcRepository(dialect=Dialect.ORACLE)
class OraclePetRepository(PetRepository, CrudRepository[Pet, int], Protocol):
    @Query(value="SELECT p.* FROM PETS p WHERE p.OWNER_ID = :ownerId ORDER BY p.NAME", nativeQuery=True)
    def findByOwnerId(self, ownerId: int) -> list[Pet]: ...

    @Join(value="type", type=Join.Type.FETCH)
    @Join(value="owner", type=Join.Type.FETCH)
    @Join(value="visits", type=Join.Type.LEFT_FETCH)
    def findOneById(self, id: int) -> Pet | None: ...


@Requires(property=DEFAULT_DIALECT_PROPERTY, value=DIALECT_ORACLE)
@JdbcRepository(dialect=Dialect.ORACLE)
class OraclePetTypeRepository(PetTypeRepository, CrudRepository[PetType, int], Protocol):

    def findOneById(self, id: int) -> PetType | None: ...

    @Query("SELECT * FROM TYPES ORDER BY NAME", nativeQuery=True)
    def findAllOrderByName(self) -> list[PetType]: ...


@Requires(property=DEFAULT_DIALECT_PROPERTY, value=DIALECT_MYSQL)
@JdbcRepository(dialect=Dialect.MYSQL)
class MySqlPetRepository(PetRepository, CrudRepository[Pet, int], Protocol):
    @Query(value="SELECT p.* FROM PETS p WHERE p.OWNER_ID = :ownerId ORDER BY p.NAME", nativeQuery=True)
    def findByOwnerId(self, ownerId: int) -> list[Pet]: ...

    @Join(value="type", type=Join.Type.FETCH)
    @Join(value="owner", type=Join.Type.FETCH)
    @Join(value="visits", type=Join.Type.LEFT_FETCH)
    def findOneById(self, id: int) -> Pet | None: ...


@Requires(property=DEFAULT_DIALECT_PROPERTY, value=DIALECT_MYSQL)
@JdbcRepository(dialect=Dialect.MYSQL)
class MySqlPetTypeRepository(PetTypeRepository, CrudRepository[PetType, int], Protocol):

    def findOneById(self, id: int) -> PetType | None: ...

    @Query("SELECT * FROM TYPES ORDER BY NAME", nativeQuery=True)
    def findAllOrderByName(self) -> list[PetType]: ...


@Requires(property=DEFAULT_DIALECT_PROPERTY, value=DIALECT_POSTGRES)
@JdbcRepository(dialect=Dialect.POSTGRES)
class PostgresPetRepository(PetRepository, CrudRepository[Pet, int], Protocol):
    @Query(value='SELECT p.* FROM "PETS" p WHERE p."OWNER_ID" = :ownerId ORDER BY p."NAME"', nativeQuery=True)
    def findByOwnerId(self, ownerId: int) -> list[Pet]: ...

    @Join(value="type", type=Join.Type.FETCH)
    @Join(value="owner", type=Join.Type.FETCH)
    @Join(value="visits", type=Join.Type.LEFT_FETCH)
    def findOneById(self, id: int) -> Pet | None: ...


@Requires(property=DEFAULT_DIALECT_PROPERTY, value=DIALECT_POSTGRES)
@JdbcRepository(dialect=Dialect.POSTGRES)
class PostgresPetTypeRepository(PetTypeRepository, CrudRepository[PetType, int], Protocol):
    @Query(value='SELECT * FROM "TYPES" ORDER BY "NAME"', nativeQuery=True)
    def findAllOrderByName(self) -> list[PetType]: ...

    def findOneById(self, id: int) -> PetType | None: ...
