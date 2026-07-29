"""PetClinic JSON API and React server-rendered browser routes."""

from typing import Annotated

from jakarta.inject import Inject
from jakarta.validation import Validator
from java.net import URI
from micronaut.http import HttpResponse, HttpStatus, MediaType
from micronaut.http.annotation import Body, Get, Post, Produces, Put, QueryValue
from micronaut.views import ModelAndView, View

from .forms import OwnerForm, PetForm, VisitForm
from .mapper import FormMapper
from .services import ClinicService

clinic_service: Annotated[ClinicService, Inject]
form_mapper: Annotated[FormMapper, Inject]
validator: Annotated[Validator, Inject]


def validation_errors(form) -> dict[str, str]:
    errors = {}
    for violation in validator.validate(form):
        field = str(violation.getPropertyPath()).rsplit(".", 1)[-1]
        if field:
            errors[field] = str(violation.getMessage())
    return errors


def invalid(errors: dict[str, str]):
    return HttpResponse.status(HttpStatus.UNPROCESSABLE_ENTITY).body({
        "message": "Validation failed",
        "errors": errors,
    })


def created(resource: dict, location: str):
    return HttpResponse.created(resource, URI.create(location))


def react_model(page: str, data: dict | None = None) -> dict:
    return {"page": page, "data": data or {}}


def not_found(message: str):
    return HttpResponse.notFound(ModelAndView("App", react_model("notFound", {"message": message})))


def pet_for_owner(owner_id: int, pet_id: int):
    pet = clinic_service.find_pet_by_id(pet_id)
    if pet is None or pet.owner is None or pet.owner.id != owner_id:
        return None
    return pet


@Get("/api/owners")
@Produces(MediaType.APPLICATION_JSON)
def api_owners(lastName: Annotated[str, QueryValue(defaultValue="")] = "") -> list[dict]:
    owners = clinic_service.find_all_owners() if not lastName else clinic_service.find_owner_by_last_name(lastName)
    return [clinic_service.owner_summary_model(owner) for owner in owners]


@Post("/api/owners")
@Produces(MediaType.APPLICATION_JSON)
def api_create_owner(form: Annotated[OwnerForm, Body]):
    errors = validation_errors(form)
    if errors:
        return invalid(errors)
    owner = clinic_service.save_owner(form_mapper.to_owner(form))
    model = clinic_service.owner_model(owner)
    return created(model, f"/api/owners/{owner.id}")


@Get("/api/owners/{ownerId}")
@Produces(MediaType.APPLICATION_JSON)
def api_owner(ownerId: int):
    owner = clinic_service.find_owner_by_id(ownerId)
    if owner is None:
        return HttpResponse.notFound()
    return clinic_service.owner_model(owner, include_pets=True)


@Put("/api/owners/{ownerId}")
@Produces(MediaType.APPLICATION_JSON)
def api_update_owner(ownerId: int, form: Annotated[OwnerForm, Body]):
    owner = clinic_service.find_owner_by_id(ownerId)
    if owner is None:
        return HttpResponse.notFound()
    errors = validation_errors(form)
    if errors:
        return invalid(errors)
    return clinic_service.owner_model(
        clinic_service.save_owner(form_mapper.update_owner(owner, form)),
        include_pets=True,
    )


@Get("/api/pet-types")
@Produces(MediaType.APPLICATION_JSON)
def api_pet_types() -> list[dict]:
    return clinic_service.pet_type_models()


@Post("/api/owners/{ownerId}/pets")
@Produces(MediaType.APPLICATION_JSON)
def api_create_pet(ownerId: int, form: Annotated[PetForm, Body]):
    owner = clinic_service.find_owner_by_id(ownerId)
    if owner is None:
        return HttpResponse.notFound()
    errors = validation_errors(form)
    pet_type = clinic_service.find_pet_type_by_id(form.typeId) if form.typeId is not None else None
    if form.typeId is not None and pet_type is None:
        errors["typeId"] = "Invalid pet type"
    if errors:
        return invalid(errors)
    pet = clinic_service.save_pet(form_mapper.to_pet(form, owner, pet_type))
    return created(clinic_service.pet_model(pet), f"/api/owners/{ownerId}/pets/{pet.id}")


@Get("/api/owners/{ownerId}/pets/{petId}")
@Produces(MediaType.APPLICATION_JSON)
def api_pet(ownerId: int, petId: int):
    pet = pet_for_owner(ownerId, petId)
    return HttpResponse.notFound() if pet is None else clinic_service.pet_model(pet, include_visits=True)


@Put("/api/owners/{ownerId}/pets/{petId}")
@Produces(MediaType.APPLICATION_JSON)
def api_update_pet(ownerId: int, petId: int, form: Annotated[PetForm, Body]):
    owner = clinic_service.find_owner_by_id(ownerId)
    pet = pet_for_owner(ownerId, petId)
    if owner is None or pet is None:
        return HttpResponse.notFound()
    errors = validation_errors(form)
    pet_type = clinic_service.find_pet_type_by_id(form.typeId) if form.typeId is not None else None
    if form.typeId is not None and pet_type is None:
        errors["typeId"] = "Invalid pet type"
    if errors:
        return invalid(errors)
    updated = clinic_service.save_pet(form_mapper.update_pet(pet, form, owner, pet_type))
    return clinic_service.pet_model(updated, include_visits=True)


@Post("/api/owners/{ownerId}/pets/{petId}/visits")
@Produces(MediaType.APPLICATION_JSON)
def api_create_visit(ownerId: int, petId: int, form: Annotated[VisitForm, Body]):
    pet = pet_for_owner(ownerId, petId)
    if pet is None:
        return HttpResponse.notFound()
    errors = validation_errors(form)
    if errors:
        return invalid(errors)
    visit = clinic_service.save_visit(form_mapper.to_visit(form, pet))
    return created(clinic_service.visit_model(visit), f"/api/owners/{ownerId}/pets/{petId}/visits/{visit.id}")


@Get("/api/vets")
@Produces(MediaType.APPLICATION_JSON)
def api_vets() -> list[dict]:
    return clinic_service.vet_models()


@Get("/vets/json")
@Produces(MediaType.APPLICATION_JSON)
def vets_json_alias() -> list[dict]:
    return clinic_service.vet_models()


@Get("/")
@View("App")
def welcome() -> dict:
    return react_model("welcome")


@Get("/owners/find")
@View("App")
def find_owners(notFound: Annotated[bool, QueryValue(defaultValue="false")] = False) -> dict:
    return react_model("ownerFind", {"notFound": notFound})


@Get("/owners")
@View("App")
def search_owners(lastName: Annotated[str, QueryValue(defaultValue="")] = ""):
    owners = clinic_service.find_all_owners() if not lastName else clinic_service.find_owner_by_last_name(lastName)
    if not owners:
        return HttpResponse.redirect(URI.create("/owners/find?notFound=true"))
    if len(owners) == 1:
        return HttpResponse.redirect(URI.create(f"/owners/{owners[0].id}"))
    return react_model("ownerList", {
        "lastName": lastName,
        "owners": [clinic_service.owner_summary_model(owner) for owner in owners],
    })


@Get("/owners/list")
@View("App")
def owner_list(lastName: Annotated[str, QueryValue(defaultValue="")] = "") -> dict:
    owners = clinic_service.find_all_owners() if not lastName else clinic_service.find_owner_by_last_name(lastName)
    return react_model("ownerList", {
        "lastName": lastName,
        "owners": [clinic_service.owner_summary_model(owner) for owner in owners],
    })


@Get("/owners/new")
@View("App")
def owner_create() -> dict:
    return react_model("ownerForm", {"owner": {}, "isNew": True})


@Get("/owners/{ownerId}")
@View("App")
def owner_detail(ownerId: int):
    owner = clinic_service.find_owner_by_id(ownerId)
    if owner is None:
        return not_found("Owner not found")
    return react_model("ownerDetail", {"owner": clinic_service.owner_model(owner, include_pets=True)})


@Get("/owners/{ownerId}/edit")
@View("App")
def owner_edit(ownerId: int):
    owner = clinic_service.find_owner_by_id(ownerId)
    if owner is None:
        return not_found("Owner not found")
    return react_model("ownerForm", {"owner": clinic_service.owner_model(owner), "isNew": False})


@Get("/owners/{ownerId}/pets/new")
@View("App")
def pet_create(ownerId: int):
    owner = clinic_service.find_owner_by_id(ownerId)
    if owner is None:
        return not_found("Owner not found")
    return react_model("petForm", {
        "owner": clinic_service.owner_summary_model(owner),
        "pet": {},
        "types": clinic_service.pet_type_models(),
        "isNew": True,
    })


@Get("/owners/{ownerId}/pets/{petId}/edit")
@View("App")
def pet_edit(ownerId: int, petId: int):
    pet = pet_for_owner(ownerId, petId)
    if pet is None:
        return not_found("Pet not found")
    return react_model("petForm", {
        "owner": clinic_service.owner_summary_model(pet.owner),
        "pet": clinic_service.pet_model(pet),
        "types": clinic_service.pet_type_models(),
        "isNew": False,
    })


@Get("/owners/{ownerId}/pets/{petId}/visits/new")
@View("App")
def visit_create(ownerId: int, petId: int):
    pet = pet_for_owner(ownerId, petId)
    if pet is None:
        return not_found("Pet not found")
    return react_model("visitForm", {
        "owner": clinic_service.owner_summary_model(pet.owner),
        "pet": clinic_service.pet_model(pet),
    })


@Get("/vets")
@View("App")
def vets() -> dict:
    return react_model("vets", {"vets": clinic_service.vet_models()})


@Get("/vets/html")
@View("App")
def vets_html() -> dict:
    return vets()
