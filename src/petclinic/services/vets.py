"""Vets application services."""

from typing import Annotated

from jakarta.inject import Inject, Singleton
from jakarta.transaction import Transactional
from micronaut.data.exceptions import OptimisticLockException
from micronaut.http import HttpStatus
from micronaut.http.exceptions import HttpStatusException
from petclinic.dtos.vets import VetForm, SpecialityForm
from petclinic.etags import speciality_hash
from petclinic.models.vets import Speciality, Vet
from petclinic.repositories.vets import SpecialityRepository, VetRepository, VetSpecialityRepository


def domain_error(status: HttpStatus, message: str):
    raise HttpStatusException(status, message)


def expected_etag(value: str | None) -> str:
    if value is None or not value.strip():
        domain_error(HttpStatus.PRECONDITION_REQUIRED, 'ETag is missing.')
    return value[1:-1] if len(value) >= 2 and value.startswith('"') and value.endswith('"') else value


@Singleton
class VetService:
    vets: Annotated[VetRepository, Inject]
    specialities: Annotated[SpecialityRepository, Inject]
    links: Annotated[VetSpecialityRepository, Inject]

    def enriched(self, row) -> Vet:
        return Vet(id=row.id, firstName=row.firstName, lastName=row.lastName,
                   specialitiesHash=row.specialitiesHash, etag=row.etag,
                   specialities=list(self.links.findSpecialitiesByVetId(row.id)))

    def find_all(self) -> list[Vet]:
        return [self.enriched(v) for v in self.vets.findAllOrderByLastName()]

    def find(self, id: int) -> Vet:
        row = self.vets.findOneById(id)
        if row is None:
            domain_error(HttpStatus.NOT_FOUND, 'Entity not found.')
        return self.enriched(row)

    def find_speciality(self, id: int) -> Speciality:
        speciality = self.specialities.findOneById(id)
        if speciality is None:
            domain_error(HttpStatus.NOT_FOUND, 'Entity not found.')
        return speciality

    def resolve(self, ids) -> list[Speciality]:
        values = list(ids or [])
        # A Java null in an Object collection is GraalPy ForeignNone, whose
        # identity is different from Python None. Compare null values directly.
        if any(id is None or id == None for id in values):
            domain_error(HttpStatus.BAD_REQUEST, 'Each speciality must have an id.')
        if any(not isinstance(id, int) or isinstance(id, bool) or
               not -2147483648 <= id <= 2147483647 for id in values):
            domain_error(HttpStatus.BAD_REQUEST, 'Invalid request value.')
        requested = set(values)
        resolved = list(self.specialities.findAllByIdIn(sorted(requested))) if requested else []
        if len(resolved) != len(requested):
            domain_error(HttpStatus.BAD_REQUEST, 'One or more specialities were not found.')
        return resolved

    @Transactional
    def create(self, form: VetForm) -> Vet:
        selected = self.resolve(form.specialityIds)
        row = self.vets.save(Vet(firstName=form.firstName, lastName=form.lastName,
                                 specialitiesHash=speciality_hash(s.id for s in selected)))
        for speciality in selected:
            self.vets.insertSpecialityLink(row.id, speciality.id)
        return self.find(row.id)

    @Transactional
    def update(self, id: int, form: VetForm, etag: str | None) -> Vet:
        current = self.find(id)
        version = expected_etag(etag)
        selected = self.resolve(form.specialityIds)
        updated = Vet(id=current.id, firstName=form.firstName, lastName=form.lastName,
                      specialitiesHash=speciality_hash(s.id for s in selected), etag=version)
        try:
            self.vets.deleteSpecialityLinks(id)
            self.vets.update(updated)
            for speciality in selected:
                self.vets.insertSpecialityLink(id, speciality.id)
        except OptimisticLockException:
            domain_error(HttpStatus.PRECONDITION_FAILED, 'The entity etag has changed since it was loaded.')
        return self.find(id)

    @Transactional
    def delete(self, id: int, etag: str | None) -> None:
        version = expected_etag(etag)
        current = self.find(id)
        try:
            self.vets.deleteSpecialityLinks(id)
            self.vets.delete(Vet(id=id, firstName=current.firstName, lastName=current.lastName,
                                 specialitiesHash=current.specialitiesHash, etag=version))
        except OptimisticLockException:
            domain_error(HttpStatus.PRECONDITION_FAILED, 'The entity etag has changed since it was loaded.')

    def unique_speciality(self, name: str, current_id: int | None):
        existing = self.specialities.findByName(name)
        if existing is not None and existing.id != current_id:
            domain_error(HttpStatus.BAD_REQUEST, 'Speciality name already exists.')

    def create_speciality(self, form: SpecialityForm) -> Speciality:
        self.unique_speciality(form.name, None)
        return self.specialities.save(Speciality(name=form.name))

    def update_speciality(self, id: int, form: SpecialityForm) -> Speciality:
        self.find_speciality(id)
        self.unique_speciality(form.name, id)
        return self.specialities.update(Speciality(id=id, name=form.name))
