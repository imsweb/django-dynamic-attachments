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
            }
        });
