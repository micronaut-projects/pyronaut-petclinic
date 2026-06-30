"""Micronaut Data entities used by the PetClinic sample.

The classes in this module are regular Python dataclasses with Micronaut
annotations attached through ``typing.Annotated``. Pyronaut reads these
annotations at build time and generates the Micronaut bean metadata needed for
Micronaut Data JDBC and Micronaut Serialization.

Key concepts demonstrated here:

* ``@MappedEntity`` maps a Python class to a database table.
* ``@Id`` and ``@GeneratedValue`` identify generated primary keys.
* ``@MappedProperty`` pins Python attribute names to explicit column names.
* ``@Relation`` models foreign-key relationships between entities.
* ``@Serdeable`` lets entities be serialized for JSON responses.
"""

from dataclasses import dataclass
from typing import Annotated

from java.time import LocalDate
from micronaut.data.annotation import GeneratedValue, Id, MappedEntity, MappedProperty, Relation
from micronaut.serde.annotation import Serdeable


@Serdeable
@MappedEntity("PET_TYPES")
@dataclass
class PetType:
    """Lookup table entity for values such as cat, dog, and lizard."""

    name: Annotated[str, MappedProperty("NAME")]
    id: Annotated[int | None, Id, GeneratedValue] = None


@Serdeable
@MappedEntity("SPECIALTIES")
@dataclass
class Specialty:
    """Lookup table entity for veterinarian specialties."""

    name: Annotated[str, MappedProperty("NAME")]
    id: Annotated[int | None, Id, GeneratedValue] = None


@Serdeable
@MappedEntity("OWNERS")
@dataclass
class Owner:
    """A PetClinic owner.

    All business fields are required. Only the generated database ID defaults
    to ``None`` so new instances clearly represent unsaved rows.
    """

    firstName: Annotated[str, MappedProperty("FIRST_NAME")]
    lastName: Annotated[str, MappedProperty("LAST_NAME")]
    address: Annotated[str, MappedProperty("ADDRESS")]
    city: Annotated[str, MappedProperty("CITY")]
    telephone: Annotated[str, MappedProperty("TELEPHONE")]
    id: Annotated[int | None, Id, GeneratedValue] = None

    def is_new(self) -> bool:
        return self.id is None


@Serdeable
@MappedEntity("PETS")
@dataclass
class Pet:
    """A pet belongs to one owner and has one pet type.

    ``Relation.Kind.MANY_TO_ONE`` tells Micronaut Data that ``type`` and
    ``owner`` are stored as foreign keys. Repository methods use ``@Join`` to
    fetch these non-null relationships when the UI needs them.
    """

    name: Annotated[str, MappedProperty("NAME")]
    birthDate: Annotated[LocalDate, MappedProperty("BIRTH_DATE")]
    type: Annotated[PetType, Relation(Relation.Kind.MANY_TO_ONE), MappedProperty("TYPE_ID")]
    owner: Annotated[Owner, Relation(Relation.Kind.MANY_TO_ONE), MappedProperty("OWNER_ID")]
    id: Annotated[int | None, Id, GeneratedValue] = None

    def is_new(self) -> bool:
        return self.id is None

    def getTypeId(self) -> int | None:
        return self.type.id if self.type is not None else None

    def getOwnerId(self) -> int | None:
        return self.owner.id if self.owner is not None else None


@Serdeable
@MappedEntity("VISITS")
@dataclass
class Visit:
    """A veterinary visit for a pet."""

    date: Annotated[LocalDate, MappedProperty("VISIT_DATE")]
    description: Annotated[str, MappedProperty("DESCRIPTION")]
    pet: Annotated[Pet, Relation(Relation.Kind.MANY_TO_ONE), MappedProperty("PET_ID")]
    id: Annotated[int | None, Id, GeneratedValue] = None

    def is_new(self) -> bool:
        return self.id is None


@Serdeable
@MappedEntity("VETS")
@dataclass
class Vet:
    """A veterinarian. Specialties are joined through ``VetSpecialty``."""

    firstName: Annotated[str, MappedProperty("FIRST_NAME")]
    lastName: Annotated[str, MappedProperty("LAST_NAME")]
    id: Annotated[int | None, Id, GeneratedValue] = None


@Serdeable
@MappedEntity("VET_SPECIALTIES")
@dataclass
class VetSpecialty:
    """Join-table row linking a veterinarian to a specialty."""

    vetId: Annotated[int, MappedProperty("VET_ID")]
    specialtyId: Annotated[int, MappedProperty("SPECIALTY_ID")]
    id: Annotated[int | None, Id, GeneratedValue] = None
