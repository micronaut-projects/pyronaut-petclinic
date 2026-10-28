"""Locale HTTP routes and helpers."""

from typing import Annotated

from java.time import Duration
from micronaut.http import HttpRequest
from micronaut.http.annotation import Get, QueryValue
from micronaut.http.cookie import Cookie
from petclinic.controllers.support import redirect_to


@Get("/locale")
def locale(request: HttpRequest, lang: Annotated[str, QueryValue(defaultValue="en")] = "en",
           backUrl: Annotated[str, QueryValue(defaultValue="")] = ""):
    language = lang.lower() if lang.lower() in ("en", "es", "de") else "en"
    target = backUrl if backUrl and backUrl.strip() else request.getHeaders().get("Referer") or "/"
    if not target.startswith("/") or target.startswith("//") or "/locale" in target:
        target = "/"
    cookie = Cookie.of("locale", language).maxAge(Duration.ofDays(365)).path("/").httpOnly(True)
    return redirect_to(target).cookie(cookie)
