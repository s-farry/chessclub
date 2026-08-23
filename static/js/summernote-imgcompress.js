/**
 * Summernote image auto-compression.
 * Images over COMPRESS_THRESHOLD are compressed via Canvas before upload.
 * A brief notice is shown when compression occurs.
 */
(function ($) {
    'use strict';

    var COMPRESS_THRESHOLD = 1 * 1024 * 1024;  // compress if > 1 MB
    var MAX_DIMENSION      = 2048;               // max width or height after resize
    var JPEG_QUALITY       = 0.82;
    var UPLOAD_URL         = '/summernote/upload/';

    function getCsrf() {
        var m = document.cookie.match(/csrftoken=([^;]+)/);
        return m ? m[1] : '';
    }

    function showNotice($note, msg) {
        var $editor = $note.closest('.note-editor');
        if (!$editor.length) return;
        $editor.css('position', 'relative');
        var $n = $('<div>').text(msg).css({
            position: 'absolute', top: '8px', right: '8px',
            background: '#856404', color: '#fff3cd',
            padding: '6px 14px', borderRadius: '4px',
            fontSize: '0.82rem', zIndex: 9999,
            boxShadow: '0 2px 6px rgba(0,0,0,0.3)',
            pointerEvents: 'none'
        });
        $editor.append($n);
        setTimeout(function () { $n.fadeOut(400, function () { $n.remove(); }); }, 4500);
    }

    function compressImage(file, done) {
        var reader = new FileReader();
        reader.onload = function (e) {
            var img = new Image();
            img.onload = function () {
                var w = img.width, h = img.height;
                // Downscale if either dimension exceeds MAX_DIMENSION
                if (w > MAX_DIMENSION || h > MAX_DIMENSION) {
                    if (w >= h) { h = Math.round(h * MAX_DIMENSION / w); w = MAX_DIMENSION; }
                    else        { w = Math.round(w * MAX_DIMENSION / h); h = MAX_DIMENSION; }
                }
                var canvas = document.createElement('canvas');
                canvas.width = w; canvas.height = h;
                canvas.getContext('2d').drawImage(img, 0, 0, w, h);
                canvas.toBlob(function (blob) {
                    // Only use compressed version if it's actually smaller
                    if (!blob || blob.size >= file.size) { done(file, false); return; }
                    var name = file.name.replace(/\.[^.]+$/, '') + '.jpg';
                    done(new File([blob], name, { type: 'image/jpeg' }), true);
                }, 'image/jpeg', JPEG_QUALITY);
            };
            img.onerror = function () { done(file, false); };
            img.src = e.target.result;
        };
        reader.onerror = function () { done(file, false); };
        reader.readAsDataURL(file);
    }

    function uploadFile($note, file) {
        var form = new FormData();
        form.append('file', file);
        $.ajax({
            url: UPLOAD_URL,
            type: 'POST',
            data: form,
            processData: false,
            contentType: false,
            headers: { 'X-CSRFToken': getCsrf() },
            success: function (resp) {
                if (resp && resp.url) {
                    $note.summernote('insertImage', resp.url, file.name);
                }
            },
            error: function () {
                showNotice($note, 'Image upload failed.');
            }
        });
    }

    function handleUpload($note, files) {
        var toCompress = 0, compressed = 0;

        Array.from(files).forEach(function (file) {
            if (!file.type.startsWith('image/')) return;

            if (file.size > COMPRESS_THRESHOLD) {
                toCompress++;
                compressImage(file, function (result, wasCompressed) {
                    if (wasCompressed) compressed++;
                    uploadFile($note, result);
                    toCompress--;
                    if (toCompress === 0 && compressed > 0) {
                        showNotice($note, 'Image was compressed to fit the upload size limit.');
                    }
                });
            } else {
                uploadFile($note, file);
            }
        });
    }

    // Patch $.fn.summernote once, before django-summernote initialises editors
    if (!$.fn.summernote || $.fn.summernote._imgCompressPatch) return;

    var _orig = $.fn.summernote;
    $.fn.summernote = function (options) {
        var $note = this;
        if (options && typeof options === 'object') {
            options = $.extend(true, {}, options);
            if (!options.callbacks) options.callbacks = {};
            options.callbacks.onImageUpload = function (files) {
                handleUpload($note, files);
            };
        }
        return _orig.apply(this, arguments);
    };
    $.fn.summernote._imgCompressPatch = true;

}(window.jQuery || (window.django && window.django.jQuery)));
