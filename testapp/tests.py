# -*- coding: utf-8 -*-

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import Client, RequestFactory, TestCase

from attachments.models import Attachment
from attachments.utils import get_storage, session, url_filename
from testapp.models import Document

from contextlib import contextmanager
import io
import os


class AttachmentsTestCase(TestCase):
    client_class = Client

    @contextmanager
    def logged_in_as(self, user, client=None):
        if client is None:
            client = self.client

        try:
            client.force_login(
                user, backend="django.contrib.auth.backends.ModelBackend"
            )
            yield client
        finally:
            client.logout()


class AttachmentTests(AttachmentsTestCase):
    @classmethod
    def setUpTestData(self):
        self.superuser = get_user_model().objects.create(
            is_superuser=True,
            is_active=True,
        )
        self.attachment_data = b"some data"

    def attach_raw_data(self, attachment_data):
        request = RequestFactory().get("/test/page/")
        attach_session = session(request)
        attachment = io.BytesIO(attachment_data)
        attachment.name = "testfile"
        response = self.client.post(
            path="/attachments/%s/" % attach_session.uuid,
            data={
                "attachment": attachment,
            },
            headers={
                "x-requested-with": "XMLHttpRequest",
            },
        )
        return attachment, attach_session, response

    def create_attachment(self):
        return Attachment.objects.create(
            file_name="fake_file.txt",
            file_path=os.path.join("testapp", "uploads", "fake_file.txt"),
            object_id=1,
            content_type=ContentType.objects.get_for_model(Attachment),
            file_size=1,
        )

    def test_url_filename_character_escaping(self):
        self.assertEqual(url_filename("Résumé.pdf"), "R%C3%A9sum%C3%A9.pdf")

    def test_url_filename_no_escaping(self):
        self.assertEqual(url_filename("Resume.pdf"), "Resume.pdf")

    def test_json_field(self):
        d = {
            "key": "value",
            "number": 42,
        }
        Document.objects.create(data=d)
        doc = Document.objects.get()
        self.assertEqual(doc.data, d)

    def test_upload(self):
        attachment, attach_session, response = self.attach_raw_data(
            attachment_data=self.attachment_data
        )
        self.assertEqual(
            response.json(),
            {
                "ok": True,
                "file_name": attachment.name,
                "file_size": len(self.attachment_data),
            },
        )
        upload = attach_session.uploads.get()
        self.assertEqual(upload.file_name, attachment.name)
        self.assertEqual(upload.file_size, len(self.attachment_data))

    def test_delete(self):
        attachment, attach_session, _ = self.attach_raw_data(
            attachment_data=self.attachment_data
        )
        upload = attach_session.uploads.get()
        with self.logged_in_as(self.superuser):
            response = self.client.post(
                path=f"/attachments/delete/upload/{attach_session.uuid}/{upload.id}/",
                data={
                    "attachment": attachment,
                },
                headers={
                    "x-requested-with": "XMLHttpRequest",
                },
            )
        self.assertEqual(
            response.json(),
            {
                "ok": True,
            },
        )

    def test_download(self):
        storage = get_storage()
        RequestFactory().get("/test/page/")
        attachment = self.create_attachment()
        with self.logged_in_as(self.superuser):
            response = self.client.post(
                path=f"/attachments/download/{attachment.id}/",
                data={
                    "attachment": attachment,
                },
            )
        self.assertEqual(
            int(response.headers["Content-Length"]),
            storage.size(attachment.file_path),
        )
        self.assertEqual(
            response.headers["Content-Disposition"],
            f'attachment; filename="{attachment.file_name}"',
        )
        self.assertEqual(
            b"this is a fake file",
            list(response.streaming_content)[0].strip(),
        )

    def test_update_attachment(self):
        RequestFactory().get("/test/page/")
        attachment = self.create_attachment()
        with self.logged_in_as(self.superuser):
            response = self.client.post(
                path=f"/attachments/update/{attachment.id}/",
                headers={
                    "x-requested-with": "XMLHttpRequest",
                },
            )
        self.assertEqual(
            response.json(),
            {
                "ok": True,
            },
        )
