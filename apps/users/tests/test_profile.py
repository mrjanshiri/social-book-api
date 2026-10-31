import shutil
import tempfile
from io import BytesIO
import os

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction
from django.test import override_settings
from PIL import Image
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()

PROFILE_URL = '/api/auth/user_profile/'
PASSWORD = 'Orig-pass-1!'
PROFILE_FIELDS = {'username', 'first_name', 'last_name', 'email', 'profile_picture'}
INVALID_EMAILS = ('not-an-email', 'alice@', '@example.com', 'alice@@example.com')


def make_user(username='alice_01', email='alice@example.com', **extra):
    return User.objects.create_user(
        username=username, email=email, password=PASSWORD, **extra
    )


def png_bytes(width=10, height=10, noisy=False):
    # noisy=True fills the image with random pixels so PNG compression can't
    # shrink it: that's how we get a multi-megabyte file.
    if noisy:
        image = Image.frombytes('RGB', (width, height), os.urandom(width * height * 3))
    else:
        image = Image.new('RGB', (width, height), (200, 30, 30))
    buffer = BytesIO()
    image.save(buffer, format='PNG')
    return buffer.getvalue()


def image_upload(name='avatar.png', **kwargs):
    return SimpleUploadedFile(name, png_bytes(**kwargs), content_type='image/png')


class _Rollback(Exception):
    pass


class ProfileTestCase(APITestCase):
    """One logged-in user with a first and last name."""

    def setUp(self):
        self.user = make_user(first_name='Alice', last_name='Smith')
        self.client.force_authenticate(user=self.user)

    def reload(self):
        self.user.refresh_from_db()
        return self.user


class ProfileReadTests(ProfileTestCase):
    def test_anonymous_is_rejected(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(PROFILE_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_returns_only_profile_fields(self):
        response = self.client.get(PROFILE_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # No id, password, is_staff, is_superuser, ...
        self.assertEqual(set(response.data), PROFILE_FIELDS)

    def test_returns_the_callers_own_data(self):
        response = self.client.get(PROFILE_URL)
        self.assertEqual(response.data['username'], 'alice_01')
        self.assertEqual(response.data['email'], 'alice@example.com')
        self.assertEqual(response.data['first_name'], 'Alice')

        other = make_user(username='bob_02', email='bob@example.com')
        self.client.force_authenticate(user=other)
        response = self.client.get(PROFILE_URL)
        self.assertEqual(response.data['username'], 'bob_02')
        self.assertEqual(response.data['email'], 'bob@example.com')

    def test_picture_is_null_when_not_set(self):
        response = self.client.get(PROFILE_URL)

        self.assertIsNone(response.data['profile_picture'])


class ProfileUpdateTests(ProfileTestCase):
    def test_anonymous_cannot_update(self):
        self.client.force_authenticate(user=None)

        for method in ('put', 'patch'):
            with self.subTest(method=method):
                response = getattr(self.client, method)(
                    PROFILE_URL, {'email': 'x@example.com'}, format='json'
                )
                self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_put_requires_email(self):
        response = self.client.put(PROFILE_URL, {'first_name': 'Changed'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
        self.assertEqual(self.reload().first_name, 'Alice')

    def test_put_without_optional_fields_keeps_them(self):
        response = self.client.put(
            PROFILE_URL, {'email': 'alice@example.com'}, format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user = self.reload()
        self.assertEqual(user.first_name, 'Alice')
        self.assertEqual(user.last_name, 'Smith')

    def test_put_full_update(self):
        payload = {'email': 'new@example.com', 'first_name': 'Alicia', 'last_name': 'Jones'}

        response = self.client.put(PROFILE_URL, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Alicia')
        user = self.reload()
        self.assertEqual(user.email, 'new@example.com')
        self.assertEqual(user.first_name, 'Alicia')
        self.assertEqual(user.last_name, 'Jones')

    def test_patch_updates_only_the_sent_fields(self):
        response = self.client.patch(PROFILE_URL, {'first_name': 'Alicia'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user = self.reload()
        self.assertEqual(user.first_name, 'Alicia')
        self.assertEqual(user.last_name, 'Smith')
        self.assertEqual(user.email, 'alice@example.com')

    def test_patch_with_empty_body_changes_nothing(self):
        response = self.client.patch(PROFILE_URL, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user = self.reload()
        self.assertEqual(user.first_name, 'Alice')
        self.assertEqual(user.last_name, 'Smith')
        self.assertEqual(user.email, 'alice@example.com')

    def test_names_can_be_cleared(self):
        response = self.client.patch(PROFILE_URL, {'first_name': ''}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.reload().first_name, '')

    def test_overlong_names_are_rejected(self):
        for field in ('first_name', 'last_name'):
            with self.subTest(field=field):
                response = self.client.patch(PROFILE_URL, {field: 'a' * 101}, format='json')

                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn(field, response.data)

    def test_other_methods_are_not_allowed(self):
        for method in ('post', 'delete'):
            with self.subTest(method=method):
                response = getattr(self.client, method)(PROFILE_URL)

                self.assertEqual(
                    response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED
                )


class ProfileImmutableFieldsTests(ProfileTestCase):
    def test_username_cannot_be_changed(self):
        response = self.client.patch(PROFILE_URL, {'username': 'new_name'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)
        self.assertEqual(self.reload().username, 'alice_01')

    def test_sending_the_current_username_is_also_rejected(self):
        response = self.client.patch(PROFILE_URL, {'username': 'alice_01'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)

    def test_username_is_rejected_on_put_too(self):
        payload = {'email': 'alice@example.com', 'username': 'new_name'}

        response = self.client.put(PROFILE_URL, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)
        self.assertEqual(self.reload().username, 'alice_01')

    def test_rejected_username_blocks_the_whole_update(self):
        payload = {'first_name': 'Changed', 'username': 'new_name'}

        response = self.client.patch(PROFILE_URL, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.reload().first_name, 'Alice')

    def test_privilege_and_internal_fields_are_ignored(self):
        payload = {
            'first_name': 'Alicia',
            'is_staff': True,
            'is_superuser': True,
            'is_active': False,
            'id': 9999,
        }

        response = self.client.patch(PROFILE_URL, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user = self.reload()
        self.assertEqual(user.first_name, 'Alicia')
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.is_active)
        self.assertFalse(User.objects.filter(pk=9999).exists())
        for key in ('is_staff', 'is_superuser', 'is_active', 'id'):
            self.assertNotIn(key, response.data)

    def test_password_cannot_be_changed_here(self):
        response = self.client.patch(
            PROFILE_URL, {'password': 'Hacked-pass-9!'}, format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn('password', response.data)
        user = self.reload()
        self.assertTrue(user.check_password(PASSWORD))
        self.assertFalse(user.check_password('Hacked-pass-9!'))


class ProfileEmailTests(ProfileTestCase):
    def test_invalid_email_is_rejected(self):
        for email in INVALID_EMAILS:
            with self.subTest(email=email):
                response = self.client.patch(PROFILE_URL, {'email': email}, format='json')

                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn('email', response.data)
                self.assertEqual(self.reload().email, 'alice@example.com')

    def test_blank_email_is_rejected(self):
        for method in ('put', 'patch'):
            with self.subTest(method=method):
                response = getattr(self.client, method)(
                    PROFILE_URL, {'email': ''}, format='json'
                )

                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn('email', response.data)
                self.assertEqual(self.reload().email, 'alice@example.com')

    def test_email_of_another_user_is_rejected_ignoring_case(self):
        make_user(username='bob_02', email='bob@example.com')

        for email in ('bob@example.com', 'Bob@Example.com', 'BOB@EXAMPLE.COM'):
            with self.subTest(email=email):
                response = self.client.patch(PROFILE_URL, {'email': email}, format='json')

                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn('email', response.data)
                self.assertEqual(self.reload().email, 'alice@example.com')

    def test_keeping_the_own_email_is_allowed(self):
        response = self.client.patch(
            PROFILE_URL, {'email': 'alice@example.com'}, format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_email_can_be_changed_to_a_free_one(self):
        response = self.client.patch(PROFILE_URL, {'email': 'new@example.com'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'new@example.com')
        self.assertEqual(self.reload().email, 'new@example.com')


class ProfilePictureTests(ProfileTestCase):
    def setUp(self):
        super().setUp()
        # Never write into the real media/ folder.
        media_root = tempfile.mkdtemp()
        override = override_settings(MEDIA_ROOT=media_root)
        override.enable()
        self.addCleanup(override.disable)
        self.addCleanup(shutil.rmtree, media_root, ignore_errors=True)

    def give_picture(self, name='seed.png'):
        """Attach a picture straight through the model (no API involved)."""
        self.user.profile_picture.save(name, ContentFile(png_bytes()))
        return self.user.profile_picture.name

    def upload(self, upload):
        # Old-file deletion is registered with transaction.on_commit; inside a
        # TestCase transaction it only runs if we execute the callbacks.
        with self.captureOnCommitCallbacks(execute=True):
            return self.client.patch(
                PROFILE_URL, {'profile_picture': upload}, format='multipart'
            )

    def test_upload_sets_the_picture(self):
        response = self.upload(image_upload('me.png'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('profile_pics/', response.data['profile_picture'])
        user = self.reload()
        self.assertTrue(user.profile_picture)
        self.assertTrue(default_storage.exists(user.profile_picture.name))

    def test_non_image_file_is_rejected(self):
        fake = SimpleUploadedFile('fake.png', b'this is not an image', content_type='image/png')

        response = self.upload(fake)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('profile_picture', response.data)
        self.assertFalse(self.reload().profile_picture)

    def test_large_upload_is_accepted(self):
        big = image_upload('big.png', width=1000, height=1400, noisy=True)
        # Must be above Django's 2.5 MB in-memory limit, so it is spooled to disk.
        self.assertGreater(big.size, 3 * 1024 * 1024)

        response = self.upload(big)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.reload().profile_picture)

    def test_replacing_the_picture_deletes_the_old_file(self):
        old_name = self.give_picture('old.png')
        self.assertTrue(default_storage.exists(old_name))

        response = self.upload(image_upload('new.png'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        new_name = self.reload().profile_picture.name
        self.assertNotEqual(old_name, new_name)
        self.assertFalse(default_storage.exists(old_name))
        self.assertTrue(default_storage.exists(new_name))

    def test_clearing_the_picture_deletes_the_file(self):
        name = self.give_picture()

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.patch(
                PROFILE_URL, {'profile_picture': None}, format='json'
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data['profile_picture'])
        self.assertFalse(self.reload().profile_picture)
        self.assertFalse(default_storage.exists(name))

    def test_updating_other_fields_keeps_the_picture(self):
        name = self.give_picture()

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.patch(PROFILE_URL, {'first_name': 'Alicia'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.reload().profile_picture.name, name)
        self.assertTrue(default_storage.exists(name))

    def test_deleting_the_account_deletes_the_picture(self):
        name = self.give_picture()

        with self.captureOnCommitCallbacks(execute=True):
            self.user.delete()

        self.assertFalse(default_storage.exists(name))

    def test_rolled_back_delete_keeps_the_picture(self):
        name = self.give_picture()

        with self.captureOnCommitCallbacks(execute=True):
            with self.assertRaises(_Rollback):
                with transaction.atomic():
                    self.user.delete()
                    raise _Rollback

        self.assertTrue(default_storage.exists(name))