"""Vets HTTP handling."""

from typing import Annotated

from jakarta.inject import Inject
from jakarta.validation import Validator
from micronaut.http import HttpResponse, HttpStatus, MediaType
from micronaut.http.annotation import Body, Controller, Delete, Get, Header, Post, Put, QueryValue
from micronaut.http.exceptions import HttpStatusException
from micronaut.http.server.exceptions import NotFoundException
from micronaut.scheduling.annotation import ExecuteOn
from micronaut.views import View
from petclinic.dtos.vets import VetForm, SpecialityForm
from petclinic.services.vets import domain_error, VetService
from petclinic.services.view_models import vet_view_models


def speciality_model(speciality) -> dict:
    return {'id': speciality.id, 'name': speciality.name}


def vet_model(vet) -> dict:
    return {'id': vet.id, 'firstName': vet.firstName, 'lastName': vet.lastName,
            'specialities': [speciality_model(s) for s in vet.specialities], 'etag': vet.etag}


@Controller('/vets')
@ExecuteOn('blocking')
class VetController:
    service: Annotated[VetService, Inject]
    validator: Annotated[Validator, Inject]

    def validate(self, form):
        if list(self.validator.validate(form)):
            domain_error(HttpStatus.BAD_REQUEST, 'Invalid request.')

    def response(self, vet, status=HttpStatus.OK):
        return (HttpResponse.status(status).header('ETag', '"' + vet.etag + '"')
                .header('Cache-Control', 'no-store').body(vet_model(vet)))

    @Get
    @View('vets/vetList')
    def page(self, saved: Annotated[bool, QueryValue(defaultValue='false')] = False):
        return {'vets': vet_view_models(self.service.find_all()), 'saved': saved}

    @Get('/html')
    @View('vets/vetList')
    def html(self, saved: Annotated[bool, QueryValue(defaultValue='false')] = False):
        return self.page(saved)

    @Get('/json')
    def listing(self):
        return [vet_model(v) for v in self.service.find_all()]

    @Get('/new')
    @View('vets/createOrUpdateVetForm')
    def new_vet(self):
        return {'vetForm': {'specialityIds': []}, 'specialities': list(self.service.specialities.findAllOrderByName()),
                'isNew': True, 'saved': False}

    @Get('/{id}/edit')
    @View('vets/createOrUpdateVetForm')
    def edit(self, id: int, saved: Annotated[bool, QueryValue(defaultValue='false')] = False):
        try:
            vet = self.service.find(id)
        except HttpStatusException:
            raise NotFoundException()
        return {'vetForm': {**vet_model(vet), 'specialityIds': [s.id for s in vet.specialities]},
                'specialities': list(self.service.specialities.findAllOrderByName()), 'isNew': False, 'saved': saved}

    @Post(consumes=MediaType.APPLICATION_JSON)
    def create(self, form: Annotated[VetForm, Body]):
        self.validate(form)
        return self.response(self.service.create(form), HttpStatus.CREATED)

    @Get('/{id}')
    def read(self, id: int):
        return self.response(self.service.find(id))

    @Put(value='/{id}', consumes=MediaType.APPLICATION_JSON)
    def update(self, id: int, form: Annotated[VetForm, Body],
               ifMatch: Annotated[str | None, Header('If-Match')] = None):
        self.validate(form)
        return self.response(self.service.update(id, form, ifMatch))

    @Delete('/{id}')
    def delete(self, id: int, ifMatch: Annotated[str | None, Header('If-Match')] = None):
        self.service.delete(id, ifMatch)
        return HttpResponse.noContent()

    @Get('/specialities')
    @View('vets/specialityList')
    def specialities(self, created: Annotated[bool, QueryValue(defaultValue='false')] = False,
                     changed: Annotated[bool, QueryValue(defaultValue='false')] = False):
        return {'specialities': list(self.service.specialities.findAllOrderByName()),
                'created': created, 'changed': changed}

    @Get('/specialities/json')
    def speciality_listing(self):
        return [speciality_model(s) for s in self.service.specialities.findAllOrderByName()]

    @Get('/specialities/new')
    @View('vets/createOrUpdateSpecialityForm')
    def new_speciality(self, duplicate: Annotated[bool, QueryValue(defaultValue='false')] = False):
        return {'specialityForm': {}, 'isNew': True, 'saved': False, 'duplicate': duplicate}

    @Get('/specialities/{id}/edit')
    @View('vets/createOrUpdateSpecialityForm')
    def edit_speciality(self, id: int, saved: Annotated[bool, QueryValue(defaultValue='false')] = False,
                        duplicate: Annotated[bool, QueryValue(defaultValue='false')] = False):
        try:
            speciality = self.service.find_speciality(id)
        except HttpStatusException:
            raise NotFoundException()
        return {'specialityForm': speciality_model(speciality), 'isNew': False, 'saved': saved, 'duplicate': duplicate}

    @Post(value='/specialities', consumes=MediaType.APPLICATION_JSON)
    def create_speciality(self, form: Annotated[SpecialityForm, Body]):
        self.validate(form)
        return HttpResponse.created(speciality_model(self.service.create_speciality(form)))

    @Put(value='/specialities/{id}', consumes=MediaType.APPLICATION_JSON)
    def update_speciality(self, id: int, form: Annotated[SpecialityForm, Body]):
        self.validate(form)
        if form.id is not None and form.id != id:
            domain_error(HttpStatus.BAD_REQUEST, 'Id should match the one in the url')
        return speciality_model(self.service.update_speciality(id, form))
