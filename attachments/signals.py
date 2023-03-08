from django.dispatch import Signal


# Sent when a file is uploaded.
file_uploaded = Signal()

# Sent when an attachment is downloaded.
file_download = Signal()

# Sent when attachments are attached to an object (i.e. saved)
attachments_attached = Signal()

# Sent when a virus was detected during an upload
# NOTE: 'quarantine_path' may be None if the file was deleted instead of quarantined
# NOTE: The 'sender' will be the Upload object representing the offending file. The actual file will have been moved or removed.
virus_detected = Signal()
