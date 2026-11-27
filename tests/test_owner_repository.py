"""Owner lookup, joins and search contracts from OwnerRepositoryTest."""

import pytest


@pytest.mark.parametrize('fragment', ['Davis', 'davis', 'DaV'])
def test_owner_repository_search_is_partial_and_case_insensitive(application_context, fragment):
    import java
    owners = application_context.java_ctx.getBean(java.type('petclinic.repositories.OwnerRepository'))
    matches = owners.findByLastNameContainingIgnoreCaseOrderByLastName(fragment)
    assert {(o.firstName, o.lastName) for o in matches} == {('Betty', 'Davis'), ('Harold', 'Davis')}
    assert all(len(o.pets) > 0 for o in matches)


def test_owner_repository_fetches_pets_and_handles_missing_ids(application_context):
    import java
    owners = application_context.java_ctx.getBean(java.type('petclinic.repositories.OwnerRepository'))
    owner = owners.findOneById(1)
    assert owner.firstName == 'George' and owner.lastName == 'Franklin'
    assert any(p.name == 'Leo' and p.type.name == 'cat' for p in owner.pets)
    assert owners.findOneById(2147483647) is None
    listed = owners.findAllOrderByLastName()
    assert len(listed) >= 10 and all(o.pets is not None for o in listed)
