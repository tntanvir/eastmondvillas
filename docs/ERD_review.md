## ERD Review — Eastmond Villas

Date: 2025-11-07

Summary
-------
I reviewed your repository files (`accounts/models.py`, `accounts/serializers.py`, `accounts/views.py`, `eastmondvilla/settings.py`) and the feature/workflow documents you provided. You also attached an ERD image showing the domain for villas, bookings, calendar events, images, views, downloads, and booking rates.

What's implemented now
----------------------
- A custom `User` model (`accounts.models.User`) with fields: `email`, `name`, `role`, `permission`, `phone`, `address`, `date_joined`, `is_verified`, `is_active`, `is_staff`.
- Authentication/registration serializers are customized (`accounts/serializers.py`).
- Basic project settings are configured for Django, REST framework, JWT, and AllAuth (but Google social provider is commented out in `INSTALLED_APPS`).

What's missing (compared to your ERD image and needed booking features)
-------------------------------------------------------------------
The project is missing most domain models required for villa bookings and calendar + maps integration. Specifically:

- Villa/property models: `Villa` (or `villas`) with fields shown in ERD (title, description, price, bedrooms, bathrooms, pool, city, location/address, villa_name, signature_distinctions, amenities, rules, status, staff/owner reference).
- Image model: `VillaImage` or generic `Image` table referencing `Villa` with fields for primary image and ordering.
- Booking model: `Booking` (or `Book`) with guest info, check_in/check_out, status (Pending/Approved/Rejected/Completed/Cancelled), total_price, link to `villa`, link to `user` (if logged-in), and optional `google_event_id`.
- BookingRate model: rates per period (per night/week/month), minimum stay and references to villas.
- Calendar / Google mapping: `CalendarEvent` or `CalendarSync` model storing google_event_id, booking_id, start_time, end_time, meeting_link, tokens if you store per-user calendar tokens.
- Views & Downloads counters/tables (optional) to collect metrics and fulfill the ERD boxes `views`, `downloads`.
- Payment model: `Payment` to store payment status, provider, amount, and link to booking.
- Location fields for Google Maps: `latitude`, `longitude`, `address`, optional `place_id` on the `Villa` model.

Important non-model items to add
--------------------------------
- Google OAuth / Calendar: environment variables for client ID and secret, an OAuth flow endpoint, token storage (per-user or per-account), scopes (calendar.events), and a service to create/update/delete calendar events.
- Google Maps: API key in env vars and frontend JS integration (Maps, geocoding). Server-side support for searches (Haversine or PostGIS) and indexing.
- Booking validation: overlap checks (no double bookings), timezone-aware date handling, and booking statuses.

Suggested next step (small, actionable)
-------------------------------------
1. Implement `Villa` and `VillaImage` models and a `Booking` model with minimal fields to support booking creation and availability checks. Add `latitude`, `longitude`, and `address` to `Villa` now for Google Maps.
2. Create migrations and a small API endpoint to create/read villas (DRF viewset + serializer). This will let you add test data and visually confirm the ERD mapping.

Proposed minimal fields (copy/paste ready)
----------------------------------------
- Villa
  - id (PK)
  - owner (FK -> `accounts.User`)
  - title, description, price (decimal)
  - bedrooms (int), bathrooms (int), pool (bool)
  - city, address (text)
  - latitude (decimal), longitude (decimal), place_id (nullable)
  - status (choice: Draft/Pending/Published/Archived)

- VillaImage
  - id (PK), villa (FK), file (ImageField), caption, is_primary (bool), order (int)

- Booking
  - id (PK), villa (FK), user (FK nullable), full_name, email, phone
  - check_in (date), check_out (date)
  - status (choice: Pending/Approved/Rejected/Completed/Cancelled)
  - total_price (decimal), created_at (datetime)
  - google_event_id (nullable)

Files added in this change
-------------------------
- `docs/ERD.mmd` — Mermaid diagram of the suggested schema.
- `docs/ERD.puml` — PlantUML version for editors that support PlantUML.
- `docs/ERD_review.md` — this analysis and recommended next steps.

Next actions I can take (pick one)
----------------------------------
1. Implement models + migrations for `Villa`, `VillaImage`, and `Booking` (MVP). I will also add serializers and a simple DRF viewset for `Villa` so you can create listings from Postman or the admin.
2. Implement Google Maps integration (add fields + sample map widget in template or React stub) next.
3. Implement Google Calendar integration scaffolding (settings + model for storing tokens and calendar events) next.

Which would you like me to start with? My recommendation: implement the `Villa` + `Booking` models first so we have a concrete schema and can create bookings and then wire Google Calendar and Maps.

If you approve, I'll implement the `Villa`, `VillaImage`, and `Booking` models next and run migrations locally. I will keep changes small and add unit tests for booking overlap validation.
