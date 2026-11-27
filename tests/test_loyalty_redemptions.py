"""Voucher redemption, constraint rollback and localized loyalty presentation."""

import pytest
from loyalty_test_support import patients, loyalty
from petclinic_test_support import DATABASE

pytestmark = pytest.mark.skipif(DATABASE != 'oracle', reason='Oracle-only reservable loyalty feature')


def test_four_new_visits_redeem_one_reward_and_short_balance_conflicts(client, loyalty):
    p = loyalty.patients
    owner = p.owner()
    pet = p.pet(owner)
    for day in range(1, 5):
        p.visit(pet, day)
    account = loyalty.accounts.findByOwner(owner)
    response = client.post(f'/owners/{owner.id}/loyalty/redemptions')
    assert response.status_code == 201, response.text
    body = response.json()
    assert body['points'] == 0 and body['voucher']['pointsSpent'] == 100
    assert body['voucher']['reference'].startswith('PCR-')
    assert body['voucher']['rewardCode'] == 'PET_CARE_REWARD'
    assert loyalty.accounts.findPointsById(account.id).orElseThrow() == 0
    assert len(loyalty.vouchers.findTop10ByOwnerLoyaltyAccountOrderByCreatedAtDescAndIdDesc(account)) == 1
    short_owner = p.owner()
    short_pet = p.pet(short_owner)
    for day in range(1, 4):
        p.visit(short_pet, day)
    conflict = client.post(f'/owners/{short_owner.id}/loyalty/redemptions')
    assert conflict.status_code == 409, conflict.text
    assert conflict.json()['code'] == 'INSUFFICIENT_LOYALTY_POINTS'
    short_account = loyalty.accounts.findByOwner(short_owner)
    assert loyalty.accounts.findPointsById(short_account.id).orElseThrow() == 75
    assert list(loyalty.vouchers.findTop10ByOwnerLoyaltyAccountOrderByCreatedAtDescAndIdDesc(short_account)) == []


def test_voucher_failure_rolls_back_reserved_points(loyalty):
    import java
    owner = loyalty.patients.owner()
    account = loyalty.accounts.findByOwner(owner)
    loyalty.credit(account, 200)
    loyalty.execute(f"ALTER TABLE OWNER_REWARD_VOUCHERS ADD CONSTRAINT TEST_PORT_VOUCHER_FAIL CHECK (OWNER_LOYALTY_ACCOUNT_ID <> {account.id} OR REWARD_CODE <> 'PET_CARE_REWARD')")
    try:
        DataIntegrityViolationException = java.type('io.micronaut.data.exceptions.DataIntegrityViolationException')
        try:
            loyalty.service.redeem(account)
            raise AssertionError('The voucher constraint must reject redemption')
        except DataIntegrityViolationException:
            pass
        assert loyalty.accounts.findPointsById(account.id).orElseThrow() == 200
        assert list(loyalty.vouchers.findTop10ByOwnerLoyaltyAccountOrderByCreatedAtDescAndIdDesc(account)) == []
    finally:
        loyalty.execute('ALTER TABLE OWNER_REWARD_VOUCHERS DROP CONSTRAINT TEST_PORT_VOUCHER_FAIL')


@pytest.mark.parametrize('points_cost', [0, -1, -100])
def test_invalid_reward_costs_do_not_mutate_balance(loyalty, points_cost):
    import java
    owner = loyalty.patients.owner()
    account = loyalty.accounts.findByOwner(owner)
    loyalty.credit(account, 200)
    HttpStatusException = java.type('io.micronaut.http.exceptions.HttpStatusException')
    try:
        loyalty.redemption.redeem(account, loyalty.Long.valueOf(points_cost))
        raise AssertionError('Nonpositive redemption costs must fail')
    except HttpStatusException as error:
        assert error.getStatus().getCode() == 400
    assert loyalty.accounts.findPointsById(account.id).orElseThrow() == 200
    assert list(loyalty.vouchers.findTop10ByOwnerLoyaltyAccountOrderByCreatedAtDescAndIdDesc(account)) == []


def test_account_deleted_after_lookup_reports_not_found(loyalty):
    import java
    owner = loyalty.patients.owner()
    account = loyalty.accounts.findByOwner(owner)
    loyalty.accounts.deleteByOwner(owner)
    HttpStatusException = java.type('io.micronaut.http.exceptions.HttpStatusException')
    try:
        loyalty.redemption.redeem(account, loyalty.Long.valueOf(100))
        raise AssertionError('A missing account must fail redemption')
    except HttpStatusException as error:
        assert error.getStatus().getCode() == 404


def test_recent_vouchers_are_limited_and_ordered_by_date_then_id(client, loyalty):
    import java
    owner = loyalty.patients.owner()
    account = loyalty.accounts.findByOwner(owner)
    Voucher = java.type('petclinic.models.OwnerRewardVoucher')
    LocalDateTime = java.type('java.time.LocalDateTime')
    beginning = LocalDateTime.parse('2025-01-01T00:00:00')
    for day in range(12):
        loyalty.vouchers.save(Voucher(account, 'PET_CARE_REWARD', loyalty.Long.valueOf(100), beginning.plusDays(day), None))
    latest = beginning.plusDays(11)
    tied = loyalty.vouchers.save(Voucher(account, 'PET_CARE_REWARD', loyalty.Long.valueOf(100), latest, None))
    summary = client.get(f'/owners/{owner.id}/loyalty')
    assert summary.status_code == 200, summary.text
    body = summary.json()
    assert body['pointsPerVisit'] == 25 and body['rewardCost'] == 100
    recent = body['recentVouchers']
    assert len(recent) == 10
    assert recent[0]['reference'] == 'PCR-' + str(tied.id).zfill(8)
    assert [v['createdAt'] for v in recent] == sorted([v['createdAt'] for v in recent], reverse=True)


@pytest.mark.parametrize('language', ['en', 'es', 'de'])
def test_loyalty_labels_dates_and_conflicts_follow_selected_locale(client, loyalty, language):
    import java
    owner = loyalty.patients.owner()
    account = loyalty.accounts.findByOwner(owner)
    Voucher = java.type('petclinic.models.OwnerRewardVoucher')
    LocalDateTime = java.type('java.time.LocalDateTime')
    timestamp = LocalDateTime.parse('2025-07-14T12:00:00')
    loyalty.vouchers.save(Voucher(account, 'PET_CARE_REWARD', loyalty.Long.valueOf(100), timestamp, None))
    resources = loyalty.patients.context.getBean(java.type('petclinic.ApplicationResources'))
    messages = resources.messages(language)
    formatter = java.type('java.time.format.DateTimeFormatter').ofLocalizedDate(java.type('java.time.format.FormatStyle').MEDIUM)
    formatter = formatter.withLocale(java.type('java.util.Locale').forLanguageTag(language))
    client.get('/locale', params={'lang': language}, allow_redirects=False)
    try:
        page = client.get(f'/owners/{owner.id}')
        assert page.status_code == 200, page.text
        start = page.text.index('<section id="owner-loyalty-card"')
        card = page.text[start:page.text.index('</section>', start)]
        assert f'data-locale="{language}"' in card and str(timestamp.format(formatter)) in card
        for key in ['title', 'balance', 'points', 'recentVouchers', 'noVouchers', 'success',
                    'insufficientPoints', 'ownerNotFound', 'requestFailed']:
            from html import unescape
            assert str(messages['loyalty.' + key]) in unescape(card), key
        assert 'loyalty.' not in card and '2025-07-14</time>' not in card
        script = client.get('/resources/js/owner-loyalty.js')
        assert script.status_code == 200 and 'javascript' in script.headers['content-type']
        conflict = client.post(f'/owners/{owner.id}/loyalty/redemptions')
        assert conflict.status_code == 409, conflict.text
        assert conflict.json() == {'code': 'INSUFFICIENT_LOYALTY_POINTS', 'message': str(messages['loyalty.insufficientPoints'])}
    finally:
        client.get('/locale', params={'lang': 'en'}, allow_redirects=False)


def test_redemption_service_reports_insufficient_points_without_mutation(loyalty):
    import java
    owner = loyalty.patients.owner()
    account = loyalty.accounts.findByOwner(owner)
    loyalty.credit(account, 75)
    from petclinic.models.loyalty import InsufficientLoyaltyPointsException
    JavaInsufficientPoints = java.type('petclinic.models.InsufficientLoyaltyPointsException')
    try:
        loyalty.redemption.redeem(account, loyalty.Long.valueOf(100))
        raise AssertionError('An unfunded reservation must fail')
    # Direct calls may expose the native exception or its generated Java mirror.
    except JavaInsufficientPoints:
        pass
    except InsufficientLoyaltyPointsException:
        pass
    assert loyalty.accounts.findPointsById(account.id).orElseThrow() == 75
    assert list(loyalty.vouchers.findTop10ByOwnerLoyaltyAccountOrderByCreatedAtDescAndIdDesc(account)) == []
