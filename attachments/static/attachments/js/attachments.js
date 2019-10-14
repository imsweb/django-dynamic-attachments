// TODO: check out https://github.com/moxiecode/moxie for IE polyfill

(function($) {
    $.fn.attachments = function(options) {
        var settings = $.extend({
            url: null,
            container: null,
            dropTarget: null,
            progress: null,
            success: null
        }, options);

        var refresh = function() {
        	  var data = {};
        	  if (settings.container && settings.container.hasClass('bind-form-on-refresh')) {
        		    data['bind-form-data'] = true;
        		    settings.container.removeClass('bind-form-on-refresh');
        	  }
            return $.ajax({
                url: settings.url,
                data: data,
                success: function(html) {
                    $(settings.container).empty().append(html).trigger('table-changed');
                }
            });
        };

        var resetInput = function(input) {
            var inp = $(input);
            inp.wrap('<form>').closest('form').get(0).reset();
            inp.unwrap();
        };

        var handleResponse = function(data, signal) {
            if(data.ok) {
                if(settings.success) {
                    settings.success(data);
                }
                signal.resolve(data);
            }
            else {
                if(settings.error) {
                    settings.error(data);
                }
                signal.reject(data);
            }
        };

        var iframeUpload = function(input) {
            var signal = $.Deferred();
            $.ajax(settings.url, {
                type: 'POST',
                iframe: true,
                files: $(input),
                dataType: 'text',
                success: function(responseText) {
                    var data = JSON.parse(responseText);
                    handleResponse(data, signal);
                    resetInput(input);
                    refresh();
                }
            });
            return signal;
        };

        var upload = function(file) {
            var signal = $.Deferred();
            var formData = new FormData();
            formData.append('attachment', file);
            //include properties data if it exists
            $(".properties >* :input").each( function() {
                if(this.type !== "checkbox"){
                    formData.append($(this).attr('id').slice(3), $(this).val());
                }else{
                    formData.append($(this).attr('id').slice(3), $(this).is(':checked') ? 'true' : 'false');
                }
            })
            var xhr = new XMLHttpRequest();
            if(settings.progress) {
                xhr.upload.addEventListener('progress', function(evt) {
                    if(evt.lengthComputable) {
                        var percentComplete = 100.0 * evt.loaded / evt.total;
                        settings.progress(percentComplete);
                    }
                }, false);
            }

            xhr.onload = function(evt) {
                // Refresh the attachments listing
                refresh();

                // Fire the success/error handlers with the returned JSON
                var data = JSON.parse(xhr.responseText);
                handleResponse(data, signal);
            };

            xhr.open('POST', settings.url, true);
            xhr.send(formData);

            return signal;
        };

        var uploadFiles = function(files, input) {
            var chain = null;
            // Call all the upload methods sequentially.
            for(var i = 0; i < files.length; i++) {
                chain = chain ? chain.then(upload(files[i])) : upload(files[i]);
            }
            // Clear the file input, if it was used to trigger the upload.
            if(input) {
                resetInput(input);
            }
        };

        if(settings.dropTarget) {
            $(settings.dropTarget).on({
                dragover: function(e) {
                    $(this).addClass('hover');
                    return false;
                },
                'dragend dragleave': function(e) {
                    $(this).removeClass('hover');
                    return false;
                },
                drop: function(e) {
                    e.preventDefault();
                    $(this).removeClass('hover');
                    uploadFiles(e.originalEvent.dataTransfer.files);
                    return false;
                }
            });
        }

        // Load the initial attachments container.
        refresh();


        return this.change(function(e) {
            if(typeof FormData === 'undefined') {
                iframeUpload(this);
            }
            else {
                uploadFiles(this.files, this);
            }
        });
    };

}(jQuery));

/*
 * The following functions only need to be applied once.
 * They will always be available if this (attachments.js) is loaded on a page.
 */
$('body').on('click', 'a.delete-upload', function() {
    var row = $(this).closest('.upload-item');
    $.ajax({
        type: 'POST',
        url: $(this).attr('href'),
        success: function(data) {
            row.remove();
            $(settings.container).trigger('table-changed');
        }
    });
    return false;
});

$('body').on('submit', '.update-attachment', function(e) {
    var postData = $(this).serializeArray();
    var formURL = $(this).attr('action');
    var popover = $(this).closest('.popover');
    var container = $(this).find('.attachment-properties-form');
    $.ajax({
        url: formURL,
        type: 'POST',
        data: postData,
        success: function(data, textStatus, jqXHR) {
            if(data.ok) {
                popover.fadeOut(150);
            }
            else {
                if(data.form_html) {
                    container.empty().html(data.form_html);
                }
                else {
                    alert(data.error);
                }
            }
        },
        error: function(jqXHR, textStatus, errorThrown) {
            alert('Error trying to update attachment properties.');
        }
    });
    return false;
});
