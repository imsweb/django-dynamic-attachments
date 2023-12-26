from django.dispatch import Signal


# Sent when a file is uploaded.
# NOTE: provides args 'request', 'session'
file_uploaded = Signal()

# Sent when an attachment is downloaded.
# NOTE provides arg 'request'
file_download = Signal()

# Sent when attachments are attached to an object (i.e. saved)
# NOTE: provides args 'obj', 'attachments'
attachments_attached = Signal()

# Sent when a virus was detected during an upload
# NOTE: 'quarantine_path' may be None if the file was deleted instead of quarantined
# NOTE: The 'sender' will be the Upload object representing the offending file. The actual file will have been moved or removed.
# NOTE: provides args 'user', 'filename', 'exception', 'time_of_upload', 'quarantine_path'
virus_detected = Signal()
