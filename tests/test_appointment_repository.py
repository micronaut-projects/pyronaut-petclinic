"""The three Java AppointmentRepositoryTest contracts on every profile."""

import pytest
from petclinic.models.appointments import status_name


@pytest.fixture
def appointments(application_context):
    import java
    repository = application_context.java_ctx.getBean(java.type('petclinic.repositories.AppointmentRepository'))
    Appointment = java.type('petclinic.models.Appointment')
    Status = java.type('petclinic.models.AppointmentStatus')
    created = []
    def save(label, order, status=None):
        row = repository.save(Appointment(label, order, status or Status.AVAILABLE, None))
        created.append(row.id)
        return row
    try:
        yield repository, Appointment, Status, save
    finally:
        for id in created:
            repository.deleteById(id)


def test_appointments_available_rows_are_in_display_order(appointments):
    repository, Appointment, Status, save = appointments
    later = save('Later appointment', 100)
    earlier = save('Earlier appointment', 99)
    booked = save('Booked appointment', 98, Status.BOOKED_FOR_REGULAR)
    available = list(repository.findAvailableAppointments())
    assert all(status_name(a.status) == 'AVAILABLE' for a in available)
    assert [a.displayOrder for a in available] == sorted(a.displayOrder for a in available)
    ids = [a.id for a in available]
    assert ids.index(earlier.id) < ids.index(later.id) and booked.id not in ids


def test_appointments_save_existing_row_updates_without_inserting(appointments, application_context):
    import java
    repository, Appointment, Status, save = appointments
    original = save('Save regression appointment', 99)
    count = repository.count()
    def lock_and_update(transaction):
        locked = repository.findByIdForUpdate(original.id)
        assert locked.id == original.id
        for status in (Status.HELD_BY_REGULAR, Status.BOOKED_FOR_REGULAR):
            updated = repository.save(Appointment(original.label, original.displayOrder, status, original.id))
            assert updated.id == original.id and repository.count() == count
            assert status_name(repository.findOneById(original.id).status) == status_name(status)
        return original.id
    # The Java source runs inside @MicronautTest's write transaction. Our
    # HTTP fixture is deliberately non-transactional, so provide that boundary.
    operations = application_context.java_ctx.getBean(java.type('io.micronaut.transaction.TransactionOperations'))
    assert operations.executeWrite(lock_and_update) == original.id
    assert status_name(original.status) == 'AVAILABLE'


def test_appointments_booked_row_remains_findable(appointments):
    repository, Appointment, Status, save = appointments
    original = save('Appointment to book', 99)
    booked = repository.save(Appointment(original.label, original.displayOrder, Status.BOOKED_FOR_EMERGENCY, original.id))
    assert repository.existsById(booked.id)
    assert status_name(repository.findOneById(booked.id).status) == 'BOOKED_FOR_EMERGENCY'
    assert booked.id not in [a.id for a in repository.findAvailableAppointments()]
