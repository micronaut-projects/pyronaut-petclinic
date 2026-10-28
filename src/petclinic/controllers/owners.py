"""Owners HTTP routes and helpers."""

from typing import Annotated

from jakarta.inject import Inject
from jakarta.validation import Validator
from micronaut.http import HttpResponse, MediaType
from micronaut.http.annotation import Body, Get, Post, QueryValue
from micronaut.http.server.exceptions import NotFoundException
from micronaut.views import View
from petclinic.controllers.support import redirect_to, validation_errors
from petclinic.dtos.patients import OwnerForm
from petclinic.errors import entity_not_found
from petclinic.mapper import FormMapper
from petclinic.services.clinic import ClinicService
from petclinic.services.view_models import owner_search_model, owner_view_model

clinic_service: Annotated[ClinicService, Inject]
form_mapper: Annotated[FormMapper, Inject]
validator: Annotated[Validator, Inject]


@Get("/owners/find")
@View("owners/findOwners")
def init_find_form(notFound: Annotated[bool, QueryValue(defaultValue="false")] = False) -> dict:
    return {"owner": OwnerForm(), "notFound": notFound}


@Get("/owners")
def process_find_form(lastName: Annotated[str, QueryValue(defaultValue="")] = ""):
    """Search owners and follow the PetClinic redirect behavior."""

    owners = clinic_service.find_all_owners() if not lastName else clinic_service.find_owner_by_last_name(lastName)
    if len(owners) == 0:
        return redirect_to("/owners/find?notFound=true")
    if len(owners) == 1:
        return redirect_to(f"/owners/{owners[0].id}")
    return HttpResponse.ok({"owners": [owner_search_model(owner) for owner in owners], "lastName": lastName})


@Get("/owners/list")
@View("owners/ownersList")
def show_owner_list(lastName: Annotated[str, QueryValue(defaultValue="")] = "") -> dict:
    owners = clinic_service.find_all_owners() if not lastName else clinic_service.find_owner_by_last_name(lastName)
    return {"owners": [owner_view_model(owner) for owner in owners], "lastName": lastName}


@Get("/owners/new")
@View("owners/createOrUpdateOwnerForm")
def init_owner_creation_form() -> dict:
    return {"owner": OwnerForm(), "isNew": True, "validationErrors": {}}


@Post(value="/owners/new", consumes=MediaType.APPLICATION_FORM_URLENCODED)
@View("owners/createOrUpdateOwnerForm")
def process_owner_creation_form(form: Annotated[OwnerForm, Body]):
    """Bind, validate, map, persist, and redirect after owner creation."""

    errors = validation_errors(form, validator)
    if errors:
        return {"owner": form, "isNew": True, "validationErrors": errors}
    owner = clinic_service.save_owner(form_mapper.to_owner(form))
    return redirect_to(f"/owners/{owner.id}")


@Get("/owners/{ownerId}/edit")
@View("owners/createOrUpdateOwnerForm")
def init_owner_update_form(ownerId: int) -> dict:
    owner = clinic_service.find_owner_by_id(ownerId)
    if owner is None:
        raise NotFoundException()
    return {"owner": form_mapper.to_owner_form(owner), "ownerId": ownerId, "isNew": False, "validationErrors": {}}


@Post(value="/owners/{ownerId}/edit", consumes=MediaType.APPLICATION_FORM_URLENCODED)
@View("owners/createOrUpdateOwnerForm")
def process_owner_update_form(ownerId: int, form: Annotated[OwnerForm, Body]):
    existing = clinic_service.find_owner_by_id(ownerId)
    if existing is None:
        return entity_not_found()
    errors = validation_errors(form, validator)
    if errors:
        form.id = ownerId
        return {"owner": form, "ownerId": ownerId, "isNew": False, "validationErrors": errors}
    clinic_service.save_owner(form_mapper.update_owner(existing, form))
    return redirect_to(f"/owners/{ownerId}")


@Get("/owners/{ownerId}")
@View("owners/ownerDetails")
def show_owner(ownerId: int) -> dict:
    owner = clinic_service.find_owner_by_id(ownerId)
    if owner is None:
        raise NotFoundException()
    return {"owner": owner_view_model(owner)}
