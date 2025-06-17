# CHANGELOG

All notable changes to this project will be documented in this file.

## v1.1

* Add support for Django 5.2
* Add support for Python 3.13
* Drop support for Django versions before 4.2
* Drop support for Python 3.8 and 3.9
* Update ruff commands to use modern syntax
* Update GitHub Actions to only test Django main branch with Python 3.12 and 3.13
* Drop `black` in favor for `ruff`

## v1.0

* Add support for Django 5.0
* Add support for Python 3.11, 3.12
* Drop support for Django 3.1
* Replace isort, flake8 with ruff

## v0.7

* Add support for per-token session expiry (#9)

## v0.5

* Return `HttpReponseBadRequest` (400) on malformed UUID token, h/t @chrisapplegate, issue #7
## v0.4

* Add support for self-service tokens
## v0.2

* Add `Visitor.expires_at` timestamp to manage expiry
* Add `Visitor.is_active` switch to allow instant disabling of visitor passes
* Add `Visitor.validate()` method to validate pass
* Add `VISITOR_TOKEN_EXPIRY` setting (default: 300s)
* Add `VISITOR_SESSION_EXPIRY` settings (default: 0s - expires on browse close)
