"""Integration checks for knowledge."""

import pytest
from petclinic_test_support import DATABASE

pytestmark = pytest.mark.skipif(DATABASE != 'oracle', reason='Oracle-only reference feature')


def test_knowledge_repository_distance_threshold(application_context):
    import java
    from micronaut.data.model.vector.search import Score, ScoringFunction
    chunks = application_context.java_ctx.getBean(java.type('petclinic.repositories.PetCareChunkRepository'))
    embeddings = application_context.java_ctx.getBean(java.type('petclinic.services.StaticPetCareEmbeddingService'))
    # Any valid query vector must be excluded by a negative cosine distance.
    results = chunks.searchTop5ByEmbeddingNear(
        embeddings.embed('What vaccinations does my puppy need?'), Score(-1.0), ScoringFunction.COSINE)
    assert len(results.results()) == 0



def test_knowledge_search_uses_reference_vectors_and_ranked_database_query(client):
    page = client.get('/knowledge')
    assert page.status_code == 200, page.text
    assert 'knowledge-search-form' in page.text
    assert '384' in page.text
    for query, title, topic in (
        ('What vaccinations does my puppy need?', 'Dog preventive care', 'preventive care'),
        ("How should I clean my bird's cage?", 'Bird companion care', 'hygiene'),
    ):
        response = client.post('/knowledge/search', json={'query': query})
        assert response.status_code == 200, response.text
        results = response.json()
        assert len(results) == 5
        assert results[0]['documentTitle'] == title
        assert results[0]['topic'] == topic
        assert [row['distance'] for row in results] == sorted(row['distance'] for row in results)
        assert all(row['documentSource'] and row['content'] for row in results)
        rendered = client.get('/knowledge', params={'query': query})
        assert rendered.status_code == 200, rendered.text
        assert title in rendered.text
    assert client.post('/knowledge/search', json={'query': ' an uncataloged question '}).json() == []
    assert client.post('/knowledge/search', json={'query': '  '}).json() == []
    exact = client.post('/knowledge/search', json={'query': '  What vaccinations does my puppy need?  '})
    assert exact.status_code == 200
    assert exact.json()[0]['documentTitle'] == 'Dog preventive care'
