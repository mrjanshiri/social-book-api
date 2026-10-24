# Todo — LIBA

## Phase 0 — Project Hygiene (done)
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
      (Superseded in Phase 2: the nested action was removed, see `apps/reviews` below.)
- [x] Extract `WishlistItem` model + serializer + view + url out of `apps/catalog` into `apps/library`
      (kept model/field names as-is — rename to `Shelf` deferred to Phase 2)
- [x] Scaffold `apps/core` (plain Python package, no models — not in INSTALLED_APPS,
      just `permissions.py` + `pagination.py` placeholders for now)
- [x] Split settings: `backend/settings/base.py`, `dev.py`, `prod.py`
      (DJANGO_SETTINGS_MODULE controlled via `.env`, read in manage.py/wsgi.py/asgi.py)

## Revisit Later (noted during Phase 0, not urgent)
- `ReviewViewSet` no longer filters by user: reviews are public-read now (see Phase 2
  `apps/reviews`). Neither reviews nor shelf use the old "staff sees all, user sees own"
  pattern, so a shared mixin has nothing to share. Leave `apps/core` alone until a
  *new* app repeats that pattern.
- `apps/core` was just an empty scaffold in Phase 0. The `role` → `is_staff`/`is_superuser`
  refactor (Phase 2) is now done, and as part of it:
  - [x] `IsSuperAdminOrAdmin` (now `IsAdminOrSelfReadOnly`) moved to `apps/core/permissions.py`,
    rewritten to use `is_staff`/`is_superuser` instead of `role`
  - [x] Shared staff/self queryset mixin — dropped. Shelf does not use that pattern, and
    forcing one mixin across apps would hide different rules. Reopen only if a second app
    copies the same queryset.
  - `apps/core/pagination.py` stays a placeholder until a concrete need for custom
    pagination (beyond DRF's global `PageNumberPagination` default) comes up — no
    speculative pagination classes before then.
- `BookSerializer` embeds every review of every book in `GET /books/` (unbounded). Replace
  with `reviews_count`; full reviews stay on `GET /reviews/?book=<id>`. Then
  `reviews__user` in `BOOK_QUERYSET` is no longer needed.
- `Book.update_average_rating` loads all reviews in Python and does a full `save()`.
  `aggregate(Avg('rating'))` + `save(update_fields=['average_rating'])` would be cheaper.
  Low priority.

## Phase 1 — Database Migration
- [ ] Add PostgreSQL (psycopg2-binary), update DATABASES in prod/dev settings
- [ ] Verify all migrations run clean on Postgres
- [ ] (Optional) Docker Compose for local Postgres

## Phase 2 — Core Domain Cleanup (current — tests and API docs left)
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
      Superseded by signals, see `apps/reviews` below (also covers cascade deletes).
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
- [x] `apps/library`: rename Wishlist → Shelf (reading status: to-read / reading / finished)
  Done across Sep 4–13. Model is `Shelf` (`migrations/0002_shelf_delete_wishlistitem` onward).
  Also landed with it, not a separate Todo item:
  - `status` + `finished_at` (set/cleared in `save()`), `is_private` (default public)
  - reads: guests can see a public shelf via `?user=<id>`; `GET /shelf/` with no user
    and no login returns 400 with a hint; invalid `user` / `status` query params return 400
  - writes: only the owner (not staff, not superuser). PUT disabled. `book_id` cannot
    be changed after create. duplicate `(user, book)` returns 400, including the
    concurrent `IntegrityError` path
  - response exposes nested `book.id` and numeric `user` id; `note` is hidden from
    anyone who is not the owner (fail-closed if request context is missing)
  - lookup is `book_id`. Another user's public item is `GET /shelf/<book_id>/?user=<owner_id>`
  - `Book` delete is `PROTECT` when the book is on a shelf; API returns a clean error
    instead of a 500. `note` is `blank=True` without `null=True`
  - catalog `most_wishlisted` counts `shelf_items`, not the old wishlist related name
- [x] `apps/reviews`: one review API, correct average rating
  - `POST /reviews/` always returned 500 (`user`/`book` were read-only and nothing
    supplied them). `/reviews/` is now the only review route; the nested
    `/books/<id>/reviews/` action and `ReviewCreateSerializer` are gone.
    Reviews of a book: `GET /reviews/?book=<id>`; a user's reviews: `?user=<id>`.
  - reads: public, guests included. writes: any logged-in user creates with `book_id`;
    only the owner edits; the owner or staff can delete (moderation only, staff cannot
    edit someone else's words). PUT disabled. `book_id` cannot change after create.
    duplicate `(book, user)` returns 400, including the concurrent `IntegrityError` path.
    response exposes `user_id` and `book_id`.
  - `unique_together` replaced by `UniqueConstraint`; `Meta.ordering` added
    (stable pagination); `select_related('user', 'book')` on the viewset.
  - `Book.average_rating` is now refreshed by `post_save`/`post_delete` signals in
    `apps/reviews/signals.py` (calling the existing `Book.update_average_rating`, so the
    calculation still lives in catalog). Needed because deleting a user cascades reviews
    away without calling `Review.delete()`. This is the only use of signals in the project.
    Caveat: `QuerySet.update()`, `bulk_create()` and `bulk_update()` on `Review` do not
    fire them.
  - Also fixed in `apps/catalog/views.py` along the way: `most_reviewed` restored,
    duplicate `most_wishlisted` (old `wishlistitems` copy won) removed,
    `BOOK_QUERYSET` prefetches `reviews__user` (N+1).
  - [ ] Record the signals exception in `Project_info.md`.
- [x] `apps/users`: a superuser must imply staff. `UserSerializer.validate` now forces
  `is_staff=True` whenever the resulting account is a superuser, so the inconsistent
  combination can no longer be created through the API.
  (Existing accounts were repaired once with
  `Account.objects.filter(is_superuser=True, is_staff=False).update(is_staff=True)`.)
- [ ] Add `drf-spectacular` for API docs
- [ ] Write basic tests for users + catalog + reviews + library
  (all four `tests.py` files are still the Django stub. Do library first — it has
  the most rules and zero coverage. For reviews cover: duplicate review, owner-only edit,
  and that deleting a user resets the book's `average_rating`.)

## Phase 2.5 — User Book Contributions (design only; the "coming soon" message is the only piece built)
- [ ] Regular (non-staff) users should be able to add a book by ISBN only —
  fetch the rest (title, author, publisher, ...) from an external books API
  (Google Books / OpenLibrary, TBD). Admin/staff keep the existing full-form
  `POST /books/` as-is; this is a *separate*, additional endpoint for regular
  users, not a replacement.
- [ ] Regular users should be able to fix an ISBN typo on a book *they added*
  (`Book.added_by` already exists and is read-only on the serializer — decided
  1-ب: only the original adder can edit their own book; staff/superuser can
  always edit any book; delete stays staff/superuser-only, even for the adder.
  The ISBN-correction flow itself is not built.)
- [x] Until the ISBN-lookup endpoint exists, regular users attempting
  `POST /books/` get an informative message
  (`IsBookOwnerOrAdminOrReadOnly`: "Adding books by regular users will be
  enabled soon via ISBN lookup.") rather than a bare permission-denied
- [ ] `apps/library`: new endpoint to see who has a given book on their shelf
  (book-centric, not user-centric — the inverse of current `/shelf/` endpoints).
  Needs its own permission/serializer; must only surface users with
  `is_private=False` for that book, never leak private shelf entries.

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