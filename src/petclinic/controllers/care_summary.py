"""Download an owner's care history using schema-generated DTOs."""

from typing import Annotated
from jakarta.inject import Inject
from micronaut.http import HttpResponse, MediaType
from micronaut.http.annotation import Controller, Get
from micronaut.scheduling.annotation import ExecuteOn
from petclinic.mapper import FormMapper
from petclinic.services.clinic import ClinicService


@Controller('/owners/{ownerId}/care-summary')
@ExecuteOn('blocking')
class OwnerCareSummaryController:
    clinic_service: Annotated[ClinicService, Inject]
    mapper: Annotated[FormMapper, Inject]

    @Get(produces=MediaType.APPLICATION_JSON)
    def download(self, ownerId: int):
        owner = self.clinic_service.find_owner_by_id(ownerId)
        return (HttpResponse.ok(self.mapper.to_owner_care_summary(owner))
                .contentType(MediaType.APPLICATION_JSON)
                .header('Content-Disposition', f'attachment; filename="owner-{ownerId}-care-summary.json"'))
