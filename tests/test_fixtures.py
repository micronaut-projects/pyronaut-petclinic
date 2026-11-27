"""Canonical stock records shared by the Java and Python showcases."""

import pytest


@pytest.mark.parametrize('id,name,birth_date', [(4, 'Rosy', '2011-04-17'),
    (10, 'Mulligan', '2007-02-24'), (11, 'Freddy', '2010-03-09'),
    (12, 'Lucky', '2010-06-24'), (13, 'Sly', '2012-06-08')])
def test_canonical_pet_birth_dates(application_context, id, name, birth_date):
    import java
    pets = application_context.java_ctx.getBean(java.type('petclinic.repositories.PetRepository'))
    pet = pets.findOneById(id)
    assert pet.name == name and str(pet.birthDate) == birth_date
