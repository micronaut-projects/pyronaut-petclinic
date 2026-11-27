"""Appointments request, form and response DTOs."""

from dataclasses import dataclass

from micronaut.serde.annotation import Serdeable
from petclinic.models.appointments import AppointmentStatus, BookingOutcome, Appointment


@Serdeable
@dataclass
class OracleBookingResult:
    appointmentId: int
    outcome: BookingOutcome
    databaseStatus: AppointmentStatus
    availableAppointments: list[Appointment]
