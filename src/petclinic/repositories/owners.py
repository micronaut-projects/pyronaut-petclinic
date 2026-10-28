"""Owners repository contracts and database-specific implementations."""

from typing import Protocol

from micronaut.context.annotation import Requires
from micronaut.data.annotation import Join
from micronaut.data.jdbc.annotation import JdbcRepository
from micronaut.data.model.query.builder.sql import Dialect
from micronaut.data.repository import CrudRepository
from micronaut.data.repository import GenericRepository
from petclinic.constants import DEFAULT_DIALECT_PROPERTY, DIALECT_H2, DIALECT_MYSQL, DIALECT_ORACLE, DIALECT_POSTGRES
from petclinic.models.patients import Owner


class OwnerRepository(GenericRepository[Owner, int], Protocol):
    """Owner queries used by search and list screens."""

    @Join(value="pets", type=Join.Type.LEFT_FETCH)
    @Join(value="pets.type", type=Join.Type.LEFT_FETCH)
    @Join(value="pets.visits", type=Join.Type.LEFT_FETCH)
    def findOneById(self, id: int) -> Owner | None: ...

    @Join(value="pets", type=Join.Type.LEFT_FETCH)
    @Join(value="pets.type", type=Join.Type.LEFT_FETCH)
    def findAllOrderByLastName(self) -> list[Owner]: ...

    @Join(value="pets", type=Join.Type.LEFT_FETCH)
    @Join(value="pets.type", type=Join.Type.LEFT_FETCH)
    def findByLastNameContainingIgnoreCaseOrderByLastName(self, lastName: str) -> list[Owner]: ...


@Requires(property=DEFAULT_DIALECT_PROPERTY, value=DIALECT_H2)
@JdbcRepository(dialect=Dialect.H2)
class H2OwnerRepository(OwnerRepository, CrudRepository[Owner, int], Protocol):

    @Join(value="pets", type=Join.Type.LEFT_FETCH)
    @Join(value="pets.type", type=Join.Type.LEFT_FETCH)
    @Join(value="pets.visits", type=Join.Type.LEFT_FETCH)
    def findOneById(self, id: int) -> Owner | None: ...

    @Join(value="pets", type=Join.Type.LEFT_FETCH)
    @Join(value="pets.type", type=Join.Type.LEFT_FETCH)
    def findAllOrderByLastName(self) -> list[Owner]: ...

    @Join(value="pets", type=Join.Type.LEFT_FETCH)
    @Join(value="pets.type", type=Join.Type.LEFT_FETCH)
    def findByLastNameContainingIgnoreCaseOrderByLastName(self, lastName: str) -> list[Owner]: ...


@Requires(property=DEFAULT_DIALECT_PROPERTY, value=DIALECT_ORACLE)
@JdbcRepository(dialect=Dialect.ORACLE)
class OracleOwnerRepository(OwnerRepository, CrudRepository[Owner, int], Protocol):

    @Join(value="pets", type=Join.Type.LEFT_FETCH)
    @Join(value="pets.type", type=Join.Type.LEFT_FETCH)
    @Join(value="pets.visits", type=Join.Type.LEFT_FETCH)
    def findOneById(self, id: int) -> Owner | None: ...

    @Join(value="pets", type=Join.Type.LEFT_FETCH)
    @Join(value="pets.type", type=Join.Type.LEFT_FETCH)
    def findAllOrderByLastName(self) -> list[Owner]: ...

    @Join(value="pets", type=Join.Type.LEFT_FETCH)
    @Join(value="pets.type", type=Join.Type.LEFT_FETCH)
    def findByLastNameContainingIgnoreCaseOrderByLastName(self, lastName: str) -> list[Owner]: ...


@Requires(property=DEFAULT_DIALECT_PROPERTY, value=DIALECT_MYSQL)
@JdbcRepository(dialect=Dialect.MYSQL)
class MySqlOwnerRepository(OwnerRepository, CrudRepository[Owner, int], Protocol):

    @Join(value="pets", type=Join.Type.LEFT_FETCH)
    @Join(value="pets.type", type=Join.Type.LEFT_FETCH)
    @Join(value="pets.visits", type=Join.Type.LEFT_FETCH)
    def findOneById(self, id: int) -> Owner | None: ...

    @Join(value="pets", type=Join.Type.LEFT_FETCH)
    @Join(value="pets.type", type=Join.Type.LEFT_FETCH)
    def findAllOrderByLastName(self) -> list[Owner]: ...

    @Join(value="pets", type=Join.Type.LEFT_FETCH)
    @Join(value="pets.type", type=Join.Type.LEFT_FETCH)
    def findByLastNameContainingIgnoreCaseOrderByLastName(self, lastName: str) -> list[Owner]: ...


@Requires(property=DEFAULT_DIALECT_PROPERTY, value=DIALECT_POSTGRES)
@JdbcRepository(dialect=Dialect.POSTGRES)
class PostgresOwnerRepository(OwnerRepository, CrudRepository[Owner, int], Protocol):

    @Join(value="pets", type=Join.Type.LEFT_FETCH)
    @Join(value="pets.type", type=Join.Type.LEFT_FETCH)
    @Join(value="pets.visits", type=Join.Type.LEFT_FETCH)
    def findOneById(self, id: int) -> Owner | None: ...

    @Join(value="pets", type=Join.Type.LEFT_FETCH)
    @Join(value="pets.type", type=Join.Type.LEFT_FETCH)
    def findAllOrderByLastName(self) -> list[Owner]: ...

    @Join(value="pets", type=Join.Type.LEFT_FETCH)
    @Join(value="pets.type", type=Join.Type.LEFT_FETCH)
    def findByLastNameContainingIgnoreCaseOrderByLastName(self, lastName: str) -> list[Owner]: ...
