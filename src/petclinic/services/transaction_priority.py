"""Transaction priority application services."""

import time
from typing import Annotated

from jakarta.inject import Inject, Singleton
from micronaut.context.annotation import Requires, Value
from micronaut.transaction.annotation import OracleTransactional, Transactional
from petclinic.constants import DEFAULT_DIALECT_PROPERTY, DIALECT_ORACLE
from petclinic.models.appointments import AppointmentStatus, Appointment, BookingTaken, status_name, with_status
from petclinic.repositories.appointments import AppointmentRepository


@Singleton
@Requires(property=DEFAULT_DIALECT_PROPERTY, value=DIALECT_ORACLE)
class OracleTransactionPriorityService:
    appointments: Annotated[AppointmentRepository, Inject]
    reservationSeconds: Annotated[int, Value('${petclinic.transaction-priority.reservation-seconds:15}')]

    def get_reservation_seconds(self) -> int:
        return self.reservationSeconds

    def lock_available(self, appointment_id: int) -> Appointment:
        appointment = self.appointments.findByIdForUpdate(appointment_id)
        if appointment is None or status_name(appointment.status) != 'AVAILABLE':
            raise BookingTaken('The appointment has already been booked')
        return appointment

    @OracleTransactional(priority=OracleTransactional.Priority.LOW, timeout=30)
    def book_regular(self, appointment_id: int) -> None:
        appointment = self.lock_available(appointment_id)
        appointment = self.appointments.save(with_status(appointment, AppointmentStatus.HELD_BY_REGULAR))
        time.sleep(self.reservationSeconds)
        self.appointments.save(with_status(appointment, AppointmentStatus.BOOKED_FOR_REGULAR))

    @OracleTransactional(priority=OracleTransactional.Priority.HIGH, timeout=30)
    def book_emergency(self, appointment_id: int) -> None:
        appointment = self.lock_available(appointment_id)
        self.appointments.save(with_status(appointment, AppointmentStatus.BOOKED_FOR_EMERGENCY))

    @Transactional
    def reset_fixture(self) -> None:
        for appointment in self.appointments.findAll():
            self.appointments.save(with_status(appointment, AppointmentStatus.AVAILABLE))
