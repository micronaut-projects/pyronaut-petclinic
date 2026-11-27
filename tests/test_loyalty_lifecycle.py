"""Oracle account provisioning and visit-credit lifecycle from the Java suite."""

import pytest
from loyalty_test_support import patients, loyalty
from petclinic_test_support import DATABASE

pytestmark = pytest.mark.skipif(DATABASE != 'oracle', reason='Oracle-only reservable loyalty feature')


def test_new_owners_visits_and_edits_maintain_the_expected_points(client, loyalty):
    p = loyalty.patients
    owner = p.owner()
    account = loyalty.accounts.findByOwner(owner)
    assert account is not None and account.points == 0
    pet = p.pet(owner)
    visit = p.visit(pet)
    assert loyalty.accounts.findPointsById(account.id).orElseThrow() == 25
    import java
    Visit = java.type('petclinic.models.Visit')
    updated = Visit(visit.date, 'Edited description', pet, visit.id, visit.duration, visit.period)
    p.clinic.save_visit(updated)
    fields = {key: str(getattr(owner, key)) for key in ('firstName', 'lastName', 'address', 'city', 'telephone')}
    fields['city'] = 'Updated City'
    response = client.post(f'/owners/{owner.id}/edit', data=fields, allow_redirects=False)
    assert response.status_code in (301, 302, 303), response.text
    assert loyalty.accounts.findPointsById(account.id).orElseThrow() == 25
    p.clinic.delete_visit(visit.id)
    assert loyalty.accounts.findPointsById(account.id).orElseThrow() == 25


def test_reconciliation_creates_zero_balance_without_historical_credit(loyalty):
    p = loyalty.patients
    owner = p.owner(raw=True)
    pet = p.pet(owner)
    for day in range(1, 5):
        p.visit(pet, day, raw=True)
    assert loyalty.accounts.findByOwner(owner) is None
    loyalty.service.ensure_accounts([owner])
    account = loyalty.accounts.findByOwner(owner)
    assert account.points == 0
    loyalty.credit(account, 75)
    loyalty.service.ensure_accounts([owner])
    loyalty.service.create_account(owner)
    assert loyalty.accounts.findByOwner(owner).id == account.id
    assert loyalty.accounts.findPointsById(account.id).orElseThrow() == 75


def test_missing_account_reads_hide_card_without_provisioning(client, loyalty):
    owner = loyalty.patients.owner(raw=True)
    for path, method in [(f'/owners/{owner.id}/loyalty', client.get),
                         (f'/owners/{owner.id}/loyalty/redemptions', client.post)]:
        response = method(path)
        assert response.status_code == 404, response.text
    page = client.get(f'/owners/{owner.id}')
    assert page.status_code == 200 and owner.lastName in page.text
    assert 'id="owner-loyalty-card"' not in page.text
    assert loyalty.accounts.findByOwner(owner) is None
    pet = loyalty.patients.pet(owner)
    loyalty.patients.visit(pet)
    assert loyalty.accounts.findByOwner(owner).points == 25


def test_unknown_owner_returns_not_found_from_both_loyalty_endpoints(client):
    assert client.get('/owners/2147483647/loyalty').status_code == 404
    assert client.post('/owners/2147483647/loyalty/redemptions').status_code == 404


@pytest.mark.parametrize('missing_account', [False, True])
def test_rolling_back_visit_rolls_back_credit_and_account_provisioning(loyalty, missing_account):
    owner = loyalty.patients.owner(raw=missing_account)
    pet = loyalty.patients.pet(owner)
    before = len(loyalty.patients.clinic.find_visits_by_pet_id(pet.id))
    def create_and_rollback(status):
        visit = loyalty.patients.visit(pet)
        status.setRollbackOnly()
        return visit.id
    loyalty.operations.executeWrite(create_and_rollback)
    account = loyalty.accounts.findByOwner(owner)
    if missing_account:
        assert account is None
    else:
        assert account.points == 0
    assert len(loyalty.patients.clinic.find_visits_by_pet_id(pet.id)) == before


def test_failed_credit_rolls_back_inserted_visit(loyalty):
    owner = loyalty.patients.owner()
    pet = loyalty.patients.pet(owner)
    account = loyalty.accounts.findByOwner(owner)
    loyalty.credit(account, 100)
    before = len(loyalty.patients.clinic.find_visits_by_pet_id(pet.id))
    loyalty.execute(f'ALTER TABLE OWNER_LOYALTY_ACCOUNT ADD CONSTRAINT TEST_PORT_LOYALTY_MAX CHECK (OWNER_ID <> {owner.id} OR POINTS <= 100)')
    try:
        import java
        RuntimeException = java.type('java.lang.RuntimeException')
        try:
            loyalty.patients.visit(pet)
            raise AssertionError('The credit constraint must reject this visit')
        except RuntimeException:
            pass
        assert len(loyalty.patients.clinic.find_visits_by_pet_id(pet.id)) == before
        assert loyalty.accounts.findPointsById(account.id).orElseThrow() == 100
    finally:
        loyalty.execute('ALTER TABLE OWNER_LOYALTY_ACCOUNT DROP CONSTRAINT TEST_PORT_LOYALTY_MAX')


def test_deleting_owner_removes_account_and_vouchers(loyalty):
    owner = loyalty.patients.owner()
    account = loyalty.accounts.findByOwner(owner)
    loyalty.credit(account, 100)
    loyalty.service.redeem(account)
    loyalty.patients.clinic.delete_owner(owner)
    assert loyalty.accounts.findByOwner(owner) is None
    assert list(loyalty.vouchers.findTop10ByOwnerLoyaltyAccountOrderByCreatedAtDescAndIdDesc(account)) == []


def test_duality_updates_preserve_the_separate_loyalty_balance(client, loyalty):
    owner = loyalty.patients.owner()
    loyalty.patients.pet(owner)
    account = loyalty.accounts.findByOwner(owner)
    loyalty.credit(account, 75)
    path = f'/owners/{owner.id}/care-record'
    original = client.get(path)
    assert original.status_code == 200, original.text
    changed = original.json()
    changed['city'] = 'Updated through JSON'
    response = client.put(path, json=changed)
    assert response.status_code == 200, response.text
    assert loyalty.accounts.findPointsById(account.id).orElseThrow() == 75


def test_startup_provisions_existing_owners_without_missing_accounts(loyalty):
    for owner in loyalty.patients.clinic.find_all_owners():
        account = loyalty.accounts.findByOwner(owner)
        assert account is not None, owner.id
        assert account.owner.id == owner.id


def test_account_lookup_never_provisions_but_explicit_creation_preserves_balance(loyalty):
    import java
    owner = loyalty.patients.owner(raw=True)
    HttpStatusException = java.type('io.micronaut.http.exceptions.HttpStatusException')
    try:
        loyalty.service.find_owner_loyalty_account(owner)
        raise AssertionError('Lookup must not create an account')
    except HttpStatusException as error:
        assert error.getStatus().getCode() == 404
    assert loyalty.accounts.findByOwner(owner) is None
    loyalty.service.create_account(owner)
    account = loyalty.service.find_owner_loyalty_account(owner)
    loyalty.credit(account, 75)
    loyalty.service.create_account(owner)
    assert loyalty.service.find_owner_loyalty_account(owner).points == 75
    assert loyalty.accounts.findByOwner(owner).id == account.id
