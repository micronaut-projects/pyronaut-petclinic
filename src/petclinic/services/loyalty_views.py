"""Localized presentation of loyalty DTOs on the owner details page."""

from java.time import LocalDateTime
from java.time.format import DateTimeFormatter, FormatStyle
from java.util import Locale


def loyalty_view_model(summary, language: str) -> dict:
    formatter = DateTimeFormatter.ofLocalizedDate(FormatStyle.MEDIUM).withLocale(Locale.forLanguageTag(language))
    vouchers = []
    for voucher in summary.recentVouchers:
        timestamp = LocalDateTime.parse(str(voucher.createdAt).replace(' ', 'T'))
        vouchers.append({'reference': voucher.reference, 'createdAt': str(timestamp),
                         'displayDate': timestamp.format(formatter)})
    return {'points': summary.points, 'pointsPerVisit': summary.pointsPerVisit,
            'rewardCost': summary.rewardCost, 'recentVouchers': vouchers}
