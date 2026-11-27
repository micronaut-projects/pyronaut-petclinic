"""Clinics application services."""

from typing import Annotated

from jakarta.inject import Inject, Singleton
from jakarta.transaction import Transactional
from petclinic.dtos.clinics import ClinicServiceOfferingForm
from petclinic.models.clinics import Clinic, ClinicServiceOffering
from petclinic.repositories.clinics import ClinicRepository, ClinicServiceOfferingRepository


@Singleton
class ClinicBranchService:
    clinics: Annotated[ClinicRepository, Inject]
    offerings: Annotated[ClinicServiceOfferingRepository, Inject]

    def filter_availability(self, clinics: list[Clinic], accepting: bool | None, emergency: bool | None) -> list[
        Clinic]:
        if accepting is None and emergency is None:
            return list(clinics)
        if accepting is not None and emergency is not None:
            matches = self.clinics.findByAcceptingNewPatientsAndEmergencyService(accepting, emergency)
        elif accepting is not None:
            matches = self.clinics.findByAcceptingNewPatients(accepting)
        else:
            matches = self.clinics.findByEmergencyService(emergency)
        ids = {clinic.id for clinic in matches}
        return [clinic for clinic in clinics if clinic.id in ids]

    @Transactional
    def upsert_offering(self, clinic: Clinic, form: ClinicServiceOfferingForm) -> ClinicServiceOffering:
        self.offerings.upsert(ClinicServiceOffering(
            clinic=clinic, serviceCode=form.serviceCode, name=form.name,
            description=form.description, price=form.price, durationMinutes=form.durationMinutes,
        ))
        # Resolve the natural key after the atomic upsert, including drivers that
        # return a generated candidate ID rather than the existing row's ID.
        return self.offerings.findByClinicIdAndServiceCode(clinic.id, form.serviceCode)
