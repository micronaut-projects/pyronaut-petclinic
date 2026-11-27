"""Embeddings application services."""

import base64
import struct
from functools import lru_cache
from typing import Annotated

from jakarta.inject import Inject, Singleton
from micronaut.context.annotation import Requires
from micronaut.data.model.vector import FloatVector
from petclinic.constants import DEFAULT_DIALECT_PROPERTY, DIALECT_ORACLE
from petclinic.resources import ApplicationResources


@lru_cache(maxsize=1)
def vector_catalog(data: str) -> dict[str, tuple[float, ...]]:
    vectors = {}
    for number, line in enumerate(data.splitlines(), 1):
        if not line.strip() or line.startswith('#'):
            continue
        fields = line.split('\t')
        if len(fields) != 3 or fields[0] not in ('C', 'Q'):
            raise ValueError(f'Invalid vector resource line {number}')
        text = base64.b64decode(fields[1], validate=True).decode('utf-8')
        data = base64.b64decode(fields[2], validate=True)
        if len(data) != 384 * 4:
            raise ValueError(f'Vector resource line {number} must contain 384 floats')
        vectors[text] = struct.unpack('>384f', data)
    if not vectors:
        raise ValueError('No precomputed pet-care vectors found')
    return vectors


@Requires(property=DEFAULT_DIALECT_PROPERTY, value=DIALECT_ORACLE)
@Singleton
class StaticPetCareEmbeddingService:
    resources: Annotated[ApplicationResources, Inject]

    def find(self, text: str) -> FloatVector | None:
        values = vector_catalog(self.resources.text('knowledge/pet-care-embeddings.tsv')).get(
            text.strip()) if text and text.strip() else None
        return FloatVector(list(values)) if values is not None else None

    def embed(self, text: str) -> FloatVector:
        if not text or not text.strip():
            return FloatVector([0.0] * 384)
        vector = self.find(text)
        if vector is None:
            raise ValueError('No precomputed pet-care vector for query: ' + text)
        return vector
