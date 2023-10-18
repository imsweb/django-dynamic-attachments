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

        $(settings.container).on('click', 'a.delete-upload', function() {
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

        let buildXHR = function(file) {
            var xhr = new XMLHttpRequest();
            if(settings.progress) {
                xhr.upload.addEventListener('progress', function(evt) {
                    if(evt.lengthComputable) {
                        var percentComplete = 100.0 * evt.loaded / evt.total;
                        settings.progress(percentComplete, file);
                    }
                }, false);
            }

            return xhr;
        };
        
        let onload = function(xhr) {
            var signal = $.Deferred();
            xhr.onload = function(evt) {
                // Refresh the attachments listing
                refresh();

                // Fire the success/error handlers with the returned JSON
                var data = JSON.parse(xhr.responseText);
                handleResponse(data, signal);
            };

            return [xhr, signal];
        };
        
        let send = function(xhr, file) {
            var formData = new FormData();
            formData.append('attachment', file);
            //include properties data if it exists
            $(".properties >* :input").each( function() {
                var name = $(this).attr('id').slice(3);
                if(this.type !== "checkbox"){
                    var value = $(this).val();
                } else{
                    var value = $(this).is(':checked') ? 'true' : 'false';
                }
                formData.append(name, value);
            });

            xhr.open('POST', settings.url, true);
            xhr.setRequestHeader('X-REQUESTED-WITH', 'XMLHttpRequest');
            xhr.send(formData);
        };

        let uploadFiles = function(files, input) {
            // start at 1 since we manually send the first file & JS is 0 based.
            var index = 1;
            var xhrs = {};
            
            for(var i = 0; i < files.length; i++) {
                var file = files[i];
                var [xhr, signal] = onload(buildXHR(file));

                if (i==0) {
                    // Send the first attachment
                    send(xhr, file);
                } else {
                    // otherwise, store & send later
                    xhrs[i] = [xhr, file];
                }

                if (i+1 != files.length) {
                    // send next file once prev finishes. Exclude last file sine nothing comes next.
                    signal.then(function() {
                        // 0 is the xhr request, 1 is the file to send
                        send(xhrs[index][0], xhrs[index][1]);
                        index++;
                    });
                } else {
                    signal.then(function() {
                        // if the input was used to trigger the upload, then
                        // clear it once the last file finishes uploading.
                        if(input) {
                            resetInput(input);
                        }
                    });
                }
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
