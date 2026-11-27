"""Transaction priority HTTP handling."""

import logging
from typing import Annotated

import java
from jakarta.inject import Inject
from java.lang import RuntimeException
from micronaut.context.annotation import Requires
from micronaut.data.exceptions import DataAccessException
from micronaut.http import HttpRequest, HttpResponse, HttpStatus, MediaType
from micronaut.http.annotation import Controller, Error, Get, Post, Produces, QueryValue
from micronaut.http.exceptions import HttpStatusException
from micronaut.scheduling.annotation import ExecuteOn
from micronaut.transaction.exceptions import OracleTransactionPriorityException, TransactionTimedOutException
from micronaut.views import View
from petclinic.constants import DEFAULT_DIALECT_PROPERTY, DIALECT_ORACLE
from petclinic.dtos.appointments import OracleBookingResult
from petclinic.models.appointments import AppointmentStatus, BookingType, BookingOutcome, BookingTaken, status_name, \
    with_status
from petclinic.repositories.appointments import AppointmentRepository
from petclinic.services.transaction_priority import OracleTransactionPriorityService

LOG = logging.getLogger(__name__)


def appointment_model(appointment) -> dict:
    return {'id': appointment.id, 'label': appointment.label, 'displayOrder': appointment.displayOrder,
            'status': status_name(appointment.status)}


def booking_outcome(error) -> BookingOutcome:
    if isinstance(error, OracleTransactionPriorityException):
        return BookingOutcome.PRIORITY_ROLLED_BACK
    # A service exception can cross the AOP/context boundary as its Java mirror.
    if isinstance(error, java.type('petclinic.models.BookingTaken')):
        return BookingOutcome.TAKEN
    if isinstance(error, BookingTaken):
        return BookingOutcome.TAKEN
    if isinstance(error, TransactionTimedOutException):
        return BookingOutcome.TIMED_OUT
    if isinstance(error, DataAccessException):
        cause = error.getCause()
        if cause is not None and hasattr(cause, 'getErrorCode') and cause.getErrorCode() in (54, 30006, 1013):
            return BookingOutcome.TIMED_OUT
    return BookingOutcome.FAILED


@Controller('/oracle/transaction-priority')
@Requires(property=DEFAULT_DIALECT_PROPERTY, value=DIALECT_ORACLE)
@ExecuteOn('blocking')
class OracleTransactionPriorityController:
    service: Annotated[OracleTransactionPriorityService, Inject]
    appointments: Annotated[AppointmentRepository, Inject]

    @Get
    @View('transaction-priority/showcase')
    @Produces(MediaType.TEXT_HTML)
    def page(self) -> dict:
        return {'appointments': [appointment_model(a) for a in self.appointments.findAvailableAppointments()],
                'reservationSeconds': self.service.get_reservation_seconds()}

    @Post('/reset')
    def reset(self) -> dict:
        try:
            self.service.reset_fixture()
        except (RuntimeException, Exception) as error:
            if booking_outcome(error) == BookingOutcome.TIMED_OUT:
                raise HttpStatusException(HttpStatus.CONFLICT,
                                          'A booking is still running. Wait for it to finish before resetting.')
            raise
        return {'status': 'reset'}

    @Post('/book')
    def book(self, appointmentId: Annotated[int, QueryValue], type: Annotated[str, QueryValue]):
        try:
            booking_type = BookingType(type.upper())
        except ValueError:
            raise HttpStatusException(HttpStatus.BAD_REQUEST, 'Invalid booking type.')
        if not self.appointments.existsById(appointmentId):
            raise HttpStatusException(HttpStatus.NOT_FOUND, 'Appointment not found.')
        outcome = BookingOutcome.COMMITTED
        try:
            if booking_type == BookingType.REGULAR:
                self.service.book_regular(appointmentId)
            else:
                self.service.book_emergency(appointmentId)
        except (RuntimeException, Exception) as error:
            outcome = booking_outcome(error)
            if outcome == BookingOutcome.FAILED:
                LOG.error('Appointment booking failed for appointmentId=%s: %s', appointmentId, error)
        booked = self.appointments.findOneById(appointmentId)
        if booked is None:
            raise HttpStatusException(HttpStatus.NOT_FOUND, 'Appointment not found.')
        status = {BookingOutcome.COMMITTED: HttpStatus.OK, BookingOutcome.PRIORITY_ROLLED_BACK: HttpStatus.CONFLICT,
                  BookingOutcome.TAKEN: HttpStatus.CONFLICT, BookingOutcome.TIMED_OUT: HttpStatus.SERVICE_UNAVAILABLE,
                  BookingOutcome.FAILED: HttpStatus.INTERNAL_SERVER_ERROR}[outcome]
        return HttpResponse.status(status).body(
            OracleBookingResult(appointmentId, outcome, AppointmentStatus(status_name(booked.status)),
                                [with_status(a, AppointmentStatus(status_name(a.status))) for a in
                                 self.appointments.findAvailableAppointments()]))

    @Error(exception=HttpStatusException)
    def lab_error(self, request: HttpRequest, error: HttpStatusException):
        body = {'message': error.getMessage()}
        if error.getStatus() == HttpStatus.NOT_FOUND:
            body['path'] = request.getPath()
        return HttpResponse.status(error.getStatus()).body(body)
