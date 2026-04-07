# API Route Map

High-level route map for `backend/server/app.py`, grouped by feature area.

## Auth

- `POST /api/auth/login` — line `267`
- `POST /api/auth/logout` — line `337`
- `GET /api/auth/me` — line `343`

## User Management (Admin)

- `GET /api/users` — line `354`
- `POST /api/users` — line `364`
- `PUT /api/users/<int:uid>/password` — line `376`
- `GET /api/admin/login-log` — line `385`

## Sections

- `GET /api/sections` — line `399`
- `GET /api/sections/<int:sid>` — line `480`
- `PUT /api/sections/<int:sid>` — line `534`
- `GET /api/sections/parishes` — line `576`

## Owners

- `GET /api/owners/states` — line `595`
- `GET /api/owners` — line `609`
- `GET /api/owners/<int:oid>` — line `699`
- `GET /api/owners/<int:oid>/associated` — line `802`
- `PUT /api/owners/<int:oid>` — line `863`
- `DELETE /api/owners/<int:oid>/phone/<int:slot>` — line `900`
- `DELETE /api/owners/<int:oid>/email/<int:slot>` — line `917`
- `GET /api/owners/<int:oid>/activities` — line `1019`
- `GET /api/owners/export` — line `1050`

## Contact Notes

- `GET /api/owners/<int:oid>/notes` — line `935`
- `POST /api/owners/<int:oid>/notes` — line `949`
- `DELETE /api/notes/<int:nid>` — line `966`

## Phone Verification

- `PUT /api/owners/<int:oid>/verify-phone` — line `983`

## Deals

- `GET /api/deals` — line `1108`
- `POST /api/deals` — line `1154`
- `GET /api/deals/<int:did>` — line `1176`
- `PUT /api/deals/<int:did>` — line `1220`
- `DELETE /api/deals/<int:did>` — line `1249`

## Activities

- `GET /api/activities` — line `1289`
- `POST /api/activities` — line `1342`

## Search

- `GET /api/search` — line `1364`

## Stats / Dashboard / Map / Lookups

- `GET /api/stats` — line `1418`
- `GET /api/dashboard` — line `1489`
- `GET /api/map/markers` — line `1545`
- `GET /api/lookups` — line `1595`

## AI Assistant

- `POST /api/assistant` — line `1764`
- `GET /api/assistant/suggestions` — line `1893`
- `POST /api/assistant/confirm` — line `1910`

## Assistant Conversation History

- `GET /api/assistant/conversations` — line `2005`
- `POST /api/assistant/conversations` — line `2020`
- `GET /api/assistant/conversations/<int:cid>` — line `2033`
- `DELETE /api/assistant/conversations/<int:cid>` — line `2049`
- `PUT /api/assistant/conversations/<int:cid>/pin` — line `2063`
- `POST /api/assistant/conversations/<int:cid>/messages` — line `2077`
