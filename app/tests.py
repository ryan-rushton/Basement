import config
config.start_app = False

from unittest import TestCase
from .general_functions import convert_bytes_to_size


class TestConvert_bytes_to_size(TestCase):
    def test_convert_bytes_to_size(self):
        self.assertEqual(convert_bytes_to_size(1.51 * 1024 * 1024), '1.51 MiB')
        self.assertEqual(convert_bytes_to_size(0 * 1024 * 1024), '0.00 B')
        self.assertEqual(convert_bytes_to_size(2.99 * 1024), '2.99 KiB')
        self.assertEqual(convert_bytes_to_size(1.51 * 1024 * 1024 * 1024), '1.51 GiB')