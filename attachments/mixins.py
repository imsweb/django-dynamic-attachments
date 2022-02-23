from django.core.exceptions import ImproperlyConfigured


class AttachmentsMixin:
    """
    This mixin is intended to be used with a form so that attachments functionality
    can be tied in with the form itself. It handles all of the attaching and deleting.

    To use this mixin, first create a class that inherits from it so that the
    ``get_session_error_message`` can be overridden.
    Then, make it a superclass of an existing ``ModelForm``.

    Due to method resolution order, make this mixin the left-most superclass.
    For example, ``class MyForm(MyAttachmentsMixin, forms.ModelForm)``.

    The ``__init__`` method does the following:
        - Make ``session`` and ``attachments_field_name`` instance variables.
        - Keep track of files that will be deleted.

    :param session: an already-created session
    :type session: optional
    :param attachments_field_name: the name of the field on the model that represents the attachments
    :type attachments_field_name: str, optional
    """
    def __init__(self, *args, session=None, attachments_field_name='attachments', **kwargs):
        self.session = session
        self.attachments_field_name = attachments_field_name
        self.attached_files = []
        self.session_error = None
        # This needs to be done since args may be (), (None, ), or (x, ...) where x is truthy.
        if args and args[0] and args[0].get('delete-attachments'):
            try:
                # If this is QueryDict, must use getlist.
                self.deletions = [int(pk) for pk in args[0].getlist('delete-attachments')]
            except AttributeError:
                # If this is any other mapping, must use get.
                self.deletions = args[0].get('delete-attachments')
        else:
            self.deletions = []
        super().__init__(*args, **kwargs)

    def is_valid(self):
        """
        :returns: ``True`` if both the form and session are valid.
        """
        return all([super().is_valid(), self._session_is_valid()])

    def _session_is_valid(self):
        """
        :returns: ``True`` if the session is valid.
        """
        if not self.session:
            return True
        self._clean_session()
        return not self.session_error

    def _clean_session(self):
        """Add a session error, if necessary."""
        if not self.session.is_valid():
            self.session_error = self.get_session_error_message()
        return self.session_error

    def get_session_error_message(self):
        """
        :returns: a string containing the session error message
        """
        raise ImproperlyConfigured('Please implement this method so that a session error message will display.')

    def uploads_exist(self):
        """
        :returns: ``True`` if uploads exist.
        """
        return bool(self.session) and self.session.uploads.exists()

    def has_changed(self):
        """
        :returns: ``True`` if the form or session has changed.
        """
        return super().has_changed() or bool(self.deletions) or self.uploads_exist()

    def save(self, commit=True):
        """
        Attach uploads from the attachment session to the ``ModelForm`` instance, delete the session,
        and perform any deletions specified by the POST data.
        """
        instance = super().save(commit=False)

        base_save_m2m = self.save_m2m
        def save_m2m():
            base_save_m2m()
            if self.uploads_exist():
                self.attached_files = self.session.attach(instance)
                self.session.delete()

            getattr(instance, self.attachments_field_name).filter(pk__in=self.deletions).delete()
        self.save_m2m = save_m2m

        if commit:
            instance.save()
            self.save_m2m()

        return instance
