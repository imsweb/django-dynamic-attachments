from django.dispatch import Signal

# Sent when a file is uploaded.
file_uploaded = Signal(providing_args=('request', 'session'))

# Sent when an attachment is downloaded.
file_downloaded = Signal(providing_args=('request',))
