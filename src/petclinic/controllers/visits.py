"""Visits HTTP routes and helpers."""

from typing import Annotated

from jakarta.inject import Inject
from jakarta.validation import Validator
from micronaut.http import HttpResponse, MediaType
from micronaut.http.annotation import Body, Get, Post
from micronaut.http.server.exceptions import NotFoundException
from micronaut.views import View
from petclinic.controllers.support import redirect_to, visit_errors, persist_visit
from petclinic.dtos.patients import VisitForm, VisitRequest
from petclinic.errors import entity_not_found
from petclinic.mapper import FormMapper
from petclinic.services.clinic import ClinicService
from petclinic.services.view_models import pet_view_model

clinic_service: Annotated[ClinicService, Inject]
form_mapper: Annotated[FormMapper, Inject]
validator: Annotated[Validator, Inject]


@Get("/owners/{ownerId}/pets/{petId}/visits/new")
@View("pets/createOrUpdateVisitForm")
def init_visit_creation_form(ownerId: int, petId: int) -> dict:
    pet = clinic_service.find_pet_by_id(petId)
    if pet is None:
        raise NotFoundException()
    return {"visit": VisitForm(), "pet": pet_view_model(pet), "owner": pet.owner, "validationErrors": {}}


@Post(value="/owners/{ownerId}/pets/{petId}/visits/new", consumes=MediaType.APPLICATION_JSON)
def process_visit_creation_json(ownerId: int, petId: int, request: Annotated[VisitRequest, Body]):
    pet = clinic_service.find_pet_by_id(petId)
    if pet is None:
        return entity_not_found()
    form = VisitForm(date=request.date, description=request.description,
                     durationMinutes=str(request.durationMinutes),
                     followUpPeriodMonths=str(request.followUpPeriodMonths))
    errors = visit_errors(form, validator)
    if errors:
        return HttpResponse.badRequest({"message": "Validation failed", "errors": errors})
    persist_visit(form, pet, clinic_service, form_mapper)
    return redirect_to(f"/owners/{ownerId}")
