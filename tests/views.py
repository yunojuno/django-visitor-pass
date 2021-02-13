from django.http import HttpRequest, HttpResponse

from visitors.decorators import user_is_visitor


@user_is_visitor(scope="foo")
def foo(request: HttpRequest) -> HttpResponse:
    return HttpResponse("OK")
