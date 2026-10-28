"""Read bundled application data through Micronaut's application environment."""

from functools import lru_cache
from typing import Annotated

from jakarta.inject import Inject, Singleton
from java.io import InputStreamReader
from java.util import Properties
from micronaut.context.env import Environment


@Singleton
class ApplicationResources:
    environment: Annotated[Environment, Inject]

    def stream(self, name: str):
        resource = self.environment.getResourceAsStream(name)
        if not resource.isPresent():
            raise ValueError('Missing application resource: ' + name)
        return resource.get()

    @lru_cache(maxsize=8)
    def text(self, name: str) -> str:
        stream = self.stream(name)
        try:
            return bytes((b & 255) for b in stream.readAllBytes()).decode('utf-8')
        finally:
            stream.close()

    @lru_cache(maxsize=3)
    def messages(self, language: str) -> dict[str, str]:
        names = ['i18n/messages.properties']
        if language in ('es', 'de'):
            names.append('i18n/messages_' + language + '.properties')
        result = {}
        for name in names:
            reader = InputStreamReader(self.stream(name), 'UTF-8')
            try:
                properties = Properties()
                properties.load(reader)
                result.update({str(key): str(properties.getProperty(key)) for key in properties.stringPropertyNames()})
            finally:
                reader.close()
        return result
