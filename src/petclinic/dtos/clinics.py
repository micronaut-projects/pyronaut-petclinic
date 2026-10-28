"""Clinics request, form and response DTOs."""

from dataclasses import dataclass
from typing import Annotated

from jakarta.validation.constraints import DecimalMin, Digits, Min, NotBlank, NotNull, Size
from java.math import BigDecimal
from micronaut.serde.annotation import Serdeable


@Serdeable
@dataclass
class Coordinate:
    latitude: float
    longitude: float


@Serdeable
@dataclass
class ClinicNearbyRequest:
    latitude: float
    longitude: float
    radiusMeters: float
    acceptingNewPatients: bool | None = None
    emergencyService: bool | None = None


@Serdeable
@dataclass
class ClinicCoordinatesRequest:
    coordinates: list[Coordinate]
    acceptingNewPatients: bool | None = None
    emergencyService: bool | None = None


@Serdeable
@dataclass
class ClinicServiceOfferingForm:
    serviceCode: Annotated[str | None, NotBlank(message="Service code is required"), Size(max=40,
                                                                                          message="Service code must be at most 40 characters")] = None
    name: Annotated[str | None, NotBlank(message="Service name is required"), Size(max=100,
                                                                                   message="Service name must be at most 100 characters")] = None
    description: Annotated[str | None, Size(max=500, message="Description must be at most 500 characters")] = None
    price: Annotated[BigDecimal | None, NotNull(message="Price is required"), DecimalMin(value="0.00",
                                                                                         message="Price cannot be negative"), Digits(
        integer=8, fraction=2, message="Price must have at most two decimal places")] = None
    durationMinutes: Annotated[int | None, NotNull(message="Duration is required"), Min(value=1,
                                                                                        message="Duration must be at least 1 minute")] = 30


@Serdeable
@dataclass
class ClinicServiceOfferingResponse:
    id: int
    clinicId: int
    serviceCode: str
    name: str
    description: str | None
    price: BigDecimal
    durationMinutes: int
