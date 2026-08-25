# Todo — LIBA

## Phase 0 — Project Hygiene (current)
- [x] Create venv, install packages, generate `requirements.txt`
- [x] Move SECRET_KEY, DEBUG to `.env` (python-decouple) + `.env.example`
- [x] Add `.gitignore` (venv/, db.sqlite3, media/, __pycache__, .env, *.pyc)
- [x] Rename project package `library` → `backend` (fix DJANGO_SETTINGS_MODULE, ROOT_URLCONF, WSGI_APPLICATION references)
- [x] Create GitHub repo (`social-book-api`), first commit pushed
- [x] Restructure `account` → `apps/users/` (fixed AUTH_USER_MODEL, apps.py name,
      internal serializer import, migration dependency references, reset local db.sqlite3)
- [x] Move `library_managment` → `apps/catalog` as a whole (fixed apps.py name,
      INSTALLED_APPS, urls.py, migration app_label references in dependencies and
      FK `to=`, reset local db.sqlite3, applied migrations)
- [x] Extract `Review` model + serializer + view + url out of `apps/catalog` into `apps/reviews`
      (kept nested `/books/<id>/reviews/` action in BookViewSet as-is — decided not to
      change API behavior during structural refactor; catalog imports Review/serializers
      from apps.reviews where needed)
- [x] Extract `WishlistItem` model + serializer + view + url out of `apps/catalog` into `apps/library`
      (kept model/field names as-is — rename to `Shelf` deferred to Phase 2)
- [x] Scaffold `apps/core` (plain Python package, no models — not in INSTALLED_APPS,
      just `permissions.py` + `pagination.py` placeholders for now)
- [x] Split settings: `backend/settings/base.py`, `dev.py`, `prod.py`
      (DJANGO_SETTINGS_MODULE controlled via `.env`, read in manage.py/wsgi.py/asgi.py)

## Revisit Later (noted during Phase 0, not urgent)
- `ReviewViewSet.get_queryset` and `WhishListItemViewSet.get_queryset` duplicate the same
  "if not staff, filter by user" pattern — candidate for a shared mixin/base class in
  `apps/core` once that app exists (marjan flagged dissatisfaction with current form,
  revisit after all apps are split)
- `apps/core` was just an empty scaffold in Phase 0. The `role` → `is_staff`/`is_superuser`
  refactor (Phase 2) is now done, and as part of it:
  - [x] `IsSuperAdminOrAdmin` (now `IsAdminOrSelfReadOnly`) moved to `apps/core/permissions.py`,
    rewritten to use `is_staff`/`is_superuser` instead of `role`
  - [ ] Still open: shared base queryset/mixin for the repeated "staff sees all, user sees
    own" pattern (see item above) — not done yet
  - `apps/core/pagination.py` stays a placeholder until a concrete need for custom
    pagination (beyond DRF's global `PageNumberPagination` default) comes up — no
    speculative pagination classes before then.

## Phase 1 — Database Migration
- [ ] Add PostgreSQL (psycopg2-binary), update DATABASES in prod/dev settings
- [ ] Verify all migrations run clean on Postgres
- [ ] (Optional) Docker Compose for local Postgres

## Phase 2 — Core Domain Cleanup
- [x] `apps/users`: replace custom `role` field with `is_staff` / `is_superuser`
  - Kept custom logic: prevent deleting/demoting last superuser (`would_remove_last_superuser`,
    now re-locks the target row too, not just the superuser count, to avoid a stale-read race)
  - Also fixed while in there: `UserViewSet` no longer allows creating users via `POST`
    (signup stays exclusive to `SignupView`); admin-to-admin actions restricted to
    superusers only; `is_superuser` is now read from validated serializer data instead
    of raw `request.data` (was vulnerable to `bool("false") == True`); `ProfileSerializer`
    hides `id` and makes `username` read-only; dropped redundant `null=True` on
    `first_name`/`last_name`
  - Renamed `IsSuperAdminOrAdmin` → `IsAdminOrSelfReadOnly` (apps/core/permissions.py) to
    actually describe its behavior; updated in apps/catalog too
- [ ] `apps/catalog`: no major changes expected, verify after app split
- [ ] `apps/reviews`: fix `most_reviewed` bug (slicing Response instead of queryset)
- [ ] `apps/library`: rename Wishlist → Shelf (add reading status: to-read / reading / finished)
- [ ] Remove leftover `print()` statements, replace with logging where needed
- [ ] Add `drf-spectacular` for API docs
- [ ] Write basic tests for users + catalog + reviews

## Phase 3 — Social Features
- [ ] `apps/social`: Follow / Follower model + endpoints
- [ ] Comments on Reviews
- [ ] Likes on Reviews
- [ ] (Activity Feed — postponed per Agent.md)

## Later / Not Now
- Discovery (search, trending, recommendations)
- Community (book clubs)
- Notifications
- Activity Feed
- Docker for deployment

---
*Update this file after each significant change. Keep completed items checked, don't delete history — move finished phases to a "Done" section if the file gets long.*