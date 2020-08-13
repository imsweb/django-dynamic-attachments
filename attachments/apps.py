from django.apps import AppConfig


class AttachmentsConfig(AppConfig):
    name = "attachments"

    def user_has_access(self, request, attachment):
        # Check to see if this attachments model instance has a can_download,
        # otherwise fall back to checking request.user.is_authenticated by
        # default.
        obj = attachment.content_object
        
        if hasattr(obj, 'can_download'):
            return obj.can_download(request, attachment)

        return request.user.is_authenticated