"""Disposable owners, pets and visits for functionality-level regressions."""

from types import SimpleNamespace
import uuid
import pytest


@pytest.fixture
def patients(application_context):
    import java
    context = application_context.java_ctx
    clinic = context.getBean(java.type('petclinic.services.ClinicService'))
    Owner = java.type('petclinic.models.Owner')
    Pet = java.type('petclinic.models.Pet')
    Visit = java.type('petclinic.models.Visit')
    LocalDate = java.type('java.time.LocalDate')
    Duration = java.type('java.time.Duration')
    Period = java.type('java.time.Period')
    List = java.type('java.util.List')
    owners, pets, visits = [], [], []

    def create_owner(telephone='6085551111', raw=False):
        candidate = Owner('Port', 'Update' + uuid.uuid4().hex[:10], '123 Test Street', 'Madison', telephone, None, List.of())
        repository = context.getBean(java.type('petclinic.repositories.OwnerRepository'))
        owner = repository.save(candidate) if raw else clinic.save_owner(candidate)
        owners.append(owner)
        return owner

    def create_pet(owner):
        pet = clinic.save_pet(Pet('Mittens', LocalDate.parse('2012-09-04'), clinic.find_pet_types()[0], owner, None, List.of()))
        pets.append(pet)
        return pet

    def create_visit(pet, day=1, raw=False):
        candidate = Visit(LocalDate.of(2025, 1, day), 'Routine visit ' + str(day), pet, None,
                          Duration.ofMinutes(30), Period.ofMonths(6))
        repository = context.getBean(java.type('petclinic.repositories.VisitRepository'))
        visit = repository.save(candidate) if raw else clinic.save_visit(candidate)
        visits.append(visit)
        return visit

    yield SimpleNamespace(clinic=clinic, owner=create_owner, pet=create_pet, visit=create_visit, context=context)
    visit_repository = context.getBean(java.type('petclinic.repositories.VisitRepository'))
    pet_repository = context.getBean(java.type('petclinic.repositories.PetRepository'))
    owner_repository = context.getBean(java.type('petclinic.repositories.OwnerRepository'))
    for visit in reversed(visits):
        visit_repository.deleteById(visit.id)
    for pet in reversed(pets):
        for visit in visit_repository.findByPetId(pet.id):
            visit_repository.deleteById(visit.id)
        pet_repository.deleteById(pet.id)
    for owner in reversed(owners):
        if owner_repository.existsById(owner.id):
            clinic.delete_owner(owner)
