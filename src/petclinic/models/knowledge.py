"""Knowledge domain and persistence models."""

from dataclasses import dataclass
from typing import Annotated

from micronaut.data.annotation import GeneratedValue, Id, MappedEntity, MappedProperty, VectorStorage
from micronaut.data.model.vector import FloatVector


@MappedEntity('PET_CARE_DOCUMENTS')
@dataclass
class PetCareDocument:
    title: Annotated[str, MappedProperty("TITLE")]
    source: Annotated[str, MappedProperty("SOURCE")]
    description: Annotated[str, MappedProperty("DESCRIPTION")]
    id: Annotated[int | None, Id, GeneratedValue] = None


@MappedEntity('PET_CARE_CHUNKS')
@dataclass
class PetCareChunk:
    documentId: Annotated[int, MappedProperty("DOCUMENT_ID")]
    documentTitle: Annotated[str, MappedProperty("DOCUMENT_TITLE")]
    documentSource: Annotated[str, MappedProperty("DOCUMENT_SOURCE")]
    topic: Annotated[str, MappedProperty("TOPIC")]
    species: Annotated[str, MappedProperty("SPECIES")]
    chunkIndex: Annotated[int, MappedProperty("CHUNK_INDEX")]
    content: Annotated[str, MappedProperty("CONTENT")]
    embedding: Annotated[FloatVector, VectorStorage(length=384), MappedProperty("EMBEDDING")]
    id: Annotated[int | None, Id, GeneratedValue] = None
