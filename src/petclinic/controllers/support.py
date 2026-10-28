"""Support HTTP routes and helpers."""

from datetime import date

from java.net import URI
from java.time import Duration, LocalDate, Period
from micronaut.http import HttpResponse
from petclinic.dtos.patients import PetForm, VisitForm
from petclinic.validation import violation_field


def redirect_to(location: str):
    """Build a redirect response using Java's ``URI`` type."""

    return HttpResponse.redirect(URI.create(location))


def validation_errors(form, validator) -> dict[str, str]:
    """Convert Jakarta ``ConstraintViolation`` objects into template data."""

    errors = {}
    for violation in validator.validate(form):
        field = violation_field(violation)
        if field:
            errors[field] = str(violation.getMessage())
    for field, label in (("birthDate", "Birth date"), ("date", "Visit date")):
        value = getattr(form, field, None)
        if value:
            try:
                date.fromisoformat(value)
            except ValueError:
                errors[field] = f"{label} must be a valid date"
    return errors


def pet_type_for(form: PetForm, errors: dict[str, str], clinic_service):
    try:
        return clinic_service.find_pet_type_by_id(int(form.typeId)) if form.typeId else None
    except ValueError:
        errors["typeId"] = "Invalid pet type"
        return None


def parse_form_date(value: str | None) -> LocalDate:
    assert value is not None
    return LocalDate.parse(date.fromisoformat(value).isoformat())


def visit_errors(form: VisitForm, validator) -> dict[str, str]:
    errors = validation_errors(form, validator)
    for field, label in (("durationMinutes", "Duration"), ("followUpPeriodMonths", "Follow-up period")):
        if field not in errors:
            value = int(getattr(form, field))
            if value < 1 or value > 2147483647:
                errors[field] = f"{label} must be between 1 and 2147483647"
    return errors


def persist_visit(form: VisitForm, pet, clinic_service, form_mapper):
    form.dateValue = parse_form_date(form.date)
    form.durationValue = Duration.ofMinutes(int(form.durationMinutes))
    form.periodValue = Period.ofMonths(int(form.followUpPeriodMonths)).normalized()
    clinic_service.save_visit(form_mapper.to_visit(form, pet))
