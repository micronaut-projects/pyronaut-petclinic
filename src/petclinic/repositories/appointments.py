"""Appointments repository contracts and database-specific implementations."""

from typing import Protocol

from micronaut.context.annotation import Requires
from micronaut.data.annotation import Query
from micronaut.data.jdbc.annotation import JdbcRepository
from micronaut.data.model.query.builder.sql import Dialect
from micronaut.data.repository import GenericRepository, CrudRepository
from petclinic.constants import DEFAULT_DIALECT_PROPERTY, DIALECT_H2, DIALECT_MYSQL, DIALECT_ORACLE, DIALECT_POSTGRES
from petclinic.models.appointments import Appointment


class AppointmentRepository(GenericRepository[Appointment, int], Protocol):
    @Query(value='SELECT a.* FROM APPOINTMENTS a WHERE a.ID = :appointmentId FOR UPDATE WAIT 10', nativeQuery=True)
    def findByIdForUpdate(self, appointmentId: int) -> Appointment | None: ...

    @Query(value="SELECT a.* FROM APPOINTMENTS a WHERE STATUS = 'AVAILABLE' ORDER BY DISPLAY_ORDER, ID",
           nativeQuery=True)
    def findAvailableAppointments(self) -> list[Appointment]: ...

    def findOneById(self, id: int) -> Appointment | None: ...


@Requires(property=DEFAULT_DIALECT_PROPERTY, value=DIALECT_H2)
@JdbcRepository(dialect=Dialect.H2)
class H2AppointmentRepository(AppointmentRepository, CrudRepository[Appointment, int], Protocol):

    @Query(value='SELECT a.* FROM APPOINTMENTS a WHERE a.ID = :appointmentId FOR UPDATE WAIT 10', nativeQuery=True)
    def findByIdForUpdate(self, appointmentId: int) -> Appointment | None: ...

    @Query(value="SELECT a.* FROM APPOINTMENTS a WHERE STATUS = 'AVAILABLE' ORDER BY DISPLAY_ORDER, ID",
           nativeQuery=True)
    def findAvailableAppointments(self) -> list[Appointment]: ...

    def findOneById(self, id: int) -> Appointment | None: ...


@Requires(property=DEFAULT_DIALECT_PROPERTY, value=DIALECT_ORACLE)
@JdbcRepository(dialect=Dialect.ORACLE)
class OracleAppointmentRepository(AppointmentRepository, CrudRepository[Appointment, int], Protocol):

    @Query(value='SELECT a.* FROM APPOINTMENTS a WHERE a.ID = :appointmentId FOR UPDATE WAIT 10', nativeQuery=True)
    def findByIdForUpdate(self, appointmentId: int) -> Appointment | None: ...

    @Query(value="SELECT a.* FROM APPOINTMENTS a WHERE STATUS = 'AVAILABLE' ORDER BY DISPLAY_ORDER, ID",
           nativeQuery=True)
    def findAvailableAppointments(self) -> list[Appointment]: ...

    def findOneById(self, id: int) -> Appointment | None: ...


@Requires(property=DEFAULT_DIALECT_PROPERTY, value=DIALECT_MYSQL)
@JdbcRepository(dialect=Dialect.MYSQL)
class MySqlAppointmentRepository(AppointmentRepository, CrudRepository[Appointment, int], Protocol):
    @Query(value="SELECT a.* FROM APPOINTMENTS a WHERE a.ID = :appointmentId FOR UPDATE", nativeQuery=True)
    def findByIdForUpdate(self, appointmentId: int) -> Appointment | None: ...

    @Query(value="SELECT a.* FROM APPOINTMENTS a WHERE STATUS = 'AVAILABLE' ORDER BY DISPLAY_ORDER, ID",
           nativeQuery=True)
    def findAvailableAppointments(self) -> list[Appointment]: ...

    def findOneById(self, id: int) -> Appointment | None: ...


@Requires(property=DEFAULT_DIALECT_PROPERTY, value=DIALECT_POSTGRES)
@JdbcRepository(dialect=Dialect.POSTGRES)
class PostgresAppointmentRepository(AppointmentRepository, CrudRepository[Appointment, int], Protocol):
    @Query(value='SELECT a.* FROM "APPOINTMENTS" a WHERE "STATUS" = \'AVAILABLE\' ORDER BY "DISPLAY_ORDER", ID',
           nativeQuery=True)
    def findAvailableAppointments(self) -> list[Appointment]: ...

    @Query(value='SELECT a.* FROM "APPOINTMENTS" a WHERE a.ID = :appointmentId FOR UPDATE', nativeQuery=True)
    def findByIdForUpdate(self, appointmentId: int) -> Appointment | None: ...

    def findOneById(self, id: int) -> Appointment | None: ...
