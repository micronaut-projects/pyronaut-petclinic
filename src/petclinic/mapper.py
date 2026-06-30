"""Compile-time bean mapper definitions.

Micronaut's ``@Mapper`` annotation generates mapping implementations from these
abstract methods. This keeps controller code focused on HTTP flow instead of
copying fields by hand.

When a mapper has multiple source parameters with overlapping property names,
explicit ``@Mapper.Mapping`` entries document and control which source wins.
Expressions such as ``#{form.name}`` are evaluated by Micronaut and are useful
when a Python identifier or a literal value should be passed through directly.
"""

from abc import ABC, abstractmethod

from jakarta.inject import Singleton
from micronaut.context.annotation import Mapper

from .entities import Owner, Pet, PetType, Visit
from .forms import OwnerForm, PetForm, VisitForm


@Singleton
class FormMapper(ABC):
    """Maps between browser-facing form DTOs and persistent entities."""

    @Mapper
    @abstractmethod
    def to_owner(self, form: OwnerForm) -> Owner:
        ...

    @Mapper
    @abstractmethod
    def update_owner(self, owner: Owner, form: OwnerForm) -> Owner:
        ...

    @Mapper
    @abstractmethod
    def to_owner_form(self, owner: Owner) -> OwnerForm:
        ...

    @Mapper.Mapping(**{"from": "#{null}", "to": "id"})
    @Mapper.Mapping(**{"from": "#{form.name}", "to": "name"})
    @Mapper.Mapping(**{"from": "#{form.birthDate}", "to": "birthDate"})
    @Mapper.Mapping(**{"from": "#{owner}", "to": "owner"})
    @Mapper.Mapping(**{"from": "#{pet_type}", "to": "type"})
    @abstractmethod
    def to_pet(self, form: PetForm, owner: Owner, pet_type: PetType) -> Pet:
        ...

    @Mapper.Mapping(**{"from": "pet.id", "to": "id"})
    @Mapper.Mapping(**{"from": "#{form.name}", "to": "name"})
    @Mapper.Mapping(**{"from": "#{form.birthDate}", "to": "birthDate"})
    @Mapper.Mapping(**{"from": "#{owner}", "to": "owner"})
    @Mapper.Mapping(**{"from": "#{pet_type}", "to": "type"})
    @abstractmethod
    def update_pet(self, pet: Pet, form: PetForm, owner: Owner, pet_type: PetType) -> Pet:
        ...

    @Mapper.Mapping(**{"from": "#{pet.getTypeId()}", "to": "typeId"})
    @abstractmethod
    def to_pet_form(self, pet: Pet) -> PetForm:
        ...

    @Mapper.Mapping(**{"from": "#{null}", "to": "id"})
    @Mapper.Mapping(**{"from": "#{pet}", "to": "pet"})
    @abstractmethod
    def to_visit(self, form: VisitForm, pet: Pet) -> Visit:
        ...
