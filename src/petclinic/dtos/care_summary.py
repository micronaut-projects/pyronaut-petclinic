"""Generated from config/jsonschema/owner-care-summary.schema.json.

Regenerate with: python3 scripts/generate_care_summary.py
"""

from dataclasses import dataclass
from typing import Annotated
from com.fasterxml.jackson.annotation import JsonInclude, JsonProperty
from java.time import LocalDate
from micronaut.serde.annotation import Serdeable


@Serdeable
@JsonInclude(JsonInclude.Include.NON_NULL)
@dataclass
class OwnerCareSummaryPetVisit:
    date: LocalDate
    description: str
    id: int


@Serdeable
@JsonInclude(JsonInclude.Include.NON_NULL)
@dataclass
class OwnerCareSummaryPet:
    birthDate: LocalDate
    id: int
    name: str
    visits: list[OwnerCareSummaryPetVisit]


@Serdeable
@JsonInclude(JsonInclude.Include.NON_NULL)
@dataclass
class OwnerCareSummary:
    id: Annotated[int, JsonProperty('_id')]
    address: str
    city: str
    firstName: str
    lastName: str
    pets: list[OwnerCareSummaryPet]
    telephone: str | None = None
