Quickstart Guide
================

1. Add ``attachments`` to your ``INSTALLED_APPS`` setting.

2. Create an attachments session in any Django view that will be processing attachments::

        import attachments
        
        def myview(request):
            session = attachments.session(request)
            if request.method == 'POST':
                form = MyForm(request.POST)
                if form.is_valid():
                    obj = form.save()
                    session.attach(obj) # This will attach all uploaded files to the object using a generic foreign key.
                    session.delete()    # Cleans up any temporary files saved to disk.
            else:
                form = MyForm()
            return render(request, 'template.html', {'form': form, 'session': session})

.. highlight:: html+django

3. Include ``attachments/js/attachments.js`` in whichever pages you want to add attachment processing to::

        {% load static %}
        <script src="{% static "attachments/js/attachments.js" %}"></script>

4. Define an attachments container, a file input, a hidden input for the session ID, and optionally a progress bar on your page::

        <div id="attachments"></div>
        <div class="progress">
            <div class="progress-bar hidden" id="progress"></div>
        </div>
        <input type="file" id="attach" />
        {{ session.hidden_input }}

.. highlight:: js+django

5. Initialize the attachments code::

        $('#attach').attachments({
            url: '{{ session.get_absolute_url }}',
            container: '#attachments',
            progress: function(pct) {
                $('#progress').removeClass('hidden').css('width', pct + '%');
            },
            success: function(data) {
                $('#progress').addClass('hidden');
            },
            error: function(data) {
                alert("Error attaching file:\n" + data.error + "\nPlease contact website administrator if this problem persists.");
                $('#progress').addClass('hidden');
            }           
        });
        
6. Set the ``ATTACHMENT_TEMP_DIR`` setting to the temporary directory you would like files to save in a settings file

7. (OPTIONAL) If you have the clamav daemon running on your server set ``ATTACHMENTS_CLAMD`` to true in a settings file. If you would like email alerts set ``ATTACHMENTS_VIRUS_EMAIL`` to a list of recipients. If you would like to set a path to quarantine infected files that are uploaded set ``ATTACHMENTS_QUARANTINE_PATH`` to desired path, if not set the default behavior will be to remove the files. Note that this currently only works for linux servers and the path to the clam socket will need to be set in /etc/clamav/clamd.conf or /etc/clamd.conf for this to work.

8. (OPTIONAL) If you would like to limit the the file types users are able to upload set ``ATTACHMENTS_ALLOWED_FILE_TYPES`` to a list or tuple of mimetypes in a settings file. IE: ALLOWED_FILE_TYPES = ['text/html'] (allowing only html files. You can also just set it to the the text after the first '/' as in [html]. Note that for some files like excel they have mimetypes like `application/vnd.ms-excel` so make sure that you check the mimetypes you want before setting them!

9. (OPTIONAL) If you would like to set a maximum file size that users are able to upload set ``ATTACHMENTS_MAXIMUM_FILE_SIZE`` to an int of the maximum bytes you would like to allow. So a maximum size of 10MB would be MAXIMUM_FILE_SIZE = 10485760  Note that it is the binary bytes not the decimal!