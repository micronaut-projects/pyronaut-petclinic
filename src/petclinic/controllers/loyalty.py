"""Oracle loyalty summary and fixed-cost reward redemption endpoints."""

from typing import Annotated
from jakarta.inject import Inject
from micronaut.context.annotation import Requires
from micronaut.http import HttpRequest, HttpResponse, HttpStatus
from micronaut.http.annotation import Controller, Error, Get, Post
from micronaut.http.server.util.locale import HttpLocaleResolver
from micronaut.scheduling.annotation import ExecuteOn
from petclinic.constants import DEFAULT_DIALECT_PROPERTY, DIALECT_ORACLE
from petclinic.models.loyalty import InsufficientLoyaltyPointsException
from petclinic.resources import ApplicationResources
from petclinic.services.clinic import ClinicService
from petclinic.services.loyalty import OwnerLoyaltyService


@Controller('/owners/{ownerId}/loyalty')
@ExecuteOn('blocking')
@Requires(property=DEFAULT_DIALECT_PROPERTY, value=DIALECT_ORACLE)
class OwnerLoyaltyController:
    clinic: Annotated[ClinicService, Inject]
    loyalty: Annotated[OwnerLoyaltyService, Inject]
    resources: Annotated[ApplicationResources, Inject]
    locales: Annotated[HttpLocaleResolver, Inject]

    @Get
    def get_loyalty(self, ownerId: int):
        account = self.loyalty.find_owner_loyalty_account(self.clinic.find_owner_by_id(ownerId))
        return self.loyalty.summary(account)

    @Post('/redemptions')
    def redeem(self, ownerId: int):
        account = self.loyalty.find_owner_loyalty_account(self.clinic.find_owner_by_id(ownerId))
        return HttpResponse.created(self.loyalty.redeem(account))

    @Error(exception=InsufficientLoyaltyPointsException)
    def insufficient_points(self, request: HttpRequest, error: InsufficientLoyaltyPointsException):
        language = str(self.locales.resolveOrDefault(request).getLanguage())
        return HttpResponse.status(HttpStatus.CONFLICT).body({
            'code': 'INSUFFICIENT_LOYALTY_POINTS',
            'message': self.resources.messages(language)['loyalty.insufficientPoints'],
        })
