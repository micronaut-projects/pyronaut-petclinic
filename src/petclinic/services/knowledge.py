"""Knowledge application services."""

import json
from typing import Annotated

from jakarta.inject import Inject, Singleton
from jakarta.transaction import Transactional
from micronaut.context.annotation import Factory, Requires
from micronaut.context.event import ApplicationEventListener, StartupEvent
from micronaut.data.model.vector.search import Score, ScoringFunction
from petclinic.constants import DEFAULT_DIALECT_PROPERTY, DIALECT_ORACLE
from petclinic.models.knowledge import PetCareDocument, PetCareChunk
from petclinic.repositories.knowledge import PetCareDocumentRepository, PetCareChunkRepository
from petclinic.resources import ApplicationResources
from petclinic.services.embeddings import StaticPetCareEmbeddingService


@Requires(property=DEFAULT_DIALECT_PROPERTY, value=DIALECT_ORACLE)
@Singleton
class PetCareKnowledgeService:
    resources: Annotated[ApplicationResources, Inject]
    chunks: Annotated[PetCareChunkRepository, Inject]
    documents: Annotated[PetCareDocumentRepository, Inject]
    embeddings: Annotated[StaticPetCareEmbeddingService, Inject]

    @Transactional
    def seed(self):
        if self.documents.count() > 0 or self.chunks.count() > 0:
            return
        for source in json.loads(self.resources.text('knowledge/pet-care-knowledge.json'))['documents']:
            document = self.documents.save(PetCareDocument(source['title'], source['source'], source['description']))
            for index, chunk in enumerate(source['chunks']):
                self.chunks.save(PetCareChunk(document.id, document.title, document.source,
                                              chunk['topic'], chunk['species'], index, chunk['content'],
                                              self.embeddings.embed(chunk['content'])))

    def search(self, query: str) -> list[dict]:
        vector = self.embeddings.find(query)
        if vector is None:
            return []
        matches = self.chunks.searchTop5ByEmbeddingNear(vector, Score(2.0), ScoringFunction.COSINE)
        results = []
        for result in matches.results():
            chunk = result.entity()
            similarity = result.similarity()
            results.append({'id': chunk.id, 'documentTitle': chunk.documentTitle,
                            'documentSource': chunk.documentSource, 'topic': chunk.topic, 'species': chunk.species,
                            'chunkIndex': chunk.chunkIndex, 'content': chunk.content,
                            'distance': result.score().value(),
                            'similarity': similarity.value() if similarity is not None else None})
        return results


@Factory
@Requires(property=DEFAULT_DIALECT_PROPERTY, value=DIALECT_ORACLE)
@Requires(property='petclinic.sample-data.enabled', value='true', defaultValue='true')
class PetCareKnowledgeLoader:
    knowledge: Annotated[PetCareKnowledgeService, Inject]

    @Singleton
    def startup_listener(self) -> ApplicationEventListener[StartupEvent]:
        def on_startup(event: StartupEvent):
            self.knowledge.seed()

        return on_startup
