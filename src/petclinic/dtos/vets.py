"""Vets request, form and response DTOs."""

from dataclasses import dataclass, field
from typing import Annotated

from jakarta.validation.constraints import NotBlank, Size
from micronaut.serde.annotation import Serdeable


@Serdeable
@dataclass
class VetForm:
    firstName: Annotated[str | None, NotBlank, Size(max=255)] = None
    lastName: Annotated[str | None, NotBlank, Size(max=255)] = None
    # The SDK coerces null elements of typed integer collections to zero.
    # Keep the input nullable here and enforce integer IDs in resolve().
    specialityIds: list[object] | None = field(default_factory=list)


@Serdeable
@dataclass
class SpecialityForm:
    id: int | None = None
    name: Annotated[str | None, NotBlank, Size(max=255)] = None
