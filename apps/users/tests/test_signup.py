from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()

# Assumes backend/urls.py mounts apps.users.urls under api/auth/.
SIGNUP_URL = '/api/auth/signup/'
LOGIN_URL = '/api/auth/login/'


def valid_payload(**overrides):
    payload = {
        'username': 'alice_01',
        'password': 'S3cure-pass!',
        'email': 'alice@example.com',
    }
    payload.update(overrides)
    return payload


class SignupSuccessTests(APITestCase):
    def test_valid_signup_creates_user(self):
        response = self.client.post(SIGNUP_URL, valid_payload(), format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, {'message': 'User created successfully.'})
        user = User.objects.get(username='alice_01')
        self.assertEqual(user.email, 'alice@example.com')

    def test_password_is_stored_hashed(self):
        self.client.post(SIGNUP_URL, valid_payload(), format='json')

        user = User.objects.get(username='alice_01')
        self.assertNotEqual(user.password, 'S3cure-pass!')
        self.assertTrue(user.check_password('S3cure-pass!'))

    def test_response_does_not_expose_account_data(self):
        response = self.client.post(SIGNUP_URL, valid_payload(), format='json')

        for key in ('id', 'username', 'email', 'password'):
            self.assertNotIn(key, response.data)

    def test_new_user_is_a_regular_user(self):
        self.client.post(SIGNUP_URL, valid_payload(), format='json')

        user = User.objects.get(username='alice_01')
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_privilege_fields_in_payload_are_ignored(self):
        payload = valid_payload(is_staff=True, is_superuser=True)

        response = self.client.post(SIGNUP_URL, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username='alice_01')
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_username_may_mix_letters_digits_and_underscores(self):
        payload = valid_payload(username='Ali_99_x')

        response = self.client.post(SIGNUP_URL, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_new_user_can_log_in(self):
        self.client.post(SIGNUP_URL, valid_payload(), format='json')

        response = self.client.post(
            LOGIN_URL,
            {'username': 'alice_01', 'password': 'S3cure-pass!'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)


class SignupValidationTests(APITestCase):
    def assert_rejected(self, payload, field):
        before = User.objects.count()

        response = self.client.post(SIGNUP_URL, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(field, response.data)
        self.assertEqual(User.objects.count(), before)

    def test_missing_field_is_rejected(self):
        for field in ('username', 'password', 'email'):
            with self.subTest(field=field):
                payload = valid_payload()
                del payload[field]
                self.assert_rejected(payload, field)

    def test_blank_field_is_rejected(self):
        for field in ('username', 'password', 'email'):
            with self.subTest(field=field):
                self.assert_rejected(valid_payload(**{field: ''}), field)

    def test_username_with_invalid_characters_is_rejected(self):
        for username in ('ali baba', 'ali-baba', 'ali.baba', 'ali@home', 'علی'):
            with self.subTest(username=username):
                self.assert_rejected(valid_payload(username=username), 'username')

    def test_invalid_email_is_rejected(self):
        for email in ('not-an-email', 'alice@', '@example.com', 'alice@@example.com'):
            with self.subTest(email=email):
                self.assert_rejected(valid_payload(email=email), 'email')

    def test_duplicate_username_is_rejected(self):
        User.objects.create_user(
            username='alice_01', email='other@example.com', password='x'
        )

        self.assert_rejected(valid_payload(), 'username')

    def test_duplicate_email_is_rejected(self):
        User.objects.create_user(
            username='someone_else', email='alice@example.com', password='x'
        )

        self.assert_rejected(valid_payload(), 'email')


class SignupMethodTests(APITestCase):
    def test_get_is_not_allowed(self):
        response = self.client.get(SIGNUP_URL)

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)



class SignupLengthLimitTests(APITestCase):
    def test_overlong_username_is_rejected(self):
        before = User.objects.count()

        response = self.client.post(
            SIGNUP_URL, valid_payload(username='a' * 151), format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)
        self.assertEqual(User.objects.count(), before)