"""Clinics HTTP handling."""

from decimal import Decimal
from math import isfinite
from typing import Annotated

from jakarta.inject import Inject
from jakarta.validation import Validator
from micronaut.data.model.geo import LineString, Point, Polygon
from micronaut.http import HttpResponse, MediaType
from micronaut.http.annotation import Body, Get, Post
from micronaut.http.server.exceptions import NotFoundException
from micronaut.views import View
from petclinic.dtos.clinics import ClinicNearbyRequest, ClinicCoordinatesRequest, ClinicServiceOfferingForm, \
    ClinicServiceOfferingResponse
from petclinic.errors import entity_not_found
from petclinic.models.clinics import Clinic, ClinicServiceOffering
from petclinic.services.clinics import ClinicBranchService
from petclinic.validation import violation_field

branch_service: Annotated[ClinicBranchService, Inject]

validator: Annotated[Validator, Inject]


def _clinic_model(clinic: Clinic) -> dict:
    return {"id": clinic.id, "name": clinic.name, "address": clinic.address, "city": clinic.city,
            "acceptingNewPatients": clinic.acceptingNewPatients, "emergencyService": clinic.emergencyService,
            "latitude": clinic.location.y(), "longitude": clinic.location.x()}


def _offering_model(offering: ClinicServiceOffering) -> dict:
    return {"id": offering.id, "serviceCode": offering.serviceCode, "name": offering.name,
            "description": offering.description or "", "price": format(Decimal(str(offering.price)), ".2f"),
            "durationMinutes": offering.durationMinutes}


def _coordinate(longitude: float, latitude: float) -> Point:
    if not isfinite(longitude) or not isfinite(latitude) or not -180 <= longitude <= 180 or not -90 <= latitude <= 90:
        raise ValueError("Coordinates must have longitude between -180 and 180 and latitude between -90 and 90.")
    return Point(longitude, latitude)


def _coordinates(request: ClinicCoordinatesRequest, minimum: int) -> list[Point]:
    if request.coordinates is None or len(request.coordinates) < minimum or any(c is None for c in request.coordinates):
        raise ValueError(f"This search requires at least {minimum} coordinates.")
    return [_coordinate(c.longitude, c.latitude) for c in request.coordinates]


def _cross(a, b, c):
    return (b.x() - a.x()) * (c.y() - a.y()) - (b.y() - a.y()) * (c.x() - a.x())


def _on_segment(a, b, p):
    return min(a.x(), b.x()) - 1e-10 <= p.x() <= max(a.x(), b.x()) + 1e-10 and min(a.y(),
                                                                                   b.y()) - 1e-10 <= p.y() <= max(a.y(),
                                                                                                                  b.y()) + 1e-10


def _intersects(a, b, c, d):
    x1, x2, x3, x4 = _cross(a, b, c), _cross(a, b, d), _cross(c, d, a), _cross(c, d, b)
    if ((x1 > 1e-10 and x2 < -1e-10) or (x1 < -1e-10 and x2 > 1e-10)) and (
            (x3 > 1e-10 and x4 < -1e-10) or (x3 < -1e-10 and x4 > 1e-10)):
        return True
    return any(abs(cross) <= 1e-10 and _on_segment(start, end, point) for cross, start, end, point in (
        (x1, a, b, c), (x2, a, b, d), (x3, c, d, a), (x4, c, d, b)))


def _polygon(points: list[Point]) -> Polygon:
    shell = list(points)
    if shell[0].x() != shell[-1].x() or shell[0].y() != shell[-1].y():
        shell.append(shell[0])
    edges = len(shell) - 1
    if edges < 3 or any(shell[i].x() == shell[i + 1].x() and shell[i].y() == shell[i + 1].y() for i in range(edges)):
        raise ValueError("A polygon requires three distinct vertices and no zero-length edges.")
    for i in range(edges):
        for j in range(i + 1, edges):
            if j == i + 1 or (i == 0 and j == edges - 1):
                continue
            if _intersects(shell[i], shell[i + 1], shell[j], shell[j + 1]):
                raise ValueError("A polygon boundary cannot cross itself.")
    area = sum(shell[i].x() * shell[i + 1].y() - shell[i + 1].x() * shell[i].y() for i in range(edges))
    if abs(area) <= 1e-10:
        raise ValueError("A polygon must enclose a nonzero area.")
    if area < 0:
        shell.reverse()
    return Polygon([LineString(shell)])


@Get("/clinics")
@View("clinics/findClinics")
def find_clinics() -> dict:
    return {}


@Post(value="/clinics/nearby", consumes=MediaType.APPLICATION_JSON)
def nearby(request: Annotated[ClinicNearbyRequest, Body]):
    try:
        point = _coordinate(request.longitude, request.latitude)
        if not isfinite(request.radiusMeters) or request.radiusMeters <= 0:
            raise ValueError("Radius must be a positive finite number of meters.")
    except ValueError as error:
        return HttpResponse.badRequest({"message": str(error)})
    matches = branch_service.clinics.findByLocationNear(point, request.radiusMeters)
    return [_clinic_model(c) for c in
            branch_service.filter_availability(matches, request.acceptingNewPatients, request.emergencyService)]


@Post(value="/clinics/within", consumes=MediaType.APPLICATION_JSON)
def within(request: Annotated[ClinicCoordinatesRequest, Body]):
    try:
        polygon = _polygon(_coordinates(request, 3))
    except ValueError as error:
        return HttpResponse.badRequest({"message": str(error)})
    matches = branch_service.clinics.findByLocationGeoWithin(polygon)
    return [_clinic_model(c) for c in
            branch_service.filter_availability(matches, request.acceptingNewPatients, request.emergencyService)]


@Post(value="/clinics/intersects", consumes=MediaType.APPLICATION_JSON)
def intersects(request: Annotated[ClinicCoordinatesRequest, Body]):
    try:
        line = LineString(_coordinates(request, 2))
    except ValueError as error:
        return HttpResponse.badRequest({"message": str(error)})
    matches = branch_service.clinics.findByServiceAreaGeoIntersects(line)
    return [_clinic_model(c) for c in
            branch_service.filter_availability(matches, request.acceptingNewPatients, request.emergencyService)]


@Get("/clinics/{clinicId}/services")
@View("clinics/servicesList")
def clinic_services(clinicId: int):
    clinic = branch_service.clinics.findOneById(clinicId)
    if clinic is None:
        raise NotFoundException()
    return {"clinic": _clinic_model(clinic), "services": [_offering_model(o) for o in
                                                          branch_service.offerings.findByClinicIdOrderByServiceCode(
                                                              clinicId)]}


@Get("/clinics/{clinicId}/services/new")
@View("clinics/createOrUpdateServiceForm")
def new_service(clinicId: int):
    clinic = branch_service.clinics.findOneById(clinicId)
    if clinic is None:
        raise NotFoundException()
    return {"clinic": _clinic_model(clinic), "service": {"price": "0.00", "durationMinutes": 30}, "isNew": True,
            "validationErrors": {}}


@Get("/clinics/{clinicId}/services/{serviceCode}/edit")
@View("clinics/createOrUpdateServiceForm")
def edit_service(clinicId: int, serviceCode: str):
    offering = branch_service.offerings.findByClinicIdAndServiceCode(clinicId, serviceCode)
    if offering is None:
        raise NotFoundException()
    return {"clinic": _clinic_model(offering.clinic), "service": _offering_model(offering), "isNew": False,
            "validationErrors": {}}


@Post(value="/clinics/{clinicId}/services", consumes=MediaType.APPLICATION_JSON)
def save_service(clinicId: int, form: Annotated[ClinicServiceOfferingForm, Body]):
    clinic = branch_service.clinics.findOneById(clinicId)
    if clinic is None:
        return entity_not_found()
    errors = {violation_field(v): str(v.getMessage()) for v in validator.validate(form)}
    if errors:
        return HttpResponse.badRequest({"message": "Validation failed", "errors": errors})
    offering = branch_service.upsert_offering(clinic, form)
    return ClinicServiceOfferingResponse(id=offering.id, clinicId=clinicId, serviceCode=offering.serviceCode,
                                         name=offering.name, description=offering.description, price=offering.price,
                                         durationMinutes=offering.durationMinutes)
