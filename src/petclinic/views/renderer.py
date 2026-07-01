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
    body = Template(path.read_text(encoding="utf-8")).safe_substitute(_context_for(view_name, model))
    if view_name == "layout":
        return body
    return layout(_title_for(view_name), body, view_name)


def layout(title: str, body: str, active: str = "") -> str:
    """Wrap page content in the shared PetClinic layout."""

    path = _template_path("_layout")
    return Template(path.read_text(encoding="utf-8")).safe_substitute({
        "title": h(title),
        "body": body,
        "owners_active": "active" if active.startswith("owners") else "",
        "vets_active": "active" if active.startswith("vets") else "",
        "home_active": "active" if active == "welcome" else "",
    })


def _template_path(view_name: str) -> Path:
    return VIEWS / f"{view_name}.html.template"


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
    return '<div class="alert alert-danger" role="alert">Please fix the errors below.</div>'


def _find_owners_context(model: dict) -> dict:
    alert = ""
    if bool(model.get("notFound")):
        alert = (
            '<div class="alert alert-warning animate-fade-in-up">'
            '<i class="fas fa-exclamation-triangle"></i>'
            "Try a different search or add a new owner"
            "</div>"
        )
    owner = model.get("owner")
    return {"not_found": alert, "last_name": h(_get(owner, "lastName", ""))}


def _owners_list_context(model: dict) -> dict:
    owners = model.get("owners", [])
    if not owners:
        return {
            "owner_count": "0",
            "owners_content": """
<div class="empty-state">
    <div class="empty-state-icon">
        <i class="fas fa-users-slash"></i>
    </div>
    <h3>No Owners Found</h3>
    <p>We couldn't find any owners matching your search criteria.</p>
    <a href="/owners/new" class="btn btn-success">
        <i class="fas fa-plus me-2"></i>Add New Owner
    </a>
</div>
""",
        }

    cards = []
    for owner in model.get("owners", []):
        pets = _get(owner, "pets", []) or []
        if pets:
            pets_html = "".join(
                f'<span class="pet-badge"><i class="fas fa-paw"></i>{h(_get(pet, "name"))}</span>'
                for pet in pets
            )
        else:
            pets_html = '<span class="text-muted small"><i class="fas fa-info-circle me-1"></i>No pets registered</span>'
        cards.append(
            f"""
<div class="col-md-6 col-lg-4">
    <div class="owner-card animate-fade-in-up">
        <div class="d-flex align-items-start mb-3">
            <div class="owner-avatar me-3">
                <span>{_owner_initials(owner)}</span>
            </div>
            <div class="flex-grow-1">
                <h5 class="mb-1">
                    <a href="/owners/{_get(owner, "id")}" class="text-decoration-none text-dark">
                        {h(_get(owner, "firstName"))} {h(_get(owner, "lastName"))}
                    </a>
                </h5>
                <p class="text-muted mb-0 small">
                    <i class="fas fa-map-marker-alt me-1"></i>{h(_get(owner, "city"))}
                </p>
            </div>
        </div>

        <div class="mb-3">
            <p class="mb-1 small text-muted">
                <i class="fas fa-home me-2"></i>{h(_get(owner, "address"))}
            </p>
            <p class="mb-0 small text-muted">
                <i class="fas fa-phone me-2"></i>{h(_get(owner, "telephone"))}
            </p>
        </div>

        <div class="mb-3">
            <div class="d-flex flex-wrap">
                {pets_html}
            </div>
        </div>

        <a href="/owners/{_get(owner, "id")}" class="btn btn-primary btn-sm w-100">
            <i class="fas fa-eye me-2"></i>View Details
        </a>
    </div>
</div>
"""
        )
    return {"owner_count": h(len(owners)), "owners_content": f'<div class="row g-4">{"".join(cards)}</div>'}


def _owner_details_context(model: dict) -> dict:
    owner = model.get("owner")
    if owner is None:
        return {"owner_block": '<div class="alert alert-warning">Owner not found</div>'}
    pets = model.get("pets", [])
    if not pets:
        pets_block = f"""
<div class="text-center py-5">
    <div class="empty-state-icon mx-auto mb-3" style="width: 80px; height: 80px; font-size: 2rem;">
        <i class="fas fa-paw"></i>
    </div>
    <h5>No Pets Yet</h5>
    <p class="text-muted">This owner hasn't registered any pets.</p>
    <a href="/owners/{owner.id}/pets/new" class="btn btn-success">
        <i class="fas fa-plus me-2"></i>Add First Pet
    </a>
</div>
"""
    else:
        pet_cards = []
        for pet in pets:
            visits = _visit_timeline(_get(pet, "visits", []))
            pet_cards.append(
                f"""
<div class="pet-card mb-3">
    <div class="row align-items-center">
        <div class="col-md-4">
            <div class="d-flex align-items-center">
                {_pet_icon(pet, "me-3")}
                <div>
                    <h6 class="mb-0">{h(_get(pet, "name"))}</h6>
                    <small class="text-muted">{h(_pet_type_name(pet))}</small>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <small class="text-muted d-block">Birth Date</small>
            <span>{h(_get(pet, "birthDate", ""))}</span>
        </div>
        <div class="col-md-5 text-md-end mt-3 mt-md-0">
            <a href="/owners/{owner.id}/pets/{_get(pet, "id")}/edit" class="btn btn-sm btn-outline-primary me-2">
                <i class="fas fa-edit"></i> Edit
            </a>
            <a href="/owners/{owner.id}/pets/{_get(pet, "id")}/visits/new" class="btn btn-sm btn-primary">
                <i class="fas fa-plus"></i> Add Visit
            </a>
        </div>
    </div>
    {visits}
</div>
"""
            )
        pets_block = "".join(pet_cards)

    for pet in model.get("pets", []):
        visits = "".join(
            f"<tr><td>{h(_get(visit, 'date'))}</td><td>{h(_get(visit, 'description'))}</td></tr>"
            for visit in _get(pet, "visits", [])
        ) or '<tr><td colspan="2">No visits yet</td></tr>'
    block = f"""
<div class="page-header">
    <div class="container">
        <div class="d-flex align-items-center">
            <div class="detail-avatar me-4">
                <span>{_owner_initials(owner)}</span>
            </div>
            <div>
                <h1>{h(owner.firstName)} {h(owner.lastName)}</h1>
                <p class="mb-0"><i class="fas fa-map-marker-alt me-2"></i>{h(owner.city)}</p>
            </div>
        </div>
    </div>
</div>

<main class="container flex-grow-1 py-4">
    <a href="/owners/find" class="btn btn-secondary mb-4">
        <i class="fas fa-arrow-left me-2"></i>Back to Search
    </a>

    <div class="row g-4">
        <div class="col-lg-4">
            <div class="detail-card animate-fade-in-up">
                <div class="card-header">
                    <h5 class="mb-0"><i class="fas fa-user me-2"></i>Owner Information</h5>
                </div>
                <div class="detail-body">
                    <div class="info-row">
                        <div class="info-label"><i class="fas fa-user me-2"></i>Name</div>
                        <div class="info-value">{h(owner.firstName)} {h(owner.lastName)}</div>
                    </div>
                    <div class="info-row">
                        <div class="info-label"><i class="fas fa-home me-2"></i>Address</div>
                        <div class="info-value">{h(owner.address)}</div>
                    </div>
                    <div class="info-row">
                        <div class="info-label"><i class="fas fa-city me-2"></i>City</div>
                        <div class="info-value">{h(owner.city)}</div>
                    </div>
                    <div class="info-row">
                        <div class="info-label"><i class="fas fa-phone me-2"></i>Phone</div>
                        <div class="info-value">{h(owner.telephone)}</div>
                    </div>

                    <div class="d-flex gap-2 mt-4">
                        <a href="/owners/{owner.id}/edit" class="btn btn-primary flex-grow-1">
                            <i class="fas fa-edit me-2"></i>Edit
                        </a>
                        <a href="/owners/{owner.id}/pets/new" class="btn btn-success flex-grow-1">
                            <i class="fas fa-plus me-2"></i>Add Pet
                        </a>
                    </div>
                </div>
            </div>
        </div>
        <div class="col-lg-8">
            <div class="card animate-fade-in-up stagger-1">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <h5 class="mb-0"><i class="fas fa-paw me-2"></i>Pets & Visits</h5>
                    <span class="badge bg-white text-primary">{h(len(pets))} pets</span>
                </div>
                <div class="card-body">
                    {pets_block}
                </div>
            </div>
        </div>
    </div>
</main>
"""
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
            "type_error": f'<div class="alert alert-warning">{message}</div>',
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
        options.append(f'<option value="{pet_type.id}"{selected}>{h(pet_type.name)}</option>')
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
            "pet_information": f'<div class="alert alert-warning">{message}</div>',
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
        previous_visits = f"""
<div class="card mt-4 animate-fade-in-up stagger-1">
    <div class="card-header">
        <h5 class="mb-0"><i class="fas fa-history me-2"></i>Previous Visits</h5>
    </div>
    <div class="card-body">
        {_visit_timeline_list(visits)}
    </div>
</div>
"""
    pet_information = f"""
<div class="detail-card animate-fade-in-up">
    <div class="card-header">
        <h5 class="mb-0"><i class="fas fa-paw me-2"></i>Pet Information</h5>
    </div>
    <div class="detail-body">
        <div class="text-center mb-4">
            {_pet_icon(pet, "mx-auto mb-3", 'style="width: 80px; height: 80px; font-size: 2rem;"')}
            <h5>{h(_get(pet, "name"))}</h5>
        </div>
        <div class="info-row">
            <div class="info-label">Type</div>
            <div class="info-value">{h(_pet_type_name(pet))}</div>
        </div>
        <div class="info-row">
            <div class="info-label">Birth Date</div>
            <div class="info-value">{h(_get(pet, "birthDate", ""))}</div>
        </div>
        <div class="info-row">
            <div class="info-label">Owner</div>
            <div class="info-value">{h(getattr(owner, "firstName", ""))} {h(getattr(owner, "lastName", ""))}</div>
        </div>
    </div>
</div>
{previous_visits}
"""
    return {
        "form_action": h(action),
        "back_url": h(f"/owners/{getattr(owner, 'id', '')}"),
        "owner_name": f"{h(getattr(owner, 'firstName', ''))} {h(getattr(owner, 'lastName', ''))}",
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
            "vets_content": """
<div class="empty-state">
    <div class="empty-state-icon">
        <i class="fas fa-user-md"></i>
    </div>
    <h3>No Veterinarians Found</h3>
    <p>There are no veterinarians registered in the system yet.</p>
</div>
""",
        }
    cards = []
    for vet in vets:
        specialities = _get(vet, "specialitiesAsString")
        if specialities and specialities != "none":
            speciality_html = "".join(
                f'<span class="speciality-badge">{h(s.strip())}</span>'
                for s in str(specialities).split(",")
            )
        else:
            speciality_html = '<span class="speciality-badge">General Practice</span>'
        cards.append(
            f"""
<div class="col-md-6 col-lg-4">
    <div class="vet-card animate-fade-in-up">
        <div class="vet-card-header">
            <div class="vet-avatar">
                <i class="fas fa-user-md"></i>
            </div>
        </div>
        <div class="vet-card-body">
            <h5>{h(_get(vet, "firstName"))} {h(_get(vet, "lastName"))}</h5>
            <div class="mt-3">
                {speciality_html}
            </div>
            <div class="mt-4 pt-3 border-top">
                <div class="d-flex justify-content-center gap-3">
                    <span class="text-muted small">
                        <i class="fas fa-certificate text-warning me-1"></i>Licensed
                    </span>
                    <span class="text-muted small">
                        <i class="fas fa-star text-warning me-1"></i>Top Rated
                    </span>
                </div>
            </div>
        </div>
    </div>
</div>
"""
        )
    return {"vet_count": h(len(vets)), "vets_content": f'<div class="row g-4">{"".join(cards)}</div>'}


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
    return f'<div class="pet-icon {h(css_type)} {h(extra_class)}"{attrs}><i class="fas {icon}"></i></div>'


def _visit_timeline(visits) -> str:
    if not visits:
        return ""
    return f"""
<div class="mt-3 pt-3 border-top">
    <h6 class="text-muted mb-3"><i class="fas fa-calendar-alt me-2"></i>Visit History</h6>
    {_visit_timeline_list(visits)}
</div>
"""


def _visit_timeline_list(visits) -> str:
    items = []
    for visit in visits:
        items.append(
            f"""
<div class="visit-item">
    <div class="visit-date">{h(_get(visit, "date", ""))}</div>
    <div class="visit-description">{h(_get(visit, "description", ""))}</div>
</div>
"""
        )
    return f'<div class="visit-timeline">{"".join(items)}</div>'


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
