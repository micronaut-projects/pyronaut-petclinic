"""Vets domain and persistence models."""

from dataclasses import dataclass, field
from typing import Annotated

from jakarta.validation.constraints import NotBlank
from micronaut.core.annotation import Creator, Introspected
from micronaut.data.annotation import GeneratedValue, Id, MappedEntity, MappedProperty, Transient
from micronaut.data.annotation.sql import ETaggable, GeneratedETag
from micronaut.serde.annotation import Serdeable
from petclinic.etags import EMPTY_SPECIALITIES_HASH


@Serdeable
@MappedEntity("SPECIALTIES")
@dataclass
class Speciality:
    """Lookup table entity for veterinarian specialities."""

    name: Annotated[str, NotBlank, MappedProperty("NAME")]
    id: Annotated[int | None, Id, GeneratedValue] = None


@Serdeable
@MappedEntity("VETS")
@ETaggable
@dataclass
class Vet:
    """ETag inputs follow the reference's positional SQL function signature."""

    id: Annotated[int | None, Id, GeneratedValue] = None
    firstName: Annotated[str | None, NotBlank, MappedProperty("FIRST_NAME")] = None
    lastName: Annotated[str | None, NotBlank, MappedProperty("LAST_NAME")] = None
    specialitiesHash: Annotated[str, MappedProperty("SPECIALITIES_ETAG_HASH")] = EMPTY_SPECIALITIES_HASH
    etag: Annotated[str | None, GeneratedETag(function="SYS_ROW_ETAG")] = None
    specialities: Annotated[list[Speciality], Transient] = field(default_factory=list)

    @staticmethod
    @Creator
    def from_columns(id: int | None, firstName: str, lastName: str,
                     specialitiesHash: str, etag: str | None) -> "Vet":
        return Vet(id=id, firstName=firstName, lastName=lastName,
                   specialitiesHash=specialitiesHash, etag=etag)


@Serdeable
@Introspected
@dataclass
class VetWithSpecialities:
    """Projection row returned by the vet list aggregate query."""

    id: int
    firstName: str
    lastName: str
    specialityRows: str | None


@MappedEntity("VET_SPECIALTIES")
@dataclass
class VetSpeciality:
    """The reference's pure join row, represented by its two foreign keys."""

    vetId: Annotated[int, MappedProperty("VET_ID")]
    specialityId: Annotated[int, MappedProperty("SPECIALTY_ID")]
