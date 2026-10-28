"""Shared locale and view-model infrastructure from the reference application."""

from typing import Annotated

from jakarta.inject import Inject, Singleton
from java.lang import String
from micronaut.context import MessageSource
from micronaut.context.annotation import Factory
from micronaut.context.env import Environment
from micronaut.context.i18n import ResourceBundleMessageSource
from micronaut.http import HttpRequest
from micronaut.http.server.util.locale import HttpLocaleResolver
from micronaut.views import ModelAndView
from micronaut.views.model import ViewModelProcessor

from .constants import DEFAULT_DIALECT_PROPERTY, DIALECT_ORACLE
from .resources import ApplicationResources


@Factory
class ViewSupport:
    resources: Annotated[ApplicationResources, Inject]
    locales: Annotated[HttpLocaleResolver, Inject]
    environment: Annotated[Environment, Inject]

    @Singleton
    def message_source(self) -> MessageSource:
        return ResourceBundleMessageSource("i18n.messages")

    @Singleton
    def view_processor(self) -> ViewModelProcessor[dict, HttpRequest]:
        def process(request: HttpRequest, modelAndView: ModelAndView[dict]):
            locale = self.locales.resolveOrDefault(request)
            messages = self.resources.messages(str(locale.getLanguage()))
            # Jinjava reads map properties directly; no template access to a
            # Python callable is required to resolve the reference message keys.
            model = dict(modelAndView.getModel().orElse({}))
            model.setdefault("msg", messages)
            model.setdefault("locale", str(locale))
            model.setdefault("requestPath", str(request.getPath()))
            model.setdefault("oracleEnabled", self.environment.getProperty(
                DEFAULT_DIALECT_PROPERTY, String).orElse('') == DIALECT_ORACLE)
            modelAndView.setModel(model)

        return process
