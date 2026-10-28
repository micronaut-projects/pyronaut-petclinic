"""Knowledge request, form and response DTOs."""

from dataclasses import dataclass

from micronaut.serde.annotation import Serdeable


@Serdeable
@dataclass
class PetCareSearchRequest:
    query: str
