from django.db import models

from attachments.utils import JSONField


class Document (models.Model):
    data = JSONField()
