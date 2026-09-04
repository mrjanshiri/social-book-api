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
- [x] `apps/catalog`: no major changes expected, verify after app split
  - Found and fixed a lot more than expected during verification:
    - `most_reviewed`: `[:10]` was slicing the `Response` object instead of the queryset
      (silently caused a 500 on every call — `Response` doesn't support slicing the
      normal way, since `__getitem__` is overridden for HTTP headers)
    - `average_rating` wasn't recalculated on review deletion (only on save) — added
      `Review.delete()` override, symmetric to the existing `save()` override
      (note: only covers `instance.delete()`, not bulk `queryset.delete()` — fine for
      now since there's no bulk-delete endpoint)
    - `BookSerializer.update()`: couldn't clear `categories` via `category_ids: []`
      (falsy-list bug — fixed by checking `'categories' in validated_data` before
      `pop()`, not the popped value's truthiness)
    - Added ISBN validation/normalization (`apps/catalog/utils.py::normalize_isbn`):
      accepts ISBN-10 or ISBN-13, with/without hyphens, validates checksum, always
      stores a normalized ISBN-13 — needed because Marjan plans to pull books from an
      external books API later
    - `Book.author` FK changed `on_delete` from `CASCADE` to `PROTECT` (deleting an
      author with books no longer cascades into deleting those books/reviews/wishlist
      items)
    - `most_wishlisted` / `top_rated` had no result limit (returned every book) —
      capped at 10, consistent with `most_reviewed`
    - `publisher_id` is now optional/nullable in `BookSerializer` (model already
      allowed `null=True`, serializer didn't) — also fixed `create()` (was a bare
      `pop('publisher')`, KeyError if omitted) and `update()` (same falsy-check bug
      as categories: `publisher_id: null` couldn't actually clear the publisher)
    - `BookFilter.Meta.fields` contained non-model field names (`published_after`,
      `published_before`, `min_average_rating`, `max_average_rating`) — this crashed
      `makemigrations`/`migrate`/`runserver` entirely on the current django-filter
      version. Explicitly declared filters don't need to be repeated in `Meta.fields`.
    - `categories` filter was comparing a Category **pk** against the `name` field
      with `icontains` (`field_name='categories__name'` + `ModelMultipleChoiceFilter`,
      which passes pks) — never matched anything real. Fixed to
      `field_name='categories'`, `lookup_expr='exact'`.
    - `AuthorViewSet`/`PublisherViewSet`/`CategoryViewSet`'s `list_books`/`list_book`:
      `except Author.DoesNotExist` was dead code (`get_object()` raises `Http404`,
      not `Model.DoesNotExist`), so `Http404` (and `PermissionDenied`) fell through to
      `except Exception` and returned **500 instead of 404/403**, leaking internal
      Python error text. Removed the try/except entirely — `get_object()` already
      handles 404/403 correctly on its own.
    - Removed unused imports: `MinValueValidator`/`MaxValueValidator`/`Account` in
      `models.py`, `render`/`Avg`/`get_object_or_404` in `views.py` — all leftovers
      from before `Review`/`Wishlist` were extracted into their own apps
- [x] Remove leftover `print()` statements, replace with logging where needed
  (none left anywhere in the project as of today — mostly found in `apps/catalog`)
- [ ] `apps/library`: rename Wishlist → Shelf (add reading status: to-read / reading / finished)
  - ⚠️ After this rename, MUST go back and fix `apps/catalog/views.py`'s
    `most_wishlisted` action — it does `Count('wishlistitems')`, which is the
    current `related_name` on `Book` from `WishlistItem.book`. Once the model/
    related_name changes (e.g. to `Shelf`/`shelf_items` or similar), this
    `Count(...)` call will break with a `FieldError` (same class of bug as the
    `published_after` one we already hit). Don't forget this — it's an easy
    one to miss since it lives in a different app.
- [ ] Add `drf-spectacular` for API docs
- [ ] Write basic tests for users + catalog + reviews

## Phase 2.5 — User Book Contributions (not started, design only so far)
- [ ] Regular (non-staff) users should be able to add a book by ISBN only —
  fetch the rest (title, author, publisher, ...) from an external books API
  (Google Books / OpenLibrary, TBD). Admin/staff keep the existing full-form
  `POST /books/` as-is; this is a *separate*, additional endpoint for regular
  users, not a replacement.
- [ ] Regular users should be able to fix an ISBN typo on a book *they added*
  (needs a `Book.added_by` FK — decided 1-ب: ownership-based, only the
  original adder can edit/isbn-correct their own book; staff/superuser can
  always edit any book; delete stays staff/superuser-only, even for the
  adder)
- [ ] Until the ISBN-lookup endpoint exists, regular users attempting
  `POST /books/` should get an informative "coming soon" message rather than
  a bare permission-denied

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