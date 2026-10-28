"""Care_records domain and persistence models."""

from dataclasses import dataclass, field
from typing import Annotated

from com.fasterxml.jackson.annotation import JsonFormat, JsonProperty
from jakarta.validation import Valid
from jakarta.validation.constraints import NotBlank, NotNull, Pattern
from java.time import LocalDate
from micronaut.data.annotation import Id, JsonSubView, JsonView, MappedProperty, Relation
from micronaut.data.annotation.sql import JoinColumn
from micronaut.serde.annotation import Serdeable
from petclinic.models.patients import Owner, Pet, Visit


@Serdeable
@dataclass
class DualityMetadata:
    etag: Annotated[str | None, NotBlank(message='The document must include its _metadata.etag value.')]
    asof: str | None = None


@JsonSubView(entity=Visit, operations=[JsonView.Operation.UPDATE])
@dataclass
class VisitCareSubView:
    id: Annotated[int, Id, MappedProperty('ID')]
    date: Annotated[
        LocalDate | None, MappedProperty('VISIT_DATE'), NotNull, JsonFormat(pattern="yyyy-MM-dd['T'HH:mm:ss]")]
    description: Annotated[str | None, MappedProperty('DESCRIPTION'), NotBlank]


@JsonSubView(entity=Pet, operations=[JsonView.Operation.UPDATE])
@dataclass
class PetCareSubView:
    id: Annotated[int, Id, MappedProperty('ID')]
    name: Annotated[str | None, MappedProperty('NAME'), NotBlank]
    birthDate: Annotated[
        LocalDate | None, MappedProperty('BIRTH_DATE'), NotNull, JsonFormat(pattern="yyyy-MM-dd['T'HH:mm:ss]")]
    visits: Annotated[list[VisitCareSubView] | None, MappedProperty('visits'), JoinColumn(name='ID',
                                                                                          referencedColumnName='PET_ID'), Relation(
        Relation.Kind.ONE_TO_MANY)] = field(default_factory=list)

    def __post_init__(self):
        if self.visits is None:
            self.visits = []


@JsonView(value='OWNER_CARE_DV', entity=Owner, operations=[JsonView.Operation.UPDATE])
@dataclass
class OwnerCareView:
    id: Annotated[int, Id, MappedProperty('ID'), JsonProperty('_id')]
    firstName: Annotated[str | None, MappedProperty('FIRST_NAME'), NotBlank]
    lastName: Annotated[str | None, MappedProperty('LAST_NAME'), NotBlank]
    address: Annotated[str | None, MappedProperty('ADDRESS'), NotBlank]
    city: Annotated[str | None, MappedProperty('CITY'), NotBlank]
    telephone: Annotated[str | None, MappedProperty('TELEPHONE'), Pattern(regexp='[0-9]{1,10}',
                                                                          message='The telephone number must contain up to 10 digits.')]
    pets: Annotated[list[PetCareSubView] | None, MappedProperty('pets'), JoinColumn(name='ID',
                                                                                    referencedColumnName='OWNER_ID'), Relation(
        Relation.Kind.ONE_TO_MANY)] = field(default_factory=list)
    metadata: Annotated[DualityMetadata | None, JsonProperty('_metadata'), NotNull(
        message='The document must include its _metadata.etag value.'), Valid] = None

    def __post_init__(self):
        if self.pets is None:
            self.pets = []
