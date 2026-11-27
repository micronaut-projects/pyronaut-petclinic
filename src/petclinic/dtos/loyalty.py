"""Public loyalty balance and redemption responses."""

from dataclasses import dataclass, field
from java.lang import Long
from java.time import LocalDateTime
from micronaut.serde.annotation import Serdeable


@Serdeable
@dataclass
class LoyaltyVoucher:
    reference: str
    rewardCode: str
    pointsSpent: Long
    createdAt: LocalDateTime


@Serdeable
@dataclass
class OwnerLoyaltySummary:
    ownerId: int | None
    points: Long
    pointsPerVisit: Long
    rewardCost: Long
    recentVouchers: list[LoyaltyVoucher] = field(default_factory=list)


@Serdeable
@dataclass
class LoyaltyRedemptionResponse:
    points: Long
    voucher: LoyaltyVoucher
