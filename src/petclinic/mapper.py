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
from petclinic.dtos.patients import OwnerForm, PetForm, VisitForm
from petclinic.dtos.care_summary import OwnerCareSummary, OwnerCareSummaryPet, OwnerCareSummaryPetVisit
from petclinic.models.patients import Owner, Pet, PetType, Visit


@Singleton
class FormMapper(ABC):
    """Maps between browser-facing form DTOs and persistent entities."""

    @Mapper.Mapping(from_="#{null}", to="id")
    @abstractmethod
    def to_owner(self, form: OwnerForm) -> Owner:
        ...

    @Mapper.Mapping(from_="owner.id", to="id")
    @Mapper.Mapping(from_="form.firstName", to="firstName")
    @Mapper.Mapping(from_="form.lastName", to="lastName")
    @Mapper.Mapping(from_="form.address", to="address")
    @Mapper.Mapping(from_="form.city", to="city")
    @Mapper.Mapping(from_="form.telephone", to="telephone")
    @abstractmethod
    def update_owner(self, owner: Owner, form: OwnerForm) -> Owner:
        ...

    @Mapper
    @abstractmethod
    def to_owner_form(self, owner: Owner) -> OwnerForm:
        ...

    @Mapper.Mapping(from_="#{null}", to="id")
    @Mapper.Mapping(from_="#{form.name}", to="name")
    @Mapper.Mapping(from_="#{form.birthDateValue}", to="birthDate")
    @Mapper.Mapping(from_="#{owner}", to="owner")
    @Mapper.Mapping(from_="#{pet_type}", to="type")
    @abstractmethod
    def to_pet(self, form: PetForm, owner: Owner, pet_type: PetType) -> Pet:
        ...

    @Mapper.Mapping(from_="pet.id", to="id")
    @Mapper.Mapping(from_="#{form.name}", to="name")
    @Mapper.Mapping(from_="#{form.birthDateValue}", to="birthDate")
    @Mapper.Mapping(from_="#{owner}", to="owner")
    @Mapper.Mapping(from_="#{pet_type}", to="type")
    @abstractmethod
    def update_pet(self, pet: Pet, form: PetForm, owner: Owner, pet_type: PetType) -> Pet:
        ...

    @Mapper.Mapping(from_="#{pet.get_type_id()}", to="typeId")
    @abstractmethod
    def to_pet_form(self, pet: Pet) -> PetForm:
        ...

    @Mapper.Mapping(from_="#{null}", to="id")
    @Mapper.Mapping(from_="#{form.dateValue}", to="date")
    @Mapper.Mapping(from_="#{form.durationValue}", to="duration")
    @Mapper.Mapping(from_="#{form.periodValue}", to="period")
    @Mapper.Mapping(from_="#{pet}", to="pet")
    @abstractmethod
    def to_visit(self, form: VisitForm, pet: Pet) -> Visit:
        ...

    @Mapper.Mapping(from_='#{this.to_care_summary_pets(owner)}', to='pets')
    @abstractmethod
    def to_owner_care_summary(self, owner: Owner) -> OwnerCareSummary:
        ...

    @Mapper.Mapping(from_='#{this.to_care_summary_visits(pet)}', to='visits')
    @abstractmethod
    def to_care_summary_pet(self, pet: Pet) -> OwnerCareSummaryPet:
        ...

    @Mapper
    @abstractmethod
    def to_care_summary_visit(self, visit: Visit) -> OwnerCareSummaryPetVisit:
        ...

    def to_care_summary_pets(self, owner: Owner) -> list[OwnerCareSummaryPet]:
        return [self.to_care_summary_pet(pet) for pet in owner.pets]

    def to_care_summary_visits(self, pet: Pet) -> list[OwnerCareSummaryPetVisit]:
        return [self.to_care_summary_visit(visit) for visit in pet.visits]
