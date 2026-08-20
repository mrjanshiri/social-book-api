# LIBA - Social Book Platform

## Overview
LIBA is a community-based book platform backend built with Django + DRF.
Users can manage personal shelves, write reviews, follow each other,
discover books, and later join book clubs.

## Core Stack
- Django + Django REST Framework
- JWT Authentication (SimpleJWT)
- PostgreSQL (added in Phase 1)
- Docker (later)

## App Structure
```
apps/
├── users/          # Auth, Profile, Permissions (is_staff/is_superuser based)
├── catalog/        # Book, Author, Publisher, Category
├── library/         # Shelves, Reading Status, Progress, Goals
├── reviews/        # Reviews & Ratings
├── social/         # Follow (Activity Feed later)
├── discovery/      # Search, Trending, Recommendations
├── community/      # Book Clubs (last phase)
├── notifications/  # Later
└── core/           # Shared permissions, pagination, utils
```

## Key Decisions
- Shelf instead of simple Wishlist (with reading status: to-read/reading/finished)
- Roles use Django's built-in `is_staff` / `is_superuser` instead of a custom
  `role` field — simpler for current scale, avoids maintaining a parallel
  permission system. Revisit Django Groups if role granularity grows.
- No Cart/Order/Payment — this project intentionally stays non-commerce
  (e-commerce depth is already covered by another portfolio project)
- Users can add books (with optional moderation)
- External book data via Open Library API (later)
- Activity Feed and Community are postponed
- Focus on clean architecture and good commit history for portfolio
