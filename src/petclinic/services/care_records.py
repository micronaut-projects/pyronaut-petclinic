"""Care records application services."""

from typing import Annotated

from jakarta.inject import Inject, Singleton
from micronaut.context.annotation import Requires
from petclinic.constants import DEFAULT_DIALECT_PROPERTY, DIALECT_ORACLE
from petclinic.models.care_records import OwnerCareView
from petclinic.repositories.care_records import OwnerCareViewRepository


@Requires(property=DEFAULT_DIALECT_PROPERTY, value=DIALECT_ORACLE)
@Singleton
class OwnerCareViewService:
    repository: Annotated[OwnerCareViewRepository, Inject]

    def find(self, owner_id: int) -> OwnerCareView | None:
        return self.repository.findOneById(owner_id)

    def update(self, document: OwnerCareView) -> OwnerCareView | None:
        self.repository.update(document)
        return self.find(document.id)
