"""Care_records repository contracts and database-specific implementations."""

from typing import Protocol

from micronaut.context.annotation import Requires
from micronaut.data.jdbc.annotation import JdbcRepository
from micronaut.data.model.query.builder.sql import Dialect
from micronaut.data.repository import CrudRepository
from petclinic.constants import DEFAULT_DIALECT_PROPERTY, DIALECT_ORACLE
from petclinic.models.care_records import OwnerCareView


@Requires(property=DEFAULT_DIALECT_PROPERTY, value=DIALECT_ORACLE)
@JdbcRepository(dialect=Dialect.ORACLE)
class OwnerCareViewRepository(CrudRepository[OwnerCareView, int], Protocol):
    def findOneById(self, id: int) -> OwnerCareView | None: ...
