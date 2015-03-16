// TODO: check out https://github.com/moxiecode/moxie for IE polyfill

(function($) {
    $.fn.attachments = function(options) {
        var settings = $.extend({
            url: null,
            container: null,
            dropTarget: null,
            contentType: null,
            progress: null,
            success: null
        }, options);
        
        var refresh = function() {
            return $.ajax({
                url: settings.url,
                data: {contentType: settings.contentType},
                success: function(html) {
                    $(settings.container).empty().append(html);
                }
            });
        };
        
        var upload = function(file) {
            var signal = $.Deferred();
            var formData = new FormData();
            formData.append('attachment', file);
            
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
                var inp = $(input);
                inp.wrap('<form>').closest('form').get(0).reset();
                inp.unwrap();
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
            uploadFiles(this.files, this);
        });
    };
    
    $('body').on('click', 'a.delete-upload', function() {
        var row = $(this).closest('.upload-item');
        $.ajax({
            type: 'POST',
            url: $(this).attr('href'),
            success: function(data) {
                row.remove();
            }
        });
        return false;
    });
    
    $("body").on('submit', '.update-attachment', function(e)
		{
		    var postData = $(this).serializeArray();
		    var formURL = $(this).attr("action");
		    $.ajax(
		    {
		        url : formURL,
		        type: "POST",
		        data : postData,
		        success:function(data, textStatus, jqXHR) 
		        {
		        	$(".att-prop-saved-alert").show();
		        	//If we want to hide popup on save sue this
		        	//$(".popover").hide();
		        },
		        error: function(jqXHR, textStatus, errorThrown) 
		        {
		        	$(".att-prop-save-failed-alert").show();
		        }
		    });
		    e.preventDefault(); //STOP default action
		    e.unbind(); //unbind. to stop multiple form submit.
		});
		 
}(jQuery));






















