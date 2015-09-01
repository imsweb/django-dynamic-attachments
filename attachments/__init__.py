__version_info__ = (0, 1, 0)
__version__ = '.'.join(str(i) for i in __version_info__)

def session(*args, **kwargs):
    from .utils import session as attachment_session
    return attachment_session(*args, **kwargs)
