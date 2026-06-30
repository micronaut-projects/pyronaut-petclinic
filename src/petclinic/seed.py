"""Startup sample-data loader.

The original PetClinic application ships with well-known sample owners, pets,
visits, vets, and specialties. This module shows how to do the same in
Pyronaut with a Micronaut startup event listener.

Concepts demonstrated:

* Module-level ``Annotated[..., Inject]`` fields receive repository beans.
* ``@EventListener`` subscribes a function to Micronaut application events.
* ``StartupEvent`` runs after the application context is ready.
* ``@Transactional`` wraps the inserts in a transaction.
"""

from typing import Annotated

from jakarta.inject import Inject
from java.time import LocalDate
from jakarta.transaction import Transactional
from micronaut.context.event import StartupEvent
from micronaut.runtime.event.annotation import EventListener

from .entities import Owner, Pet, PetType, Specialty, Vet, VetSpecialty, Visit
from .repositories import (
    OwnerRepository,
    PetRepository,
    PetTypeRepository,
    SpecialtyRepository,
    VetRepository,
    VetSpecialtyRepository,
    VisitRepository,
)

owner_repository: Annotated[OwnerRepository, Inject]
pet_repository: Annotated[PetRepository, Inject]
pet_type_repository: Annotated[PetTypeRepository, Inject]
visit_repository: Annotated[VisitRepository, Inject]
vet_repository: Annotated[VetRepository, Inject]
specialty_repository: Annotated[SpecialtyRepository, Inject]
vet_specialty_repository: Annotated[VetSpecialtyRepository, Inject]


@EventListener
@Transactional
def load_sample_data(event: StartupEvent):
    """Insert deterministic sample rows whenever the app starts."""

    radiology = specialty_repository.save(Specialty(name="radiology"))
    surgery = specialty_repository.save(Specialty(name="surgery"))
    dentistry = specialty_repository.save(Specialty(name="dentistry"))

    _vet("James", "Carter")
    _vet("Helen", "Leary", radiology)
    _vet("Linda", "Douglas", surgery, dentistry)
    _vet("Rafael", "Ortega", surgery)
    _vet("Henry", "Stevens", radiology)
    _vet("Sharon", "Jenkins")

    cat = pet_type_repository.save(PetType(name="cat"))
    dog = pet_type_repository.save(PetType(name="dog"))
    lizard = pet_type_repository.save(PetType(name="lizard"))
    snake = pet_type_repository.save(PetType(name="snake"))
    bird = pet_type_repository.save(PetType(name="bird"))
    hamster = pet_type_repository.save(PetType(name="hamster"))

    george = _owner("George", "Franklin", "110 W. Liberty St.", "Madison", "6085551023")
    _pet("Leo", LocalDate.of(2010, 9, 7), cat, george)
    betty = _owner("Betty", "Davis", "638 Cardinal Ave.", "Sun Prairie", "6085551749")
    _pet("Basil", LocalDate.of(2012, 8, 6), hamster, betty)
    eduardo = _owner("Eduardo", "Rodriquez", "2693 Commerce St.", "McFarland", "6085558763")
    _pet("Jewel", LocalDate.of(2010, 3, 7), dog, eduardo)
    _pet("Rosy", LocalDate.of(2011, 4, 17), dog, eduardo)
    harold = _owner("Harold", "Davis", "563 Friendly St.", "Windsor", "6085553198")
    _pet("Iggy", LocalDate.of(2010, 11, 30), lizard, harold)
    peter = _owner("Peter", "McTavish", "2387 S. Fair Way", "Madison", "6085552765")
    _pet("George", LocalDate.of(2010, 1, 20), snake, peter)
    jean = _owner("Jean", "Coleman", "105 N. Lake St.", "Monona", "6085552654")
    samantha = _pet("Samantha", LocalDate.of(2012, 9, 4), cat, jean)
    max_pet = _pet("Max", LocalDate.of(2012, 9, 4), cat, jean)
    jeff = _owner("Jeff", "Black", "1450 Oak Blvd.", "Monona", "6085555387")
    _pet("Lucky", LocalDate.of(2011, 8, 6), bird, jeff)
    maria = _owner("Maria", "Escobito", "345 Maple St.", "Madison", "6085557683")
    _pet("Mulligan", LocalDate.of(2007, 2, 24), dog, maria)
    david = _owner("David", "Schroeder", "2749 Blackhawk Trail", "Madison", "6085559435")
    _pet("Freddy", LocalDate.of(2010, 3, 9), bird, david)
    carlos = _owner("Carlos", "Estaban", "2335 Independence La.", "Waunakee", "6085555487")
    _pet("Lucky", LocalDate.of(2010, 6, 24), dog, carlos)
    _pet("Sly", LocalDate.of(2012, 6, 8), cat, carlos)

    _visit(samantha, LocalDate.of(2013, 1, 1), "rabies shot")
    _visit(samantha, LocalDate.of(2013, 1, 4), "neutered")
    _visit(max_pet, LocalDate.of(2013, 1, 2), "rabies shot")
    _visit(max_pet, LocalDate.of(2013, 1, 3), "neutered")


def _vet(first_name: str, last_name: str, *specialties: Specialty) -> Vet:
    """Create a vet and its join-table specialty rows."""

    vet = vet_repository.save(Vet(firstName=first_name, lastName=last_name))
    for specialty in specialties:
        vet_specialty_repository.save(VetSpecialty(vetId=vet.id, specialtyId=specialty.id))
    return vet


def _owner(first_name: str, last_name: str, address: str, city: str, telephone: str) -> Owner:
    """Small helper that keeps the seed data readable."""

    return owner_repository.save(Owner(firstName=first_name, lastName=last_name, address=address, city=city, telephone=telephone))


def _pet(name: str, birth_date: LocalDate, pet_type: PetType, owner: Owner) -> Pet:
    """Create a pet with required non-null relation objects."""

    return pet_repository.save(Pet(name=name, birthDate=birth_date, type=pet_type, owner=owner))


def _visit(pet: Pet, visit_date: LocalDate, description: str) -> Visit:
    """Create a visit for an existing pet."""

    return visit_repository.save(Visit(date=visit_date, description=description, pet=pet))
