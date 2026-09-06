from django.test import TestCase


class HomePageTests(TestCase):
    def test_home_page_returns_success(self):
        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'e-Business Card Generator')
