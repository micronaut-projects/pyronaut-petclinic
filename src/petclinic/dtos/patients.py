"""Patients request, form and response DTOs."""

from dataclasses import dataclass
from typing import Annotated

from jakarta.validation.constraints import Min, NotBlank, Pattern, Size
from java.time import Duration, LocalDate, Period
from micronaut.serde.annotation import Serdeable


@Serdeable
@dataclass
class OwnerForm:
    """Create/update form for ``Owner``."""

    id: int | None = None
    firstName: Annotated[str | None, NotBlank(message="First name is required"), Size(min=1, max=30,
                                                                                      message="First name must be between 1 and 30 characters")] = None
    lastName: Annotated[str | None, NotBlank(message="Last name is required"), Size(min=1, max=30,
                                                                                    message="Last name must be between 1 and 30 characters")] = None
    address: Annotated[str | None, NotBlank(message="Address is required"), Size(min=1, max=255,
                                                                                 message="Address must be between 1 and 255 characters")] = None
    city: Annotated[str | None, NotBlank(message="City is required"), Size(min=1, max=80,
                                                                           message="City must be between 1 and 80 characters")] = None
    telephone: Annotated[str | None, NotBlank(message="Telephone is required"), Pattern(regexp=r"\d{10}",
                                                                                        message="Telephone must be a 10-digit number")] = None


@Serdeable
@dataclass
class PetForm:
    """Create/update form for ``Pet``.

    The form carries ``typeId`` instead of a nested ``PetType`` object because
    HTML ``select`` elements submit scalar values.
    """

    id: int | None = None
    name: Annotated[str | None, NotBlank(message="Pet name is required"), Size(min=1, max=30,
                                                                               message="Pet name must be between 1 and 30 characters")] = None
    # HTML sends empty controls as strings. Keeping these as strings lets
    # validation render the form again instead of failing body conversion.
    birthDate: Annotated[str | None, NotBlank(message="Birth date is required")] = None
    typeId: Annotated[str | None, NotBlank(message="Pet type is required")] = None
    birthDateValue: LocalDate | None = None


@Serdeable
@dataclass
class VisitForm:
    """Create form for ``Visit``."""

    id: int | None = None
    date: Annotated[str | None, NotBlank(message="Visit date is required")] = None
    description: Annotated[str | None, NotBlank(message="Description is required"), Size(min=1, max=255,
                                                                                         message="Description must be between 1 and 255 characters")] = None
    dateValue: LocalDate | None = None
    durationMinutes: Annotated[str | None, NotBlank(message="Duration is required"), Pattern(regexp="[0-9]+",
                                                                                             message="Duration must be a whole number of minutes")] = "30"
    followUpPeriodMonths: Annotated[
        str | None, NotBlank(message="Follow-up period is required"), Pattern(regexp="[0-9]+",
                                                                              message="Follow-up period must be a whole number of months")] = "6"
    durationValue: Duration | None = None
    periodValue: Period | None = None


@Serdeable
@dataclass
class VisitRequest:
    """JSON counterpart of the HTML visit form, using numeric interval values."""

    date: Annotated[str, NotBlank(message="Visit date is required")]
    description: Annotated[str, NotBlank(message="Description is required"), Size(max=255)]
    durationMinutes: Annotated[int, Min(value=1, message="Duration must be at least 1 minute")] = 30
    followUpPeriodMonths: Annotated[int, Min(value=1, message="Follow-up period must be at least 1 month")] = 6
