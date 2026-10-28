"""Knowledge HTTP handling."""

from typing import Annotated

from jakarta.inject import Inject
from micronaut.context.annotation import Requires
from micronaut.http import MediaType
from micronaut.http.annotation import Body, Controller, Get, Post, Produces, QueryValue
from micronaut.views import View
from petclinic.constants import DEFAULT_DIALECT_PROPERTY, DIALECT_ORACLE
from petclinic.dtos.knowledge import PetCareSearchRequest
from petclinic.services.knowledge import PetCareKnowledgeService


@Controller('/knowledge')
@Requires(property=DEFAULT_DIALECT_PROPERTY, value=DIALECT_ORACLE)
class PetCareKnowledgeController:
    knowledge: Annotated[PetCareKnowledgeService, Inject]

    @Get
    @View('knowledge/search')
    def knowledge_page(self, query: Annotated[str, QueryValue(defaultValue='')] = '') -> dict:
        return {'query': query, 'results': self.knowledge.search(query), 'dimensions': 384}

    @Post(value='/search', consumes=MediaType.APPLICATION_JSON)
    @Produces(MediaType.APPLICATION_JSON)
    def search_knowledge(self, request: Annotated[PetCareSearchRequest, Body]):
        return self.knowledge.search(request.query)
