__version_info__ = (3, 4, 0)
__version__ = '.'.join(str(i) for i in __version_info__)


default_app_config = 'attachments.apps.AttachmentsConfig'


def session(*args, **kwargs):
    # Expose utils.session without importing utils from __init__ at module level.
    from .utils import session as attachment_session
    return attachment_session(*args, **kwargs)
