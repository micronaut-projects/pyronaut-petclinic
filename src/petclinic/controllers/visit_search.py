"""Visit search HTTP handling."""

from datetime import date
from typing import Annotated

from jakarta.inject import Inject
from java.time import LocalDate
from micronaut.context.annotation import Requires
from micronaut.http import HttpResponse, MediaType
from micronaut.http.annotation import Controller, Get, Produces, QueryValue
from micronaut.views import View
from petclinic.constants import DEFAULT_DIALECT_PROPERTY, DIALECT_ORACLE
from petclinic.services.clinic import ClinicService


@Controller('/visits')
@Requires(property=DEFAULT_DIALECT_PROPERTY, value=DIALECT_ORACLE)
class VisitSearchController:
    clinic_service: Annotated[ClinicService, Inject]

    @Get
    @View("visits/searchVisits")
    def visit_search_page(self) -> dict:
        return {"year": date.today().year}

    @Get("/search")
    @Produces(MediaType.APPLICATION_JSON)
    def search_visits(
            self,
            fromDate: Annotated[str, QueryValue],
            toDate: Annotated[str, QueryValue],
            maxDurationMinutes: Annotated[int, QueryValue(defaultValue="120")] = 120,
            maxFollowUpMonths: Annotated[int, QueryValue(defaultValue="12")] = 12,
    ):
        try:
            start = date.fromisoformat(fromDate)
            end = date.fromisoformat(toDate)
        except ValueError:
            return HttpResponse.badRequest({"message": "Dates must be valid ISO dates (YYYY-MM-DD)."})
        return self.clinic_service.search_visits(LocalDate.parse(start.isoformat()), LocalDate.parse(end.isoformat()),
                                                 maxDurationMinutes, maxFollowUpMonths)
