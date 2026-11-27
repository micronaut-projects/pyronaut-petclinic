"""Real Oracle lock-free reservations, concurrency and committed visibility."""

import pytest
from loyalty_test_support import patients, loyalty, concurrent_posts
from petclinic_test_support import DATABASE

pytestmark = pytest.mark.skipif(DATABASE != 'oracle', reason='Oracle-only reservable loyalty feature')


def test_schema_enforces_reservable_nonnegative_unique_account_balance(loyalty):
    import java
    owner = loyalty.patients.owner()
    account = loyalty.accounts.findByOwner(owner)
    assert loyalty.scalar("SELECT RESERVABLE_COLUMN FROM USER_TAB_COLUMNS WHERE TABLE_NAME='OWNER_LOYALTY_ACCOUNT' AND COLUMN_NAME='POINTS'") == 'YES'
    assert loyalty.scalar("SELECT NULLABLE FROM USER_TAB_COLUMNS WHERE TABLE_NAME='OWNER_LOYALTY_ACCOUNT' AND COLUMN_NAME='POINTS'") == 'N'
    assert int(loyalty.scalar("SELECT COUNT(*) FROM USER_CONSTRAINTS WHERE TABLE_NAME='OWNER_LOYALTY_ACCOUNT' AND CONSTRAINT_TYPE='C' AND UPPER(SEARCH_CONDITION_VC) LIKE '%POINTS%>= 0%'")) > 0
    assert int(loyalty.scalar("SELECT COUNT(*) FROM USER_INDEXES WHERE TABLE_NAME='OWNER_LOYALTY_ACCOUNT' AND UNIQUENESS='UNIQUE' AND INDEX_NAME='UK_OWNER_LOYALTY_ACCOUNT_OWNER'")) == 1
    SQLException = java.type('java.sql.SQLException')
    try:
        loyalty.execute(f'UPDATE OWNER_LOYALTY_ACCOUNT SET POINTS = 500 WHERE ID={account.id}')
        raise AssertionError('Reservable points must reject direct assignment')
    except SQLException:
        pass
    assert loyalty.accounts.findPointsById(account.id).orElseThrow() == 0


def test_generated_reservation_methods_apply_64_bit_deltas_after_commit(loyalty):
    owner = loyalty.patients.owner()
    account = loyalty.accounts.findByOwner(owner)
    large = 2147483648
    assert loyalty.credit(account, large) == 1
    assert loyalty.accounts.findPointsById(account.id).orElseThrow() == large
    assert loyalty.debit(account, large - 75) == 1
    assert loyalty.accounts.findPointsById(account.id).orElseThrow() == 75


@pytest.mark.parametrize('points,expected_statuses,expected_balance', [
    (100, [201, 409], 0), (200, [201, 201], 0),
])
def test_simultaneous_redemptions_respect_available_balance(client, loyalty, points, expected_statuses, expected_balance):
    owner = loyalty.patients.owner()
    account = loyalty.accounts.findByOwner(owner)
    loyalty.credit(account, points)
    responses = concurrent_posts(client, [f'/owners/{owner.id}/loyalty/redemptions'] * 2)
    assert sorted(code for code, body in responses) == expected_statuses, responses
    assert loyalty.accounts.findPointsById(account.id).orElseThrow() == expected_balance
    vouchers = loyalty.vouchers.findTop10ByOwnerLoyaltyAccountOrderByCreatedAtDescAndIdDesc(account)
    assert len(vouchers) == expected_statuses.count(201)


def test_concurrent_visits_credit_every_committed_visit(client, loyalty):
    owner = loyalty.patients.owner()
    pet = loyalty.patients.pet(owner)
    paths = [f'/owners/{owner.id}/pets/{pet.id}/visits/new'] * 4
    bodies = [{'date': f'2025-02-0{day}', 'description': 'Concurrent credit ' + str(day),
               'durationMinutes': 30, 'followUpPeriodMonths': 6} for day in range(1, 5)]
    responses = concurrent_posts(client, paths, bodies)
    assert all(code in (301, 302, 303) for code, body in responses), responses
    account = loyalty.accounts.findByOwner(owner)
    assert loyalty.accounts.findPointsById(account.id).orElseThrow() == 100
    # The HTTP calls created these rows outside the fixture helper.
    for visit in loyalty.patients.clinic.find_visits_by_pet_id(pet.id):
        loyalty.patients.clinic.delete_visit(visit.id)


@pytest.mark.parametrize('commit_first,expected_balance', [(True, 0), (False, 100)])
def test_another_reservation_commits_before_the_first_completes(client, loyalty, commit_first, expected_balance):
    owner = loyalty.patients.owner()
    account = loyalty.accounts.findByOwner(owner)
    loyalty.credit(account, 200)
    holder = loyalty.source.getConnection()
    try:
        holder.setAutoCommit(False)
        statement = holder.prepareStatement('UPDATE OWNER_LOYALTY_ACCOUNT SET POINTS = POINTS - ? WHERE ID = ?')
        try:
            statement.setLong(1, 100)
            statement.setLong(2, account.id)
            assert statement.executeUpdate() == 1
            assert loyalty.accounts.findPointsById(account.id).orElseThrow() == 200
            # This request must complete while the independent reservation is open.
            response = client.post(f'/owners/{owner.id}/loyalty/redemptions', timeout=10)
            assert response.status_code == 201, response.text
            assert loyalty.accounts.findPointsById(account.id).orElseThrow() == 100
            holder.commit() if commit_first else holder.rollback()
            assert loyalty.accounts.findPointsById(account.id).orElseThrow() == expected_balance
        finally:
            statement.close()
    finally:
        holder.rollback()
        holder.close()


def test_rollback_releases_a_pending_reservation_for_redemption(client, loyalty):
    owner = loyalty.patients.owner()
    account = loyalty.accounts.findByOwner(owner)
    loyalty.credit(account, 100)
    holder = loyalty.source.getConnection()
    try:
        holder.setAutoCommit(False)
        statement = holder.prepareStatement('UPDATE OWNER_LOYALTY_ACCOUNT SET POINTS = POINTS - 100 WHERE ID = ?')
        try:
            statement.setLong(1, account.id)
            assert statement.executeUpdate() == 1
            rejected = client.post(f'/owners/{owner.id}/loyalty/redemptions', timeout=10)
            assert rejected.status_code == 409, rejected.text
            assert loyalty.accounts.findPointsById(account.id).orElseThrow() == 100
            holder.rollback()
            accepted = client.post(f'/owners/{owner.id}/loyalty/redemptions')
            assert accepted.status_code == 201, accepted.text
            assert loyalty.accounts.findPointsById(account.id).orElseThrow() == 0
        finally:
            statement.close()
    finally:
        holder.rollback()
        holder.close()


def test_generated_debit_is_visible_only_after_transaction_commit(loyalty):
    owner = loyalty.patients.owner()
    account = loyalty.accounts.findByOwner(owner)
    loyalty.credit(account, 100)
    def reserve(status):
        assert loyalty.accounts.reserveDecrementPoints(account.id, loyalty.Long.valueOf(25)) == 1
        assert loyalty.accounts.findPointsById(account.id).orElseThrow() == 100
        return None
    loyalty.operations.executeWrite(reserve)
    assert loyalty.accounts.findPointsById(account.id).orElseThrow() == 75
