from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.catalog.models import Author, Book
from apps.library.models import Shelf
from apps.reviews.models import Review

User = get_user_model()

# Assumes backend/urls.py mounts apps.users.urls under api/auth/ (same as the other test files).
LIST_URL = '/api/auth/users/'
PASSWORD = 'Orig-pass-1!'
USER_FIELDS = {'id', 'username', 'email', 'is_staff', 'is_superuser'}


def detail_url(user):
    return f'{LIST_URL}{user.pk}/'


def make_user(username, email, **extra):
    return User.objects.create_user(
        username=username, email=email, password=PASSWORD, **extra
    )


def make_staff(username, email):
    return make_user(username, email, is_staff=True)


def make_superuser(username, email):
    return User.objects.create_superuser(
        username=username, email=email, password=PASSWORD
    )


def make_book():
    author = Author.objects.create(name='Some Author')
    return Book.objects.create(
        title='Some Book',
        author=author,
        publication_date='2020-01-01',
        isbn='9780306406157',
        pages=100,
    )


class UserAdminTestCase(APITestCase):
    """Two regular users, two staff accounts and exactly one superuser."""

    def setUp(self):
        self.regular = make_user('regular_01', 'regular@example.com')
        self.other = make_user('other_02', 'other@example.com')
        self.staff = make_staff('staff_01', 'staff@example.com')
        self.staff2 = make_staff('staff_02', 'staff2@example.com')
        self.superuser = make_superuser('super_01', 'super@example.com')

    def login(self, user):
        self.client.force_authenticate(user=user)

    def patch_user(self, target, payload, fmt='json'):
        return self.client.patch(detail_url(target), payload, format=fmt)

    def flags(self, user):
        """(is_staff, is_superuser) as currently stored in the database."""
        user.refresh_from_db()
        return user.is_staff, user.is_superuser


class AnonymousAccessTests(UserAdminTestCase):
    def test_every_endpoint_requires_login(self):
        url = detail_url(self.regular)
        responses = {
            'list': self.client.get(LIST_URL),
            'detail': self.client.get(url),
            'patch': self.client.patch(url, {'email': 'x@example.com'}, format='json'),
            'delete': self.client.delete(url),
        }

        for name, response in responses.items():
            with self.subTest(endpoint=name):
                self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(User.objects.filter(pk=self.regular.pk).exists())


class VisibilityTests(UserAdminTestCase):
    def all_listed_ids(self):
        """Follow the pagination links and collect every id in order."""
        ids = []
        url = LIST_URL
        while url:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            ids.extend(item['id'] for item in response.data['results'])
            url = response.data['next']
        return ids

    def test_regular_user_lists_only_themselves(self):
        self.login(self.regular)

        response = self.client.get(LIST_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.regular.pk)

    def test_regular_user_can_open_their_own_account(self):
        self.login(self.regular)

        response = self.client.get(detail_url(self.regular))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'regular_01')

    def test_regular_user_gets_404_for_other_accounts(self):
        self.login(self.regular)

        for target in (self.other, self.staff, self.superuser):
            with self.subTest(target=target.username):
                response = self.client.get(detail_url(target))

                self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_staff_and_superuser_list_everyone(self):
        for viewer in (self.staff, self.superuser):
            with self.subTest(viewer=viewer.username):
                self.login(viewer)

                response = self.client.get(LIST_URL)

                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(response.data['count'], User.objects.count())

    def test_staff_can_open_any_account(self):
        self.login(self.staff)

        for target in (self.regular, self.staff2, self.superuser):
            with self.subTest(target=target.username):
                response = self.client.get(detail_url(target))

                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(response.data['id'], target.pk)

    def test_only_safe_fields_are_exposed(self):
        self.login(self.superuser)

        detail = self.client.get(detail_url(self.regular))
        listing = self.client.get(LIST_URL)

        self.assertEqual(set(detail.data), USER_FIELDS)
        for item in listing.data['results']:
            self.assertEqual(set(item), USER_FIELDS)

    def test_list_is_ordered_by_id_across_pages(self):
        for i in range(8):
            make_user(f'extra_{i:02d}', f'extra{i}@example.com')
        self.login(self.staff)

        ids = self.all_listed_ids()

        self.assertEqual(len(ids), User.objects.count())
        self.assertEqual(len(set(ids)), len(ids))  # no id repeated between pages
        self.assertEqual(ids, sorted(ids))


class MethodTests(UserAdminTestCase):
    def test_post_is_not_allowed(self):
        self.login(self.superuser)
        before = User.objects.count()
        payload = {'username': 'new_user', 'password': PASSWORD, 'email': 'new@example.com'}

        response = self.client.post(LIST_URL, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(User.objects.count(), before)

    def test_put_is_not_allowed(self):
        self.login(self.superuser)

        response = self.client.put(
            detail_url(self.regular), {'email': 'new@example.com'}, format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.regular.refresh_from_db()
        self.assertEqual(self.regular.email, 'regular@example.com')


class RegularUserWriteTests(UserAdminTestCase):
    def test_regular_user_cannot_edit_or_delete_anyone(self):
        self.login(self.regular)

        for target in (self.regular, self.other):
            with self.subTest(target=target.username):
                original_email = target.email

                patched = self.patch_user(target, {'email': 'changed@example.com'})
                deleted = self.client.delete(detail_url(target))

                self.assertEqual(patched.status_code, status.HTTP_403_FORBIDDEN)
                self.assertEqual(deleted.status_code, status.HTTP_403_FORBIDDEN)
                target.refresh_from_db()
                self.assertEqual(target.email, original_email)


class StaffWriteTests(UserAdminTestCase):
    def setUp(self):
        super().setUp()
        self.login(self.staff)

    def test_can_edit_a_regular_user(self):
        response = self.patch_user(self.regular, {'email': 'new@example.com'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.regular.refresh_from_db()
        self.assertEqual(self.regular.email, 'new@example.com')

    def test_can_edit_themselves(self):
        response = self.patch_user(self.staff, {'email': 'newstaff@example.com'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.staff.refresh_from_db()
        self.assertEqual(self.staff.email, 'newstaff@example.com')

    def test_can_delete_a_regular_user(self):
        response = self.client.delete(detail_url(self.regular))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(pk=self.regular.pk).exists())

    def test_cannot_edit_or_delete_other_staff_or_superusers(self):
        for target in (self.staff2, self.superuser):
            with self.subTest(target=target.username):
                original_email = target.email

                patched = self.patch_user(target, {'email': 'changed@example.com'})
                deleted = self.client.delete(detail_url(target))

                self.assertEqual(patched.status_code, status.HTTP_403_FORBIDDEN)
                self.assertEqual(deleted.status_code, status.HTTP_403_FORBIDDEN)
                target.refresh_from_db()
                self.assertEqual(target.email, original_email)

    def test_cannot_change_staff_or_superuser_flags(self):
        # On a regular user and on themselves.
        for target in (self.regular, self.staff):
            before = self.flags(target)
            for payload in ({'is_staff': True}, {'is_superuser': True}):
                with self.subTest(target=target.username, payload=payload):
                    response = self.patch_user(target, payload)

                    self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                    self.assertIn(next(iter(payload)), response.data)
                    self.assertEqual(self.flags(target), before)


class SuperuserWriteTests(UserAdminTestCase):
    def setUp(self):
        super().setUp()
        self.login(self.superuser)

    def test_can_edit_staff_and_regular_users(self):
        for target in (self.staff2, self.regular):
            with self.subTest(target=target.username):
                new_email = f'changed_{target.pk}@example.com'

                response = self.patch_user(target, {'email': new_email})

                self.assertEqual(response.status_code, status.HTTP_200_OK)
                target.refresh_from_db()
                self.assertEqual(target.email, new_email)

    def test_can_delete_a_staff_account(self):
        response = self.client.delete(detail_url(self.staff2))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(pk=self.staff2.pk).exists())


class EmailAndUsernameTests(UserAdminTestCase):
    def setUp(self):
        super().setUp()
        self.login(self.staff)

    def test_username_is_ignored(self):
        response = self.patch_user(self.regular, {'username': 'new_name'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'regular_01')
        self.regular.refresh_from_db()
        self.assertEqual(self.regular.username, 'regular_01')

    def test_invalid_email_is_rejected(self):
        for email in ('not-an-email', 'alice@', '@example.com', ''):
            with self.subTest(email=email):
                response = self.patch_user(self.regular, {'email': email})

                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn('email', response.data)

    def test_email_of_another_user_is_rejected_ignoring_case(self):
        for email in ('other@example.com', 'Other@Example.com', 'OTHER@EXAMPLE.COM'):
            with self.subTest(email=email):
                response = self.patch_user(self.regular, {'email': email})

                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn('email', response.data)
                self.regular.refresh_from_db()
                self.assertEqual(self.regular.email, 'regular@example.com')

    def test_keeping_the_own_email_is_allowed(self):
        response = self.patch_user(self.regular, {'email': 'regular@example.com'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_email_can_be_changed_to_a_free_one(self):
        response = self.patch_user(self.regular, {'email': 'free@example.com'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.regular.refresh_from_db()
        self.assertEqual(self.regular.email, 'free@example.com')


class SuperuserImpliesStaffTests(UserAdminTestCase):
    """One test per branch of the 'a superuser is always staff' rule."""

    def setUp(self):
        super().setUp()
        self.superuser2 = make_superuser('super_02', 'super2@example.com')
        self.login(self.superuser)

    def test_granting_superuser_also_grants_staff(self):
        response = self.patch_user(self.regular, {'is_superuser': True})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_staff'])
        self.assertTrue(response.data['is_superuser'])
        self.assertEqual(self.flags(self.regular), (True, True))

    def test_sending_both_flags_still_ends_up_staff(self):
        response = self.patch_user(
            self.regular, {'is_superuser': True, 'is_staff': False}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.flags(self.regular), (True, True))

    def test_staff_flag_cannot_be_removed_from_a_superuser(self):
        response = self.patch_user(self.superuser2, {'is_staff': False})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.flags(self.superuser2), (True, True))

    def test_staff_flag_can_be_removed_from_a_non_superuser(self):
        response = self.patch_user(self.staff2, {'is_staff': False})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.flags(self.staff2), (False, False))

    def test_staff_flag_can_be_granted_to_a_regular_user(self):
        response = self.patch_user(self.regular, {'is_staff': True})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.flags(self.regular), (True, False))

    def test_staff_false_on_a_regular_user_changes_nothing(self):
        response = self.patch_user(self.regular, {'is_staff': False})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.flags(self.regular), (False, False))

    def test_demoting_a_superuser_keeps_them_staff(self):
        response = self.patch_user(self.superuser2, {'is_superuser': False})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.flags(self.superuser2), (True, False))

    def test_other_changes_do_not_touch_the_flags(self):
        cases = (
            (self.regular, (False, False)),
            (self.staff2, (True, False)),
            (self.superuser2, (True, True)),
        )
        for target, expected in cases:
            with self.subTest(target=target.username):
                response = self.patch_user(
                    target, {'email': f'changed_{target.pk}@example.com'}
                )

                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(self.flags(target), expected)


class LastSuperuserTests(UserAdminTestCase):
    def setUp(self):
        super().setUp()  # exactly one superuser: self.superuser
        self.login(self.superuser)

    def test_last_superuser_cannot_be_deleted(self):
        response = self.client.delete(detail_url(self.superuser))

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn('detail', response.data)
        self.assertTrue(User.objects.filter(pk=self.superuser.pk).exists())

    def test_last_superuser_cannot_be_demoted(self):
        response = self.patch_user(self.superuser, {'is_superuser': False})

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(self.flags(self.superuser), (True, True))

    def test_string_false_does_not_bypass_the_guard(self):
        # Form data and sloppy clients send booleans as strings. The guard must
        # see a real False, not the truthy string "false".
        for fmt in ('json', 'multipart'):
            with self.subTest(format=fmt):
                response = self.patch_user(
                    self.superuser, {'is_superuser': 'false'}, fmt=fmt
                )

                self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
                self.assertEqual(self.flags(self.superuser), (True, True))

    def test_other_edits_of_the_last_superuser_are_allowed(self):
        edited = self.patch_user(self.superuser, {'email': 'new-super@example.com'})
        unchanged = self.patch_user(self.superuser, {'is_superuser': True})

        self.assertEqual(edited.status_code, status.HTTP_200_OK)
        self.assertEqual(unchanged.status_code, status.HTTP_200_OK)
        self.assertEqual(self.flags(self.superuser), (True, True))

    def test_with_two_superusers_one_can_be_demoted(self):
        second = make_superuser('super_02', 'super2@example.com')

        demoted = self.patch_user(second, {'is_superuser': False})
        blocked = self.patch_user(self.superuser, {'is_superuser': False})

        self.assertEqual(demoted.status_code, status.HTTP_200_OK)
        self.assertEqual(self.flags(second), (True, False))
        # Now only one is left, so the guard is back.
        self.assertEqual(blocked.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(self.flags(self.superuser), (True, True))

    def test_with_two_superusers_one_can_be_deleted(self):
        second = make_superuser('super_02', 'super2@example.com')

        deleted = self.client.delete(detail_url(second))
        blocked = self.client.delete(detail_url(self.superuser))

        self.assertEqual(deleted.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(pk=second.pk).exists())
        self.assertEqual(blocked.status_code, status.HTTP_409_CONFLICT)
        self.assertTrue(User.objects.filter(pk=self.superuser.pk).exists())


class DeletingAUserTests(UserAdminTestCase):
    def setUp(self):
        super().setUp()
        self.book = make_book()
        self.login(self.superuser)

    def test_reviews_and_shelf_items_are_removed_with_the_user(self):
        Review.objects.create(book=self.book, user=self.regular, rating=5)
        Review.objects.create(book=self.book, user=self.other, rating=3)
        Shelf.objects.create(user=self.regular, book=self.book)

        response = self.client.delete(detail_url(self.regular))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Review.objects.filter(user_id=self.regular.pk).exists())
        self.assertFalse(Shelf.objects.filter(user_id=self.regular.pk).exists())
        # Other people's data is untouched.
        self.assertTrue(Review.objects.filter(user=self.other).exists())

    def test_the_books_average_rating_is_recalculated(self):
        Review.objects.create(book=self.book, user=self.regular, rating=5)
        Review.objects.create(book=self.book, user=self.other, rating=3)
        self.book.refresh_from_db()
        # Sanity check: the review signals are wired up.
        self.assertEqual(self.book.average_rating, 4.0)

        self.client.delete(detail_url(self.regular))

        self.book.refresh_from_db()
        self.assertEqual(self.book.average_rating, 3.0)

    def test_average_rating_returns_to_zero_when_the_only_reviewer_is_deleted(self):
        Review.objects.create(book=self.book, user=self.regular, rating=5)

        self.client.delete(detail_url(self.regular))

        self.book.refresh_from_db()
        self.assertEqual(self.book.average_rating, 0.0)

    def test_books_added_by_the_user_survive(self):
        Book.objects.filter(pk=self.book.pk).update(added_by=self.regular)

        response = self.client.delete(detail_url(self.regular))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.book.refresh_from_db()
        self.assertIsNone(self.book.added_by)