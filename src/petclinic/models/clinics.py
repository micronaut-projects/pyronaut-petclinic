"""Clinics domain and persistence models."""

from dataclasses import dataclass, field
from typing import Annotated

from java.math import BigDecimal
from micronaut.data.annotation import GeneratedValue, Id, Index, MappedEntity, MappedProperty, Relation, Srid
from micronaut.data.model.geo import Point, Polygon


@MappedEntity("CLINICS")
@dataclass
class Clinic:
    name: Annotated[str, MappedProperty("NAME")]
    address: Annotated[str, MappedProperty("ADDRESS")]
    city: Annotated[str, MappedProperty("CITY")]
    acceptingNewPatients: Annotated[bool, MappedProperty("ACCEPTING_NEW_PATIENTS")]
    emergencyService: Annotated[bool, MappedProperty("EMERGENCY_SERVICE")]
    location: Annotated[Point, Srid(value=4326, type=Srid.CrsType.GEOGRAPHIC), MappedProperty("LOCATION")]
    serviceArea: Annotated[Polygon, Srid(value=4326, type=Srid.CrsType.GEOGRAPHIC), MappedProperty("SERVICE_AREA")]
    id: Annotated[int | None, Id, GeneratedValue] = None
    serviceOfferings: Annotated[
        list["ClinicServiceOffering"], Relation(value=Relation.Kind.ONE_TO_MANY, mappedBy="clinic")] = field(
        default_factory=list)


@Index(name="UK_CLINIC_SERVICE_CODE", columns=["CLINIC_ID", "SERVICE_CODE"], unique=True)
@MappedEntity("CLINIC_SERVICE_OFFERINGS")
@dataclass
class ClinicServiceOffering:
    clinic: Annotated[Clinic, Relation(Relation.Kind.MANY_TO_ONE), MappedProperty("CLINIC_ID")]
    serviceCode: Annotated[str, MappedProperty("SERVICE_CODE")]
    name: Annotated[str, MappedProperty("NAME")]
    description: Annotated[str | None, MappedProperty("DESCRIPTION")]
    price: Annotated[BigDecimal, MappedProperty("PRICE")]
    durationMinutes: Annotated[int, MappedProperty("DURATION_MINUTES")]
    id: Annotated[int | None, Id, GeneratedValue] = None
