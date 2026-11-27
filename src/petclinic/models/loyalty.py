"""Oracle reservable loyalty balances and issued reward vouchers."""

from dataclasses import dataclass
from typing import Annotated

from jakarta.validation.constraints import NotNull, PositiveOrZero
from java.lang import Long
from java.time import LocalDateTime
from micronaut.data.annotation import GeneratedValue, Id, Index, MappedEntity, MappedProperty, Relation, Reservable
from petclinic.models.patients import Owner


@MappedEntity('OWNER_LOYALTY_ACCOUNT')
@Index(name='UK_OWNER_LOYALTY_ACCOUNT_OWNER', columns=['OWNER_ID'], unique=True)
@dataclass
class OwnerLoyaltyAccount:
    owner: Annotated[Owner, Relation(Relation.Kind.ONE_TO_ONE), MappedProperty('OWNER_ID'), NotNull]
    points: Annotated[Long, Reservable, NotNull, PositiveOrZero] = 0
    id: Annotated[Long, Id, GeneratedValue] = None


@MappedEntity('OWNER_REWARD_VOUCHERS')
@dataclass
class OwnerRewardVoucher:
    ownerLoyaltyAccount: Annotated[OwnerLoyaltyAccount, Relation(Relation.Kind.MANY_TO_ONE), MappedProperty('OWNER_LOYALTY_ACCOUNT_ID'), NotNull]
    rewardCode: Annotated[str, MappedProperty('REWARD_CODE'), NotNull]
    pointsSpent: Annotated[Long, MappedProperty('POINTS_SPENT'), NotNull]
    createdAt: Annotated[LocalDateTime, MappedProperty('CREATED_AT'), NotNull]
    id: Annotated[Long, Id, GeneratedValue] = None


class InsufficientLoyaltyPointsException(RuntimeError):
    """The database rejected an unfunded points reservation."""
