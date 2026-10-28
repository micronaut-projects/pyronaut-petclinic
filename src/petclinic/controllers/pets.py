"""Pets HTTP routes and helpers."""

from typing import Annotated

from jakarta.inject import Inject
from jakarta.validation import Validator
from micronaut.http import HttpResponse, MediaType
from micronaut.http.annotation import Body, Get, Post
from micronaut.http.server.exceptions import NotFoundException
from micronaut.views import View
from petclinic.controllers.support import redirect_to, validation_errors, pet_type_for, parse_form_date
from petclinic.dtos.patients import PetForm
from petclinic.errors import entity_not_found
from petclinic.mapper import FormMapper
from petclinic.services.clinic import ClinicService

clinic_service: Annotated[ClinicService, Inject]

form_mapper: Annotated[FormMapper, Inject]

validator: Annotated[Validator, Inject]


@Get("/owners/{ownerId}/pets/new")
@View("pets/createOrUpdatePetForm")
def init_pet_creation_form(ownerId: int) -> dict:
    owner = clinic_service.find_owner_by_id(ownerId)
    if owner is None or owner.id != ownerId:
        raise NotFoundException()
    return {"pet": PetForm(), "owner": owner, "types": clinic_service.find_pet_types(), "isNew": True,
            "validationErrors": {}}


@Post(value="/owners/{ownerId}/pets/new", consumes=MediaType.APPLICATION_FORM_URLENCODED)
@View("pets/createOrUpdatePetForm")
def process_pet_creation_form(ownerId: int, form: Annotated[PetForm, Body]):
    """Create a pet from a form DTO.

    ``PetForm`` carries a scalar ``typeId``. The controller resolves that ID to
    the ``PetType`` entity before calling the generated mapper.
    """

    owner = clinic_service.find_owner_by_id(ownerId)
    if owner is None:
        return entity_not_found()
    errors = validation_errors(form, validator)
    pet_type = pet_type_for(form, errors, clinic_service)
    if errors:
        return {"pet": form, "owner": owner, "types": clinic_service.find_pet_types(), "isNew": True,
                "validationErrors": errors}
    if pet_type is None:
        return HttpResponse.badRequest("Invalid pet type")
    form.birthDateValue = parse_form_date(form.birthDate)
    pet = form_mapper.to_pet(form, owner, pet_type)
    clinic_service.save_pet(pet)
    return redirect_to(f"/owners/{ownerId}")


@Get("/owners/{ownerId}/pets/{petId}/edit")
@View("pets/createOrUpdatePetForm")
def init_pet_update_form(ownerId: int, petId: int) -> dict:
    pet = clinic_service.find_pet_by_id(petId)
    if pet is None:
        raise NotFoundException()
    owner = pet.owner or clinic_service.find_owner_by_id(ownerId)
    return {"pet": form_mapper.to_pet_form(pet), "petId": petId, "owner": owner,
            "types": clinic_service.find_pet_types(), "isNew": False, "validationErrors": {}}


@Post(value="/owners/{ownerId}/pets/{petId}/edit", consumes=MediaType.APPLICATION_FORM_URLENCODED)
@View("pets/createOrUpdatePetForm")
def process_pet_update_form(ownerId: int, petId: int, form: Annotated[PetForm, Body]):
    owner = clinic_service.find_owner_by_id(ownerId)
    pet = clinic_service.find_pet_by_id(petId)
    if owner is None or pet is None:
        return entity_not_found()
    errors = validation_errors(form, validator)
    pet_type = pet_type_for(form, errors, clinic_service)
    if errors:
        form.id = petId
        return {"pet": form, "petId": petId, "owner": owner, "types": clinic_service.find_pet_types(), "isNew": False,
                "validationErrors": errors}
    if pet_type is None:
        return HttpResponse.badRequest("Invalid pet type")
    form.birthDateValue = parse_form_date(form.birthDate)
    updated = form_mapper.update_pet(pet, form, owner, pet_type)
    clinic_service.save_pet(updated)
    return redirect_to(f"/owners/{ownerId}")
