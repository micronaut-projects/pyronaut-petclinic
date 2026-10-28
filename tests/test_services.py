"""Integration checks for services."""

import re


def test_reference_service_lookup_operations(client, application_context):
    import java

    service = application_context.java_ctx.getBean(java.type('petclinic.services.ClinicService'))
    assert len(service.find_all_pets()) >= 13
    visit = service.find_visits_by_pet_id(1)[0]
    assert service.find_visit_by_id(visit.id).id == visit.id
    assert service.find_vet_by_id(1).lastName == 'Carter'
    assert service.find_speciality_by_id(1).id == 1
    assert service.find_visit_by_id(999999) is None
    assert service.find_vet_by_id(999999) is None
    assert service.find_speciality_by_id(999999) is None
    vets = service.find_all_vets()
    douglas = next(vet for vet in vets if vet.lastName == 'Douglas')
    assert sorted(s.name for s in douglas.specialities) == ['dentistry', 'surgery']
    joins = application_context.java_ctx.getBean(java.type('petclinic.repositories.VetSpecialityRepository'))
    assert sorted(s.name for s in joins.findSpecialitiesByVetId(douglas.id)) == ['dentistry', 'surgery']

    owner = client.post('/owners/new', data={'firstName': 'Service', 'lastName': 'Facade',
                        'address': '1 Reference Road', 'city': 'Madison', 'telephone': '6085550000'},
                        allow_redirects=False)
    assert owner.status_code in (301, 302, 303), owner.text
    owner_url = owner.headers['location']
    owner_id = int(owner_url.rsplit('/', 1)[-1])
    pet = client.post(owner_url + '/pets/new', data={'name': 'FacadePet', 'birthDate': '2020-01-01', 'typeId': '2'},
                      allow_redirects=False)
    assert pet.status_code in (301, 302, 303), pet.text
    pet_id = int(re.search(r'/pets/(\d+)/edit', client.get(owner_url).text).group(1))
    visit = client.post(f'{owner_url}/pets/{pet_id}/visits/new', json={'date': '2029-11-20',
                        'description': 'Facade delete check', 'durationMinutes': 30, 'followUpPeriodMonths': 6},
                        allow_redirects=False)
    assert visit.status_code in (301, 302, 303), visit.text
    visits = service.find_visits_by_pet_id(pet_id)
    visit_id = next(v.id for v in visits if v.description == 'Facade delete check')
    assert service.find_visit_by_id(visit_id).description == 'Facade delete check'
    service.delete_visit(visit_id)
    assert service.find_visit_by_id(visit_id) is None
    service.delete_pet(pet_id)
    assert service.find_pet_by_id(pet_id) is None
    service.delete_owner(owner_id)
    assert service.find_owner_by_id(owner_id) is None
