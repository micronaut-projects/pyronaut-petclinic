"""Pets HTTP routes and helpers."""

from typing import Annotated

from jakarta.inject import Inject
from jakarta.validation import Validator
from micronaut.http import HttpResponse, MediaType
from micronaut.http.exceptions import HttpStatusException
from micronaut.http.annotation import Body, Get, Post
from micronaut.http.server.exceptions import NotFoundException
from micronaut.views import View, ModelAndView
from petclinic.controllers.support import redirect_to, validation_errors, pet_type_for, parse_form_date, page_owner, page_pet
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
    owner = page_owner(clinic_service, ownerId)
    return {"pet": PetForm(), "owner": owner, "types": clinic_service.find_pet_types(), "isNew": True,
            "validationErrors": {}}


@Post(value="/owners/{ownerId}/pets/new", consumes=MediaType.APPLICATION_FORM_URLENCODED)
@View("pets/createOrUpdatePetForm")
def process_pet_creation_form(ownerId: int, form: Annotated[PetForm, Body]):
    """Create a pet from a form DTO.

    ``PetForm`` carries a scalar ``typeId``. The controller resolves that ID to
    the ``PetType`` entity before calling the generated mapper.
    """

    errors = validation_errors(form, validator)
    try:
        owner = clinic_service.find_owner_by_id(ownerId)
    except HttpStatusException:
        if errors:
            return HttpResponse.notFound(ModelAndView('error/404', {'path': f'/owners/{ownerId}/pets/new', 'message': 'Entity not found.'}))
        raise
    pet_type = pet_type_for(form, errors, clinic_service)
    if errors:
        form.id = None
        return HttpResponse.badRequest(ModelAndView("pets/createOrUpdatePetForm", {"pet": form, "owner": owner, "types": clinic_service.find_pet_types(), "isNew": True,
                "validationErrors": errors}))
    if pet_type is None:
        return HttpResponse.badRequest("Invalid pet type")
    form.birthDateValue = parse_form_date(form.birthDate)
    pet = form_mapper.to_pet(form, owner, pet_type)
    clinic_service.save_pet(pet)
    return redirect_to(f"/owners/{ownerId}")


@Get("/owners/{ownerId}/pets/{petId}/edit")
@View("pets/createOrUpdatePetForm")
def init_pet_update_form(ownerId: int, petId: int) -> dict:
    pet = page_pet(clinic_service, petId)
    owner = pet.owner or clinic_service.find_owner_by_id(ownerId)
    return {"pet": form_mapper.to_pet_form(pet), "petId": petId, "owner": owner,
            "types": clinic_service.find_pet_types(), "isNew": False, "validationErrors": {}}


@Post(value="/owners/{ownerId}/pets/{petId}/edit", consumes=MediaType.APPLICATION_FORM_URLENCODED)
@View("pets/createOrUpdatePetForm")
def process_pet_update_form(ownerId: int, petId: int, form: Annotated[PetForm, Body]):
    errors = validation_errors(form, validator)
    try:
        owner = clinic_service.find_owner_by_id(ownerId)
    except HttpStatusException:
        if errors:
            return HttpResponse.notFound(ModelAndView('error/404', {'path': f'/owners/{ownerId}/pets/{petId}/edit', 'message': 'Entity not found.'}))
        raise
    pet_type = pet_type_for(form, errors, clinic_service)
    if errors:
        form.id = petId
        return HttpResponse.badRequest(ModelAndView("pets/createOrUpdatePetForm", {"pet": form, "petId": petId, "owner": owner, "types": clinic_service.find_pet_types(), "isNew": False,
                "validationErrors": errors}))
    pet = clinic_service.find_pet_by_id(petId)
    if pet_type is None:
        return HttpResponse.badRequest("Invalid pet type")
    form.birthDateValue = parse_form_date(form.birthDate)
    updated = form_mapper.update_pet(pet, form, owner, pet_type)
    clinic_service.save_pet(updated)
    return redirect_to(f"/owners/{ownerId}")
