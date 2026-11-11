"""Generated Oracle lock-free reservation and voucher queries."""

from typing import Annotated, Optional, Protocol
from java.lang import Long
from micronaut.context.annotation import Requires
from micronaut.data.annotation import Id, Join
from micronaut.data.jdbc.annotation import JdbcRepository
from micronaut.data.model.query.builder.sql import Dialect
from micronaut.data.repository import CrudRepository, GenericRepository
from petclinic.constants import DEFAULT_DIALECT_PROPERTY, DIALECT_ORACLE
from petclinic.models.loyalty import OwnerLoyaltyAccount, OwnerRewardVoucher
from petclinic.models.patients import Owner


@Requires(property=DEFAULT_DIALECT_PROPERTY, value=DIALECT_ORACLE)
@JdbcRepository(dialect=Dialect.ORACLE)
class OwnerLoyaltyAccountRepository(GenericRepository[OwnerLoyaltyAccount, Long], Protocol):
    def insert(self, account: OwnerLoyaltyAccount) -> OwnerLoyaltyAccount: ...

    @Join(value='owner', type=Join.Type.LEFT_FETCH)
    def findByOwner(self, owner: Owner) -> OwnerLoyaltyAccount | None: ...

    @Join(value='owner', type=Join.Type.LEFT_FETCH)
    def findById(self, id: Long) -> OwnerLoyaltyAccount | None: ...

    def findPointsById(self, id: Long) -> Optional[Long]: ...

    def deleteByOwner(self, owner: Owner) -> None: ...

    def reserveIncrementPoints(self, accountId: Annotated[Long, Id], points: Long) -> Long: ...

    def reserveDecrementPoints(self, accountId: Annotated[Long, Id], points: Long) -> Long: ...


@Requires(property=DEFAULT_DIALECT_PROPERTY, value=DIALECT_ORACLE)
@JdbcRepository(dialect=Dialect.ORACLE)
class OwnerRewardVoucherRepository(CrudRepository[OwnerRewardVoucher, Long], Protocol):
    @Join(value='ownerLoyaltyAccount', type=Join.Type.LEFT_FETCH)
    @Join(value='ownerLoyaltyAccount.owner', type=Join.Type.LEFT_FETCH)
    def findTop10ByOwnerLoyaltyAccountOrderByCreatedAtDescAndIdDesc(self, account: OwnerLoyaltyAccount) -> list[OwnerRewardVoucher]: ...

    def deleteByOwnerLoyaltyAccount(self, account: OwnerLoyaltyAccount) -> None: ...
