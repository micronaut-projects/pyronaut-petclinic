"""Profile-specific loyalty lifecycle hooks and Oracle reservation transactions."""

from typing import Annotated, Protocol
from jakarta.inject import Inject, Singleton
from jakarta.transaction import Transactional
from java.lang import IllegalStateException, Throwable, Long
from java.time import LocalDateTime
from micronaut.context.annotation import Requires
from micronaut.context.event import StartupEvent
from micronaut.runtime.event.annotation import EventListener
from micronaut.data.exceptions import DataIntegrityViolationException
from micronaut.http import HttpStatus
from micronaut.http.exceptions import HttpStatusException
from petclinic.constants import DEFAULT_DIALECT_PROPERTY, DIALECT_ORACLE
from petclinic.dtos.loyalty import LoyaltyRedemptionResponse, LoyaltyVoucher, OwnerLoyaltySummary
from petclinic.errors import entity_not_found
from petclinic.models.loyalty import InsufficientLoyaltyPointsException, OwnerLoyaltyAccount, OwnerRewardVoucher
from petclinic.models.patients import Owner
from petclinic.repositories.loyalty import OwnerLoyaltyAccountRepository, OwnerRewardVoucherRepository
from petclinic.repositories.owners import OwnerRepository

POINTS_PER_VISIT = 25
REWARD_COST = 100


class OwnerLoyaltyService(Protocol):
    def is_enabled(self) -> bool: ...
    def create_account(self, owner: Owner) -> None: ...
    def find_owner_loyalty_account(self, owner: Owner) -> OwnerLoyaltyAccount: ...
    def ensure_accounts(self, owners: list[Owner]) -> None: ...
    def award_visit(self, owner: Owner) -> None: ...
    def delete_owner_data(self, owner: Owner) -> None: ...
    def summary(self, account: OwnerLoyaltyAccount) -> OwnerLoyaltySummary: ...
    def redeem(self, account: OwnerLoyaltyAccount) -> LoyaltyRedemptionResponse: ...


@Singleton
@Requires(property=DEFAULT_DIALECT_PROPERTY, notEquals=DIALECT_ORACLE)
class NoOpOwnerLoyaltyService(OwnerLoyaltyService):
    def is_enabled(self) -> bool:
        return False

    def create_account(self, owner: Owner) -> None:
        pass

    def find_owner_loyalty_account(self, owner: Owner) -> OwnerLoyaltyAccount:
        entity_not_found()

    def ensure_accounts(self, owners: list[Owner]) -> None:
        pass

    def award_visit(self, owner: Owner) -> None:
        pass

    def delete_owner_data(self, owner: Owner) -> None:
        pass

    def summary(self, account: OwnerLoyaltyAccount) -> OwnerLoyaltySummary:
        return OwnerLoyaltySummary(None, 0, 0, 0, [])

    def redeem(self, account: OwnerLoyaltyAccount) -> LoyaltyRedemptionResponse:
        entity_not_found()


@Singleton
@Requires(property=DEFAULT_DIALECT_PROPERTY, value=DIALECT_ORACLE)
class LoyaltyRedemptionService:
    accounts: Annotated[OwnerLoyaltyAccountRepository, Inject]
    vouchers: Annotated[OwnerRewardVoucherRepository, Inject]

    @Transactional(value=Transactional.TxType.REQUIRES_NEW, rollbackOn=[Throwable])
    def redeem(self, account: OwnerLoyaltyAccount, points_cost: Long) -> OwnerRewardVoucher:
        if points_cost <= 0:
            raise HttpStatusException(HttpStatus.BAD_REQUEST, 'The points cost must be positive.')
        try:
            updated = self.accounts.reserveDecrementPoints(account.id, points_cost)
        except DataIntegrityViolationException:
            raise InsufficientLoyaltyPointsException('Insufficient loyalty points.')
        if updated != 1:
            entity_not_found()
        return self.vouchers.save(OwnerRewardVoucher(account, 'PET_CARE_REWARD', points_cost, LocalDateTime.now()))


def voucher_view(voucher) -> LoyaltyVoucher:
    return LoyaltyVoucher('PCR-' + str(voucher.id).zfill(8), voucher.rewardCode, voucher.pointsSpent, voucher.createdAt)


@Singleton
@Requires(property=DEFAULT_DIALECT_PROPERTY, value=DIALECT_ORACLE)
class OracleOwnerLoyaltyService(OwnerLoyaltyService):
    accounts: Annotated[OwnerLoyaltyAccountRepository, Inject]
    vouchers: Annotated[OwnerRewardVoucherRepository, Inject]
    redemptions: Annotated[LoyaltyRedemptionService, Inject]

    def is_enabled(self) -> bool:
        return True

    @Transactional
    def create_account(self, owner: Owner) -> None:
        if self.accounts.findByOwner(owner) is None:
            self.accounts.insert(OwnerLoyaltyAccount(owner))

    def find_owner_loyalty_account(self, owner: Owner) -> OwnerLoyaltyAccount:
        account = self.accounts.findByOwner(owner)
        if account is None:
            entity_not_found()
        return account

    @Transactional
    def ensure_accounts(self, owners: list[Owner]) -> None:
        for owner in owners:
            self.create_account(owner)

    @Transactional
    def award_visit(self, owner: Owner) -> None:
        account = self.accounts.findByOwner(owner)
        if account is None:
            account = self.accounts.insert(OwnerLoyaltyAccount(owner))
        if self.accounts.reserveIncrementPoints(account.id, POINTS_PER_VISIT) != 1:
            raise IllegalStateException("The owner's loyalty account could not be credited.")

    @Transactional
    def delete_owner_data(self, owner: Owner) -> None:
        account = self.accounts.findByOwner(owner)
        if account is not None:
            self.vouchers.deleteByOwnerLoyaltyAccount(account)
        self.accounts.deleteByOwner(owner)

    def summary(self, account: OwnerLoyaltyAccount) -> OwnerLoyaltySummary:
        return OwnerLoyaltySummary(account.owner.id, account.points, POINTS_PER_VISIT, REWARD_COST,
            [voucher_view(v) for v in self.vouchers.findTop10ByOwnerLoyaltyAccountOrderByCreatedAtDescAndIdDesc(account)])

    def redeem(self, account: OwnerLoyaltyAccount) -> LoyaltyRedemptionResponse:
        voucher = self.redemptions.redeem(account, REWARD_COST)
        points = self.accounts.findPointsById(account.id).orElse(None)
        if points is None:
            entity_not_found()
        return LoyaltyRedemptionResponse(points, voucher_view(voucher))


@Singleton
@Requires(property=DEFAULT_DIALECT_PROPERTY, value=DIALECT_ORACLE)
@Requires(property='petclinic.sample-data.enabled', value='true', defaultValue='true')
class LoyaltyAccountLoader:
    loyalty: Annotated[OwnerLoyaltyService, Inject]
    owners: Annotated[OwnerRepository, Inject]

    @EventListener
    @Transactional
    def on_startup(self, event: StartupEvent) -> None:
        self.loyalty.ensure_accounts(list(self.owners.findAllOrderByLastName()))
