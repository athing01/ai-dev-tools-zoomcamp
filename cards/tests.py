from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from .forms import BusinessCardForm


class BusinessCardFormTests(TestCase):
    def valid_data(self):
        return {
            'primary_language': 'thai',
            'name_th': 'สมชาย ใจดี',
            'name_en': '',
            'role_th': '',
            'role_en': '',
            'company_th': '',
            'company_en': '',
            'address': '',
            'phone': '0812345678',
            'email': 'somchai@example.com',
            'social_links': '',
            'qr_destination_url': 'https://example.com/profile',
            'orientation': 'portrait',
            'photo_choice': 'without_photo',
        }

    def test_optional_fields_and_photo_may_be_left_empty(self):
        form = BusinessCardForm(data=self.valid_data())

        self.assertTrue(form.is_valid())

    def test_missing_required_fields_are_invalid(self):
        data = self.valid_data()
        for field in (
            'primary_language',
            'qr_destination_url',
            'orientation',
            'photo_choice',
        ):
            data[field] = ''

        form = BusinessCardForm(data=data)

        self.assertFalse(form.is_valid())
        for field in (
            'primary_language',
            'qr_destination_url',
            'orientation',
            'photo_choice',
        ):
            self.assertIn(field, form.errors)

    def test_phone_only_is_valid(self):
        data = self.valid_data()
        data['email'] = ''

        form = BusinessCardForm(data=data)

        self.assertTrue(form.is_valid(), form.errors)

    def test_email_only_is_valid(self):
        data = self.valid_data()
        data['phone'] = ''

        form = BusinessCardForm(data=data)

        self.assertTrue(form.is_valid(), form.errors)

    def test_phone_and_email_are_valid(self):
        form = BusinessCardForm(data=self.valid_data())

        self.assertTrue(form.is_valid(), form.errors)

    def test_phone_and_email_both_missing_are_invalid(self):
        data = self.valid_data()
        data['phone'] = ''
        data['email'] = ''

        form = BusinessCardForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)

    def test_invalid_email_is_rejected_when_provided(self):
        data = self.valid_data()
        data['phone'] = ''
        data['email'] = 'not-an-email'

        form = BusinessCardForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_invalid_email_is_rejected_when_phone_is_provided(self):
        data = self.valid_data()
        data['email'] = 'not-an-email'

        form = BusinessCardForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_invalid_qr_destination_url_is_rejected(self):
        data = self.valid_data()
        data['qr_destination_url'] = 'not-a-url'

        form = BusinessCardForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn('qr_destination_url', form.errors)

    def test_primary_language_must_be_a_supported_choice(self):
        data = self.valid_data()
        data['primary_language'] = 'japanese'

        form = BusinessCardForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn('primary_language', form.errors)

    def test_primary_language_requires_its_matching_name(self):
        cases = (
            ('thai', 'name_th', 'name_en'),
            ('english', 'name_en', 'name_th'),
        )

        for language, required_name, other_name in cases:
            with self.subTest(language=language):
                data = self.valid_data()
                data['primary_language'] = language
                data[required_name] = ''
                data[other_name] = 'Optional name'

                form = BusinessCardForm(data=data)

                self.assertFalse(form.is_valid())
                self.assertIn(required_name, form.errors)

    def test_invalid_orientation_and_photo_choice_are_rejected(self):
        for field in ('orientation', 'photo_choice'):
            with self.subTest(field=field):
                data = self.valid_data()
                data[field] = 'invalid-choice'

                form = BusinessCardForm(data=data)

                self.assertFalse(form.is_valid())
                self.assertIn(field, form.errors)

    def test_with_photo_choice_is_valid_without_an_uploaded_file(self):
        data = self.valid_data()
        data['photo_choice'] = 'with_photo'

        form = BusinessCardForm(data=data)

        self.assertTrue(form.is_valid(), form.errors)

    def test_populated_optional_text_fields_are_retained(self):
        data = self.valid_data()
        optional_values = {
            'name_en': 'Somchai Jaidee',
            'role_th': 'นักพัฒนา',
            'role_en': 'Developer',
            'company_th': 'บริษัท ตัวอย่าง',
            'company_en': 'Example Company',
            'address': 'Bangkok, Thailand',
            'social_links': 'https://example.com/social',
        }
        data.update(optional_values)

        form = BusinessCardForm(data=data)

        self.assertTrue(form.is_valid(), form.errors)
        for field, value in optional_values.items():
            self.assertEqual(form.cleaned_data[field], value)


class HomePageTests(TestCase):
    def valid_data(self):
        return {
            'primary_language': 'english',
            'name_th': '',
            'name_en': 'Jane Doe',
            'phone': '0812345678',
            'email': 'jane@example.com',
            'qr_destination_url': 'https://example.com/profile',
            'orientation': 'landscape',
            'photo_choice': 'without_photo',
        }

    def test_home_page_displays_the_form(self):
        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'e-Business Card Generator')
        self.assertContains(response, 'Primary language')

    def test_valid_submission_is_accepted_without_persistence(self):
        response = self.client.post(reverse('home'), data=self.valid_data())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Card information is valid.')

    def test_invalid_submission_redisplays_errors_without_confirmation(self):
        data = self.valid_data()
        data['phone'] = ''
        data['email'] = ''

        response = self.client.post(reverse('home'), data=data)

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            'Provide at least one of a phone number or an email address.',
        )
        self.assertNotContains(response, 'Card information is valid.')

    def test_uploaded_photo_is_accepted_by_the_view(self):
        data = self.valid_data()
        data['photo_choice'] = 'with_photo'
        data['photo'] = SimpleUploadedFile(
            'photo.jpg',
            b'image-data',
            content_type='image/jpeg',
        )

        response = self.client.post(reverse('home'), data=data)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Card information is valid.')
