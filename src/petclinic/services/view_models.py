"""Presentation models for owner, pet and veterinarian views."""

from petclinic.models.patients import Owner, Pet
from petclinic.models.vets import Vet
from petclinic.services.durations import duration_minutes


def vet_view_models(vets: list[Vet]) -> list[dict]:
    """Adapt the cached service entities for the translated veterinarian view."""

    models = []
    for vet in vets:
        specialities = [{'id': s.id, 'name': s.name} for s in sorted(vet.specialities, key=lambda s: s.name)]
        models.append({'id': vet.id, 'firstName': vet.firstName, 'lastName': vet.lastName,
                       'specialities': specialities,
                       'specialitiesAsString': ', '.join(s['name'] for s in specialities) if specialities else 'none'})
    return models


def pet_view_model(pet: Pet) -> dict:
    pet_type = pet.type.name if pet.type is not None else ''
    return {
        'id': pet.id, 'name': pet.name, 'birthDate': str(pet.birthDate or ''),
        'type': {'name': pet_type} if pet.type is not None else None,
        'typeClass': pet_type.strip().lower() or 'dog',
        'icon': {'cat': 'fa-cat', 'bird': 'fa-dove', 'hamster': 'fa-hippo', 'snake': 'fa-worm'}.get(
            pet_type.strip().lower(), 'fa-dog'),
        'visits': [{'id': v.id, 'date': str(v.date or ''), 'description': v.description,
                    'durationInMinutes': duration_minutes(v.duration) if v.duration is not None else None,
                    'periodInMonths': v.period.toTotalMonths() if v.period is not None else None}
                   for v in sorted(pet.visits, key=lambda visit: str(visit.date))],
    }


def owner_view_model(owner: Owner) -> dict:
    return {'id': owner.id, 'firstName': owner.firstName, 'lastName': owner.lastName,
            'address': owner.address, 'city': owner.city, 'telephone': owner.telephone,
            'pets': [pet_view_model(pet) for pet in owner.pets]}


def owner_search_model(owner: Owner) -> dict:
    """Match the reference's non-recursive owner search JSON representation."""

    result = {'id': owner.id, 'firstName': owner.firstName, 'lastName': owner.lastName,
              'address': owner.address, 'city': owner.city, 'telephone': owner.telephone}
    pets = []
    for pet in owner.pets:
        pets.append({'id': pet.id, 'name': pet.name, 'birthDate': str(pet.birthDate),
                     'type': {'id': pet.type.id, 'name': pet.type.name},
                     'owner': dict(result)})
    if pets:
        result['pets'] = pets
    return result
