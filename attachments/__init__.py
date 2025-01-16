__version__ = "4.0.6"


def session(*args, **kwargs):
    # Expose utils.session without importing utils from __init__ at module level.
    from .utils import session as attachment_session
    return attachment_session(*args, **kwargs)
