"""Simple Python-backed view renderer for ``@View`` routes.

Micronaut Views calls into this renderer through the small Java bridge in
``src-java``. The renderer intentionally uses Python's ``string.Template`` so
new Pyronaut users can understand the full rendering path without learning a
separate template language.

Important concepts shown here:

* Controllers return dictionaries as view models.
* ``render_view`` loads ``views/<name>.html.template``.
* Dynamic values pass through ``h`` for HTML escaping by default.
* Layout composition is explicit Python code instead of framework magic.
"""

from pathlib import Path
from string import Template
from html import escape as html_escape


ROOT = Path.cwd()
VIEWS = ROOT / "views"


class TemplateNotFoundError(RuntimeError):
    """Raised when a controller references a missing template."""

    pass


def h(value) -> str:
    """Escape a value for safe HTML output."""

    if value is None:
        return ""
    return html_escape(str(value), quote=True)


def exists(view_name: str) -> bool:
    """Return whether a view template exists."""

    if view_name.startswith("_"):
        return False
    return _template_path(view_name).is_file()


def render_view(view_name: str, model=None) -> str:
    """Render a named view with an optional Micronaut or Python model."""

    model = _to_dict(model)
    path = _template_path(view_name)
    if not path.is_file():
        raise TemplateNotFoundError(f"Template not found: {view_name}")
    body = _render_template(path, _context_for(view_name, model))
    if view_name == "layout":
        return body
    return layout(_title_for(view_name), body, view_name)


def layout(title: str, body: str, active: str = "") -> str:
    """Wrap page content in the shared PetClinic layout."""

    path = _template_path("_layout")
    return _render_template(path, {
        "title": h(title),
        "body": body,
        "owners_active": "active" if active.startswith("owners") else "",
        "vets_active": "active" if active.startswith("vets") else "",
        "home_active": "active" if active == "welcome" else "",
    })


def _template_path(view_name: str) -> Path:
    return VIEWS / f"{view_name}.html.template"


def _fragment(name: str, context: dict | None = None) -> str:
    """Render a reusable HTML fragment from ``views/fragments``."""

    return _render_template(VIEWS / "fragments" / f"{name}.html.template", context or {})


def _render_template(path: Path, context: dict) -> str:
    return Template(path.read_text(encoding="utf-8")).safe_substitute(context)


def _to_dict(model) -> dict:
    """Convert Java map-like models and Python dicts to a Python dict."""

    if model is None:
        return {}
    if isinstance(model, dict):
        return model
    if hasattr(model, "items"):
        return {str(entry.getKey()): entry.getValue() for entry in model.entrySet()}
    return {}


def _context_for(view_name: str, model: dict) -> dict:
    context = {key: h(value) for key, value in model.items()}
    if view_name == "owners/findOwners":
        context.update(_find_owners_context(model))
    elif view_name == "owners/ownersList":
        context.update(_owners_list_context(model))
    elif view_name == "owners/ownerDetails":
        context.update(_owner_details_context(model))
    elif view_name == "owners/createOrUpdateOwnerForm":
        context.update(_owner_form_context(model))
    elif view_name == "pets/createOrUpdatePetForm":
        context.update(_pet_form_context(model))
    elif view_name == "pets/createOrUpdateVisitForm":
        context.update(_visit_form_context(model))
    elif view_name == "vets/vetList":
        context.update(_vet_list_context(model))
    elif view_name.startswith("error"):
        context["message"] = h(model.get("message", "Something happened."))
    return context


def _title_for(view_name: str) -> str:
    return {
        "welcome": "Welcome",
        "owners/findOwners": "Find Owners",
        "owners/ownersList": "Owners",
        "owners/ownerDetails": "Owner Details",
        "owners/createOrUpdateOwnerForm": "Owner",
        "pets/createOrUpdatePetForm": "Pet",
        "pets/createOrUpdateVisitForm": "Visit",
        "vets/vetList": "Veterinarians",
    }.get(view_name, "PetClinic")


def _error(errors: dict, field: str) -> str:
    if field not in errors:
        return ""
    return h(errors[field])


def _invalid_class(errors: dict, field: str) -> str:
    return "is-invalid" if field in errors else ""


def _validation_summary(errors: dict) -> str:
    if not errors:
        return ""
    return _fragment("validation-summary")


def _find_owners_context(model: dict) -> dict:
    alert = ""
    if bool(model.get("notFound")):
        alert = _fragment("find-not-found-alert")
    owner = model.get("owner")
    return {"not_found": alert, "last_name": h(_get(owner, "lastName", ""))}


def _owners_list_context(model: dict) -> dict:
    owners = model.get("owners", [])
    if not owners:
        return {
            "owner_count": "0",
            "owners_content": _fragment("owners-empty"),
        }

    cards = []
    for owner in model.get("owners", []):
        pets = _get(owner, "pets", []) or []
        if pets:
            pets_html = "".join(
                _fragment("pet-badge", {"name": h(_get(pet, "name"))})
                for pet in pets
            )
        else:
            pets_html = _fragment("no-pets-registered")
        cards.append(_fragment("owner-card", {
            "owner_id": h(_get(owner, "id")),
            "initials": _owner_initials(owner),
            "first_name": h(_get(owner, "firstName")),
            "last_name": h(_get(owner, "lastName")),
            "city": h(_get(owner, "city")),
            "address": h(_get(owner, "address")),
            "telephone": h(_get(owner, "telephone")),
            "pets_html": pets_html,
        }))
    return {"owner_count": h(len(owners)), "owners_content": _fragment("card-row", {"content": "".join(cards)})}


def _owner_details_context(model: dict) -> dict:
    owner = model.get("owner")
    if owner is None:
        return {"owner_block": _fragment("owner-not-found")}
    pets = model.get("pets", [])
    if not pets:
        pets_block = _fragment("owner-no-pets", {"owner_id": h(owner.id)})
    else:
        pet_cards = []
        for pet in pets:
            visits = _visit_timeline(_get(pet, "visits", []))
            pet_cards.append(_fragment("pet-detail-card", {
                "owner_id": h(owner.id),
                "pet_id": h(_get(pet, "id")),
                "pet_icon": _pet_icon(pet, "me-3"),
                "pet_name": h(_get(pet, "name")),
                "pet_type": h(_pet_type_name(pet)),
                "birth_date": h(_get(pet, "birthDate", "")),
                "visits": visits,
            }))
        pets_block = "".join(pet_cards)

    block = _fragment("owner-details", {
        "owner_id": h(owner.id),
        "initials": _owner_initials(owner),
        "first_name": h(owner.firstName),
        "last_name": h(owner.lastName),
        "address": h(owner.address),
        "city": h(owner.city),
        "telephone": h(owner.telephone),
        "pet_count": h(len(pets)),
        "pets_block": pets_block,
    })
    return {"owner_block": block}


def _owner_form_context(model: dict) -> dict:
    owner = model.get("owner")
    errors = model.get("validationErrors", {})
    is_new = bool(model.get("isNew", True))
    action = "/owners/new" if is_new else f"/owners/{model.get('ownerId', getattr(owner, 'id', ''))}/edit"
    label = "Add Owner" if is_new else "Update Owner"
    owner_id = model.get("ownerId", getattr(owner, "id", ""))
    back_url = "/owners/find" if is_new else f"/owners/{owner_id}"
    return {
        "form_action": h(action),
        "back_url": h(back_url),
        "header_icon": "fas fa-user-plus me-3" if is_new else "fas fa-user-edit me-3",
        "header_title": "New Owner" if is_new else "Edit Owner",
        "form_description": "Register a new pet owner" if is_new else "Update owner information",
        "button_label": h(label),
        "button_icon": "fas fa-plus me-2" if is_new else "fas fa-save me-2",
        "first_name": h(getattr(owner, "firstName", "")),
        "last_name": h(getattr(owner, "lastName", "")),
        "address_value": h(getattr(owner, "address", "")),
        "city_value": h(getattr(owner, "city", "")),
        "telephone": h(getattr(owner, "telephone", "")),
        "validation_summary": _validation_summary(errors),
        "first_invalid": _invalid_class(errors, "firstName"),
        "last_invalid": _invalid_class(errors, "lastName"),
        "address_invalid": _invalid_class(errors, "address"),
        "city_invalid": _invalid_class(errors, "city"),
        "telephone_invalid": _invalid_class(errors, "telephone"),
        "first_error": _error(errors, "firstName") or "First name is required.",
        "last_error": _error(errors, "lastName") or "Last name is required.",
        "address_error": _error(errors, "address") or "Address is required.",
        "city_error": _error(errors, "city") or "City is required.",
        "telephone_error": _error(errors, "telephone") or "Please enter a valid telephone number (10 digits)",
    }


def _pet_form_context(model: dict) -> dict:
    if "error" in model:
        message = h(model.get("error"))
        return {
            "form_action": "",
            "button_label": "",
            "button_icon": "",
            "header_icon": "fas fa-paw me-3",
            "header_title": "Pet",
            "form_description": "",
            "back_url": "/owners/find",
            "owner_name": "",
            "pet_name": "",
            "pet_form_title": "",
            "pet_form_subtitle": "",
            "birth_date": "",
            "type_options": "",
            "validation_summary": "",
            "name_invalid": "",
            "birth_invalid": "",
            "type_invalid": "",
            "name_error": "",
            "birth_error": "",
            "type_feedback": "",
            "type_error": _fragment("warning-alert", {"message": message}),
        }
    pet = model.get("pet")
    owner = model.get("owner")
    errors = model.get("validationErrors", {})
    is_new = bool(model.get("isNew", True))
    owner_id = getattr(owner, "id", "")
    pet_id = model.get("petId", getattr(pet, "id", ""))
    action = f"/owners/{owner_id}/pets/new" if is_new else f"/owners/{owner_id}/pets/{pet_id}/edit"
    type_id = _get(pet, "typeId")
    options = []
    for pet_type in model.get("types", []):
        selected = " selected" if pet_type.id == type_id else ""
        options.append(_fragment("type-option", {
            "value": h(pet_type.id),
            "selected": selected,
            "label": h(pet_type.name),
        }))
    return {
        "form_action": h(action),
        "back_url": h(f"/owners/{owner_id}"),
        "header_icon": "fas fa-paw me-3",
        "header_title": "New Pet" if is_new else "Edit Pet",
        "form_description": "Register a new pet" if is_new else "Update pet information",
        "button_label": "Add Pet" if is_new else "Update",
        "button_icon": "fas fa-plus me-2" if is_new else "fas fa-save me-2",
        "owner_name": f"{h(getattr(owner, 'firstName', ''))} {h(getattr(owner, 'lastName', ''))}",
        "pet_form_title": "Register a New Pet" if is_new else "Update Pet Information",
        "pet_form_subtitle": f"Owner: {h(getattr(owner, 'firstName', ''))} {h(getattr(owner, 'lastName', ''))}",
        "pet_name": h(getattr(pet, "name", "")),
        "birth_date": h(getattr(pet, "birthDate", "") or ""),
        "type_options": "\n".join(options),
        "validation_summary": _validation_summary(errors),
        "name_invalid": _invalid_class(errors, "name"),
        "birth_invalid": _invalid_class(errors, "birthDate"),
        "type_invalid": _invalid_class(errors, "typeId"),
        "name_error": _error(errors, "name") or "Pet name is required.",
        "birth_error": _error(errors, "birthDate") or "Birth date is required.",
        "type_feedback": _error(errors, "typeId") or "Please select a pet type.",
        "type_error": "",
    }


def _visit_form_context(model: dict) -> dict:
    if "error" in model:
        message = h(model.get("error"))
        return {
            "form_action": "",
            "back_url": "/owners/find",
            "owner_name": "",
            "pet_name": "",
            "pet_information": _fragment("warning-alert", {"message": message}),
            "visit_date": "",
            "description": "",
            "validation_summary": "",
            "date_invalid": "",
            "description_invalid": "",
            "date_error": "",
            "description_error": "",
        }
    visit = model.get("visit")
    pet = model.get("pet")
    owner = model.get("owner")
    errors = model.get("validationErrors", {})
    action = f"/owners/{getattr(owner, 'id', '')}/pets/{getattr(pet, 'id', '')}/visits/new"
    visits = _get(pet, "visits", []) or []
    previous_visits = ""
    if visits:
        previous_visits = _fragment("previous-visits", {"visits": _visit_timeline_list(visits)})
    owner_name = f"{h(getattr(owner, 'firstName', ''))} {h(getattr(owner, 'lastName', ''))}"
    pet_information = _fragment("visit-pet-information", {
        "pet_icon": _pet_icon(pet, "mx-auto mb-3", 'style="width: 80px; height: 80px; font-size: 2rem;"'),
        "pet_name": h(_get(pet, "name")),
        "pet_type": h(_pet_type_name(pet)),
        "birth_date": h(_get(pet, "birthDate", "")),
        "owner_name": owner_name,
        "previous_visits": previous_visits,
    })
    return {
        "form_action": h(action),
        "back_url": h(f"/owners/{getattr(owner, 'id', '')}"),
        "owner_name": owner_name,
        "pet_name": h(getattr(pet, "name", "")),
        "pet_information": pet_information,
        "visit_date": h(getattr(visit, "date", "") or ""),
        "description": h(getattr(visit, "description", "")),
        "validation_summary": _validation_summary(errors),
        "date_invalid": _invalid_class(errors, "date"),
        "description_invalid": _invalid_class(errors, "description"),
        "date_error": _error(errors, "date") or "Visit date is required.",
        "description_error": _error(errors, "description") or "Description is required.",
    }


def _vet_list_context(model: dict) -> dict:
    vets = model.get("vets", [])
    if not vets:
        return {
            "vet_count": "0",
            "vets_content": _fragment("vets-empty"),
        }
    cards = []
    for vet in vets:
        specialities = _get(vet, "specialitiesAsString")
        if specialities and specialities != "none":
            speciality_html = "".join(
                _fragment("speciality-badge", {"name": h(s.strip())})
                for s in str(specialities).split(",")
            )
        else:
            speciality_html = _fragment("speciality-badge", {"name": "General Practice"})
        cards.append(_fragment("vet-card", {
            "first_name": h(_get(vet, "firstName")),
            "last_name": h(_get(vet, "lastName")),
            "specialities": speciality_html,
        }))
    return {"vet_count": h(len(vets)), "vets_content": _fragment("card-row", {"content": "".join(cards)})}


def _owner_initials(owner) -> str:
    first = str(_get(owner, "firstName", "") or "")
    last = str(_get(owner, "lastName", "") or "")
    return h((first[:1] or "?") + (last[:1] or "?"))


def _pet_type_name(pet) -> str:
    pet_type = _get(pet, "type")
    if pet_type is None:
        return "Unknown"
    return _get(pet_type, "name", pet_type) or "Unknown"


def _pet_icon(pet, extra_class: str = "", extra_attrs: str = "") -> str:
    pet_type = str(_pet_type_name(pet)).strip().lower()
    icon = {
        "cat": "fa-cat",
        "bird": "fa-dove",
        "hamster": "fa-hippo",
        "snake": "fa-worm",
    }.get(pet_type, "fa-dog")
    css_type = pet_type if pet_type in {"cat", "dog", "bird", "hamster", "snake", "lizard"} else "dog"
    attrs = f" {extra_attrs}" if extra_attrs else ""
    return _fragment("pet-icon", {
        "type": h(css_type),
        "extra_class": h(extra_class),
        "extra_attrs": attrs,
        "icon": icon,
    })


def _visit_timeline(visits) -> str:
    if not visits:
        return ""
    return _fragment("visit-timeline", {"visits": _visit_timeline_list(visits)})


def _visit_timeline_list(visits) -> str:
    items = []
    for visit in visits:
        items.append(_fragment("visit-item", {
            "date": h(_get(visit, "date", "")),
            "description": h(_get(visit, "description", "")),
        }))
    return _fragment("visit-timeline-list", {"items": "".join(items)})


def _get(value, key: str, default=None):
    if value is None:
        return default
    if isinstance(value, dict):
        return value.get(key, default)
    attr = getattr(value, key, default)
    if attr is not default:
        return attr
    getter = getattr(value, f"get{key[0].upper()}{key[1:]}", None)
    if getter is not None:
        return getter()
    return default
