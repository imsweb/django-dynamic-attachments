# -*- coding: utf-8 -*-

from django.test import TestCase
from attachments.utils import url_filename

class AttachmentTests (TestCase):

    def test_url_filename(self):
        self.assertEqual(url_filename(u'Résumé.pdf'), 'R%C3%A9sum%C3%A9.pdf')
