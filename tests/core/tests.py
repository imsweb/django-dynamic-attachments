# -*- coding: utf-8 -*-

from django.test import TestCase
from attachments.utils import url_filename
from .models import Document

class AttachmentTests (TestCase):

    def test_url_filename(self):
        self.assertEqual(url_filename(u'Résumé.pdf'), 'R%C3%A9sum%C3%A9.pdf')

    def test_json_field(self):
        d = {
            'key': 'value',
            'number': 42,
        }
        Document.objects.create(data=d)
        doc = Document.objects.get()
        self.assertEqual(doc.data, d)
