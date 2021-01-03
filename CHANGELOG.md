# CHANGELOG

All notable changes to this project will be documented in this file.

## v0.2

* Add `Visitor.expires_at` timestamp to manage expiry
* Add `Visitor.is_active` switch to allow instant disabling of visitor passes
* Add `Visitor.validate()` method to validate pass 
* Add `VISITOR_TOKEN_EXPIRY` setting (default: 300s)
* Add `VISITOR_SESSION_EXPIRY` settings (default: 0s - expires on browse close)
