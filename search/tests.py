from django.test import TestCase
from .tasks import update_sections

# Create your tests here.
class UpdateSectionsTestCase(TestCase):
    def setUp(self):
        pass

    def test_update_sections(self):
        self.assertEqual(update_sections(term=1234, department="CSE"), True)
        