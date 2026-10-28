"""Care records HTTP handling."""

from typing import Annotated

from jakarta.inject import Inject
from jakarta.validation import Validator
from java.sql import SQLException
from micronaut.context.annotation import Requires
from micronaut.data.exceptions import DataAccessException, OptimisticLockException
from micronaut.http import HttpResponse, HttpStatus, MediaType
from micronaut.http.annotation import Body, Controller, Get, Put
from petclinic.constants import DEFAULT_DIALECT_PROPERTY, DIALECT_ORACLE
from petclinic.errors import entity_not_found
from petclinic.models.care_records import OwnerCareView
from petclinic.services.care_records import OwnerCareViewService
from petclinic.validation import violation_path


def missing_document():
    return entity_not_found()


def disallowed_operation(error) -> bool:
    cause = error
    while cause is not None and cause != None:
        if isinstance(cause, SQLException):
            sql = cause
            while sql is not None and sql != None:
                if sql.getErrorCode() in (40937, 40938, 40939, 40940, 42689):
                    return True
                sql = sql.getNextException()
        cause = cause.getCause()
    return False


@Controller('/')
@Requires(property=DEFAULT_DIALECT_PROPERTY, value=DIALECT_ORACLE)
class OwnerCareRecordController:
    service: Annotated[OwnerCareViewService, Inject]
    validator: Annotated[Validator, Inject]

    @Get('/owners/{ownerId}/care-record')
    def get_care_record(self, ownerId: int):
        document = self.service.find(ownerId)
        return document if document is not None else missing_document()

    @Put(value='/owners/{ownerId}/care-record', consumes=MediaType.APPLICATION_JSON)
    def update_care_record(self, ownerId: int, document: Annotated[OwnerCareView, Body]):
        violations = sorted(violation_path(v) + ': ' + str(v.getMessage()) for v in self.validator.validate(document))
        # Validate collection children explicitly: type-use @Valid did not cascade
        # on the earlier SDK and produces invalid constructor annotations in 0.1.1.
        # Each child retains its Jakarta field constraints and indexed error path.
        for pet_index, pet in enumerate(document.pets):
            prefix = 'pets[' + str(pet_index) + ']'
            violations.extend(
                prefix + '.' + violation_path(v) + ': ' + str(v.getMessage()) for v in self.validator.validate(pet))
            for visit_index, visit in enumerate(pet.visits):
                visit_prefix = prefix + '.visits[' + str(visit_index) + ']'
                violations.extend(visit_prefix + '.' + violation_path(v) + ': ' + str(v.getMessage()) for v in
                                  self.validator.validate(visit))
        if violations:
            return HttpResponse.badRequest({'message': '; '.join(sorted(violations))})
        if ownerId != document.id:
            return HttpResponse.badRequest({'message': 'The document _id must match the owner in the URL.'})
        if self.service.find(ownerId) is None:
            return missing_document()
        try:
            updated = self.service.update(document)
        except OptimisticLockException:
            return HttpResponse.status(HttpStatus.CONFLICT).body(
                {'message': 'This owner record changed after it was loaded. Reload it before saving.'})
        except DataAccessException as error:
            if disallowed_operation(error):
                return HttpResponse.badRequest({'message': 'The requested operation is not allowed.'})
            raise
        return updated if updated is not None else missing_document()
