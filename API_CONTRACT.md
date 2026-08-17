# Forum Platform API Contract — v1

Stage 7.2 establishes the API contract that the first Web frontend may build against.

## Base URL

```text
/api/v1/
```

The existing `v1` path is retained. Backward-incompatible changes should not silently change existing v1 payloads.

## Authentication

JWT access tokens are sent as:

```http
Authorization: Bearer <access-token>
```

Access tokens are short-lived. Refresh tokens are rotated by the refresh endpoint.

## Errors

DRF-generated failures use:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Request validation failed.",
    "status": 400,
    "fields": {}
  }
}
```

`fields` is present for validation errors. `retry_after` may be present for HTTP 429 throttling responses.

## Pagination

Timeline/list endpoints use cursor pagination where configured. Clients must follow the returned `next` / `previous` URLs instead of constructing cursor values themselves.

## Dates

Django/DRF timestamps are serialized as ISO-8601 values. Clients must treat them as timestamps, not localized display strings.

## IDs

Public API object IDs are UUIDs. Internal numeric database primary keys are not part of the API contract.

## Content

Publications and comments use structured JSON blocks. Clients should switch on the block `type` and gracefully ignore unsupported future block types where possible.

## Media

Large media bytes do not pass through Django. Clients request multipart upload authorization from the API and upload directly to the S3-compatible endpoint with presigned URLs.

## Visibility

Blocked/muted historical content is not silently deleted from thread history. Viewer-relative flags instruct clients when content should be collapsed or filtered.

## OpenAPI

```text
/api/schema/
/api/docs/
/api/redoc/
```

The OpenAPI schema is the machine-readable reference for endpoint input/output structure.
