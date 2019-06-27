from django.dispatch import Signal


# Sent when a file is uploaded.
file_uploaded = Signal(providing_args=('request', 'session'))

# Sent when an attachment is downloaded.
file_download = Signal(providing_args=('request',))

# Sent when attachments are attached to an object (i.e. saved)
attachments_attached = Signal(providing_args=('obj', 'attachments'))

# Sent when a virus was detected during an upload
# NOTE: 'quarantine_path' may be None if the file was deleted instead of quarantined
# NOTE: The 'sender' will be the Upload object representing the offending file. The actual file will have been moved or removed.
virus_detected = Signal(providing_args=('user', 'filename', 'exception', 'time_of_upload', 'quarantine_path'))
