"""Shared PetClinic service facade and veterinarian aggregate decoding."""

from typing import Annotated

from jakarta.inject import Inject, Singleton
from jakarta.transaction import Transactional
from java.time import Duration, LocalDate, Period
from micronaut.cache.annotation import Cacheable
from petclinic.models.patients import Owner, Pet, PetType, Visit
from petclinic.models.vets import Speciality, Vet
from petclinic.repositories.owners import OwnerRepository
from petclinic.repositories.pets import PetRepository, PetTypeRepository
from petclinic.repositories.vets import SpecialityRepository, VetRepository
from petclinic.repositories.visits import VisitRepository
from petclinic.services.durations import duration_minutes


@Singleton
class ClinicService:
    """Facade over repositories for PetClinic workflows."""

    owner_repository: Annotated[OwnerRepository, Inject]
    pet_repository: Annotated[PetRepository, Inject]
    pet_type_repository: Annotated[PetTypeRepository, Inject]
    visit_repository: Annotated[VisitRepository, Inject]
    vet_repository: Annotated[VetRepository, Inject]
    speciality_repository: Annotated[SpecialityRepository, Inject]

    def find_owner_by_id(self, owner_id: int) -> Owner | None:
        """Return one owner or ``None`` when no row exists."""

        return self.owner_repository.findOneById(owner_id)

    def find_owner_by_last_name(self, last_name: str) -> list[Owner]:
        return list(self.owner_repository.findByLastNameContainingIgnoreCaseOrderByLastName(last_name))

    def find_all_owners(self) -> list[Owner]:
        return list(self.owner_repository.findAllOrderByLastName())

    @Transactional
    def save_owner(self, owner: Owner) -> Owner:
        """Insert new owners and update existing owners in one call."""

        if owner.id is None:
            return self.owner_repository.save(owner)
        return self.owner_repository.update(owner)

    def find_pet_by_id(self, pet_id: int) -> Pet | None:
        return self.pet_repository.findOneById(pet_id)

    @Transactional
    def delete_owner(self, owner_id: int) -> None:
        self.owner_repository.deleteById(owner_id)

    def find_all_pets(self) -> list[Pet]:
        return list(self.pet_repository.findAll())

    def find_pet_types(self) -> list[PetType]:
        return list(self.pet_type_repository.findAllOrderByName())

    def find_pet_type_by_id(self, type_id: int) -> PetType | None:
        return self.pet_type_repository.findOneById(type_id)

    @Transactional
    def save_pet(self, pet: Pet) -> Pet:
        """Insert new pets and update existing pets in one call."""

        if pet.id is None:
            return self.pet_repository.save(pet)
        return self.pet_repository.update(pet)

    def find_visits_by_pet_id(self, pet_id: int) -> list[Visit]:
        return list(self.visit_repository.findByPetId(pet_id))

    @Transactional
    def delete_pet(self, pet_id: int) -> None:
        self.pet_repository.deleteById(pet_id)

    def find_visit_by_id(self, visit_id: int) -> Visit | None:
        return self.visit_repository.findOneById(visit_id)

    def search_visits(self, from_date: LocalDate, to_date: LocalDate, max_duration_minutes: int,
                      max_follow_up_months: int) -> list[dict]:
        visits = self.visit_repository.findByDateBetweenAndDurationLessThanEqualsAndPeriodLessThanEquals(
            from_date, to_date, Duration.ofMinutes(max_duration_minutes),
            Period.ofMonths(max_follow_up_months).normalized()
        )
        return [{
            "id": visit.id,
            "date": str(visit.date),
            "description": visit.description,
            "petName": visit.pet.name if visit.pet is not None else None,
            "ownerName": f"{visit.pet.owner.firstName} {visit.pet.owner.lastName}" if visit.pet is not None and visit.pet.owner is not None else None,
            "durationInMinutes": duration_minutes(visit.duration),
            "periodInMonths": visit.period.toTotalMonths(),
        } for visit in visits]

    @Transactional
    def save_visit(self, visit: Visit) -> Visit:
        """Persist a visit inside a Micronaut transaction."""

        if visit.id is None:
            return self.visit_repository.save(visit)
        return self.visit_repository.update(visit)

    @Cacheable("vets")
    def find_all_vets(self) -> list[Vet]:
        return [Vet(id=vet.id, firstName=vet.firstName, lastName=vet.lastName,
                    specialities=[Speciality(id=s['id'], name=s['name']) for s in
                                  _parse_speciality_rows(vet.specialityRows)])
                for vet in self.vet_repository.findAllWithSpecialities()]

    @Transactional
    def delete_visit(self, visit_id: int) -> None:
        self.visit_repository.deleteById(visit_id)

    def find_vet_by_id(self, vet_id: int) -> Vet | None:
        return self.vet_repository.findOneById(vet_id)

    def find_all_specialities(self) -> list[Speciality]:
        return list(self.speciality_repository.findAllOrderByName())

    def find_speciality_by_id(self, speciality_id: int) -> Speciality | None:
        return self.speciality_repository.findOneById(speciality_id)


def _parse_speciality_rows(value: str | None) -> list[dict]:
    """Decode ``LISTAGG`` speciality rows from the vet aggregate query."""

    if not value:
        return []
    specialities = []
    for row in str(value).split("|"):
        if not row or ":" not in row:
            continue
        speciality_id, name = row.split(":", 1)
        if not speciality_id:
            continue
        specialities.append({"id": int(speciality_id), "name": name})
    return specialities
