# Todo — LIBA

## Phase 0 — Project Hygiene (current)
- [ ] Restructure project into `apps/` layout:
  - `account` → `apps/users/`
  - `library_managment` → split into `apps/catalog/` (Book, Author, Publisher, Category) + `apps/reviews/` (Review) + `apps/library/` (Wishlist → Shelf)
  - Create empty `apps/core/` for shared permissions, pagination, utils
- [ ] Move SECRET_KEY, DEBUG, DB creds to `.env` (django-environ or python-decouple)
- [ ] Split settings: `library/settings/base.py`, `dev.py`, `prod.py`
- [ ] Add `.gitignore` (db.sqlite3, media/, __pycache__, .env, *.pyc)
- [ ] Add `requirements.txt`
- [ ] First clean commit

## Phase 1 — Database Migration
- [ ] Add PostgreSQL (psycopg2-binary), update DATABASES in prod/dev settings
- [ ] Verify all migrations run clean on Postgres
- [ ] (Optional) Docker Compose for local Postgres

## Phase 2 — Core Domain Cleanup
- [ ] `apps/users`: replace custom `role` field with `is_staff` / `is_superuser`
  - Keep custom logic: prevent deleting/demoting last superuser
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
