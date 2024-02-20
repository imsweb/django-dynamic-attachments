# -*- coding: utf-8 -*-

from django.test import RequestFactory, TestCase

from attachments.utils import session, url_filename

from testapp.models import Document
from testapp.utils import get_storage

import io


class AttachmentTests (TestCase):

    def test_url_filename_character_escaping(self):
        self.assertEqual(url_filename(u'Résumé.pdf'), 'R%C3%A9sum%C3%A9.pdf')

    def test_url_filename_no_escaping(self):
        self.assertEqual(url_filename('Resume.pdf'), 'Resume.pdf')

    def test_json_field(self):
        d = {
            'key': 'value',
            'number': 42,
        }
        Document.objects.create(data=d)
        doc = Document.objects.get()
        self.assertEqual(doc.data, d)

    def test_upload(self):
        att_data = b'some data'
        request = RequestFactory().get('/test/page/')
        sess = session(request)
        att = io.BytesIO(att_data)
        att.name = 'testfile'
        response = self.client.post(
            path='/attachments/%s/' % sess.uuid,
            data={
                'attachment': att,
            },
            headers={
                'x-requested-with': 'XMLHttpRequest',
            },
        )
        self.assertEqual(response.json(), {
            'ok': True,
            'file_name': att.name,
            'file_size': len(att_data),
        })
        upload = sess.uploads.get()
        self.assertEqual(upload.file_name, att.name)
        self.assertEqual(upload.file_size, len(att_data))

    def test_delete(self):
        att_data = b'some data'
        request = RequestFactory().get('/test/page/')
        sess = session(request)
        att = io.BytesIO(att_data)
        att.name = 'testfile'
        response = self.client.post('/attachments/%s/' % sess.uuid, {'attachment': att})
        upload = sess.uploads.get()
        response = self.client.post(f'/attachments/delete/upload/{sess.uuid}/{upload.upload_id}', {'attachment': att})
        self.assertEqual(response.json(), {'ok': True})

    def test_download(self):
        storage = get_storage()
        att_data = b'some data'
        request = RequestFactory().get('/test/page/')
        sess = session(request)
        att = io.BytesIO(att_data)
        att.name = 'testfile'
        response = self.client.post(f'/attachments/download/{att.id}/{att.name}', {'attachment': att})
        self.assertEqual(
            response.json(), 
            {'X-Sendfile': att.file_path,
             'Content-Length': storage.size(att.file_path),
             'Content-Disposition': 'attachment; filename="%s"' % att.name})

    def test_update_attachment(self):
        att_data = b'some data'
        request = RequestFactory().get('/test/page/')
        sess = session(request)
        att = io.BytesIO(att_data)
        att.name = 'testfile'
        response = self.client.post(f'/attachments/update/{att.id}', {'attachment': att})
        self.assertEqual(response.json(), {'ok': True})
