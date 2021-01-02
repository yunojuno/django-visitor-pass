# Django Visitor Pass

Django app for managing temporary session-based users.

### Background

This package has been extracted out of `django-request-token` as a specific use
case - that of temporary site "visitors". It enables a type of ephemeral user
who is neither anonymous nor authenticated, but somewhere in between - known for
the duration of their session.

### Motivation

We've been using `django-request-token` for a while, and have issued over
100,000 tokens. A recent analysis showed two main use cases - single-use "magic
links" for logging people in, and a more involved case where we invite
unregistered users on to the platform to perform some action - providing a
reference perhaps, or collaborating on something with (registered) users. The
former we have extracted out into `django-magic-links` - and this package
addresses the latter.

### What is a "visitor"?

In the standard Django model you have the concept of an `AnonymousUser`, and an
authenticated `User` - someone who has logged in. We have a third, intermediate,
type of user - which we have historically referred to as a "Temp User", which is
someone we know _of_, but who has not yet registered.

The canonical example of this is leaving a reference: user A on the site invites
user B to leave a reference for them. They (A) give us B's name and email, we
invite them to click on a link and fill out a form. That's it. We store their
name and email so that we can contact them, but it's ephemeral - we don't need
it, and we don't use it. Storing this data in the User table made sense (as it
has name and email fields), but it led to a lot of `user_type=TEMP` munging to
determine who is a 'real' user on the site.

What we really want is to 'stash' this information somewhere outside of the auth
system, and to enable these temp users to have restricted access to specific
areas of the application, for a limited period, after which we can forget about
them and clear out the data.

We call these users "visitors".

### Use Case - request a reference

Fred is a registered user on the site, and would like a reference from Ginger,
his dance partner.

1. Fred fills out the reference request form:

```
   Name: Ginger
   Email: ginger@[...].com
   Message: ...
   Scope: REFERENCE_REQUEST [hidden field]
```

2. We save this information, and generate a unique link which we send to Ginger,
   along with the message.

3. Ginger clicks on the link, at which point we recognise that this is someone
   we know about - a "visitor" - but who is in all other respects an
   `AnonymousUser`.

4. We stash the visitor info in the standard session object - so that even
   though Ginger is not authenticated, we know who she is, and more importantly
   we know why she's here (REFERENCE_REQUEST).

5. Ginger submits the reference - which may be a multi-step process, involving
   GETs and POSTs, all of which are guarded by a decorator that restricts access
   to visitors with the appropriate Scope (just like `django-request-token`).

6. At the final step we can (optionally) choose to clear the session info
   immediately, effectively removing all further access.

### Implementation

This code has been extracted out of `django-request-token` and simplified. It
stores the visitor data in the `Visitor` model, and on each successful first
request (where the token is 'processed' and the session filled) we record a
`VisitorLog` record. This includes HTTP request info (session_key, referer,
client IP, user-agent). This information is for analytics only - for instance
determining whether links are being shared.

The app works by adding some attributes to the `request` and `request.user`
objects. The user has a boolean `user.is_visitor` property, and the request has
a `request.visitor` property which is the relevant `Visitor` object.

This is done via two bits of middleware, `VisitorRequestMiddleware` and
`VisitSessionMiddleware`. 

#### `VisitorRequestMiddleware`

This middleware looks for a visitor token (uuid) on the incoming request
querystring. If it finds a token, it will look up the `Visitor` object, add it
to the request, and then set the `request.user.is_visitor` attribute. It sets
the properties from the request, and has no interaction with the session. This
happens in the second piece of middleware.

#### `VisitorSessionMiddleware`

This middleware must come after the `VisitorRequestMiddleware` (it will blow up
if it can't access `request.visitor`). It has two responsibilities:

1. If the request object has a visitor object on it, then it _must_ have been
   set by the request middleware on the current request - so it's a new visitor,
   and we immediately stash it in the `request.session`. 

1. If `request.visitor` is None, then we don't have a _new_ visitor, but there
   may be one already stashed in the `request.session`, in which case we want to
   add it on the to the request.

Note: splitting this in two seems over-complicated, but because we are moving
values from request-into-session-into-request it's a lot simpler to run two
completely separate passes.

### Configuration

#### Django Settings

1. Add `visitors` to `INSTALLED_APPS`
1. Add `visitors.middleware.VisitorRequestMiddleware` to `MIDDLEWARE`
1. Add `visitors.middleware.VisitorSessionMiddleware` to `MIDDLEWARE`

#### Environment Settings

* `VISITOR_SESSION_KEY`: session key used to stash visitor info (defaut:
  `visitor:session`)

* `VISITOR_QUERYSTRING_KEY`: querystring param used on tokenised links (default:
  `vuid`)

### Usage

Once you have the package configured, you can use the `user_is_visitor`
decorator to protect views that you want to restricted to visitors only. The
decorator requires a `scope` kwarg, which must match the `Visitor.scope` value
set when the `Visitor` object is created.

```python
@user_is_visitor(scope="foo")
def protected_view(request):
   pass
```

By default the decorator will allow visitors with the correct scope only. If you
want more control over the access, you can pass a callable as the `bypass_func`
param:

```python
# allow authenticated users as well as visitors
@user_is_visitor(scope="foo", bypass_func=lambda r: r.user.is_staff)
def allow_visitors_and_staff(request):
   pass
```

If you don't care about the scope (you should), you can use `"*"` to allow all
visitors access:

```python
@user_is_visitor(scope="*")  # see also SCOPE_ANY
def allow_all_scopes(request):
   pass
```

Alternatively, for more complex use cases, you can ignore the decorator and just
inspect the request itself:

```python
def complicated_rules(request):
   if request.user.is_visitor:
      pass
   elif is_national_holiday():
      pass
   elif is_sunny_day():
      pass
   else:
      raise PermissionDenied
```
