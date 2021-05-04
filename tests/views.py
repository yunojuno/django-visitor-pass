from django.http import HttpRequest, HttpResponse

from visitors.decorators import user_is_visitor


# Test view that requires a valid Visitor Pass
@user_is_visitor(scope="foo")
def foo(request: HttpRequest) -> HttpResponse:
    return HttpResponse("OK")


# Test view that supports self-service
@user_is_visitor(scope="bar", self_service=True)
def bar(request: HttpRequest) -> HttpResponse:
    return HttpResponse(f"Hello, {request.visitor.first_name}")
