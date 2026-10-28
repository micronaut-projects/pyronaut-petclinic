"""Embedding and resource contracts from the Java unit suites."""

import json
import math

import pytest


@pytest.fixture
def resources(application_context):
    from petclinic.resources import ApplicationResources
    resources = ApplicationResources()
    resources.environment = application_context.java_ctx.getEnvironment()
    return resources


@pytest.fixture
def embedding_service(resources):
    from petclinic.services.embeddings import StaticPetCareEmbeddingService
    service = StaticPetCareEmbeddingService()
    service.resources = resources
    return service


def cosine(left, right):
    left, right = list(left), list(right)
    return sum(a * b for a, b in zip(left, right)) / math.sqrt(
        sum(v * v for v in left) * sum(v * v for v in right))


def test_embedding_has_reference_dimensions(embedding_service):
    assert len(embedding_service.embed('What vaccinations does my puppy need?').data()) == 384


def test_embedding_blank_text_is_zero(embedding_service):
    vector = list(embedding_service.embed('   ').data())
    assert len(vector) == 384 and all(v == 0 for v in vector)


def test_embedding_unknown_text_has_no_vector(embedding_service):
    assert embedding_service.find('an uncataloged question') is None


def test_embedding_related_questions_are_similar(embedding_service):
    a = embedding_service.embed('What vaccinations does my puppy need?')
    b = embedding_service.embed('When should a young dog receive its shots?')
    assert cosine(a.data(), b.data()) > 0.50


def test_embedding_different_topics_are_less_similar(embedding_service):
    a = embedding_service.embed("How should I clean my bird's cage?")
    b = embedding_service.embed('What temperature and humidity does a reptile habitat need?')
    assert cosine(a.data(), b.data()) < 0.80


def test_embedding_resource_documents_and_chunks_are_complete(resources, embedding_service):
    documents = json.loads(resources.text('knowledge/pet-care-knowledge.json'))['documents']
    assert len(documents) >= 10
    count = 0
    for document in documents:
        assert document['title'].strip() and document['source'].strip()
        assert len(document['chunks']) >= 2
        for chunk in document['chunks']:
            assert all(chunk[key].strip() for key in ('topic', 'species', 'content'))
            assert len(embedding_service.embed(chunk['content']).data()) == 384
            count += 1
    assert count >= 20
