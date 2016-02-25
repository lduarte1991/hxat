// ----------------Plugin for Annotator to setup videojs---------------- //

Annotator.Plugin.VideoJS = (function(_super) {
    __extends(VideoJS, _super);

    // constructor
    function VideoJS() {
        this.pluginSubmit = __bind(this.pluginSubmit, this);
        _ref = VideoJS.__super__.constructor.apply(this, arguments);
        this.__indexOf = [].indexOf || function(item) { 
            for (var i = 0, l = this.length; i < l; i++) { 
                if (i in this && this[i] === item) 
                    return i; 
            } 
            return -1; 
        };
        return _ref;
    };

    VideoJS.prototype.field = null;
    VideoJS.prototype.input = null;

    VideoJS.prototype.pluginInit = function() {
        //console.log("VideoJS-pluginInit");
        // Check that annotator is working
        if (!Annotator.supported()) {
            return;
        }
        
        // -- Editor
        this.field = this.annotator.editor.addField({
            id: 'vjs-input-rangeTime-annotations',
            type: 'input', // options (textarea, input, select, checkbox)
            submit: this.pluginSubmit,
            EditVideoAn: this.EditVideoAn
        });
        
        // Modify the element created with annotator to be an invisible span
        var select = '<li><span id="vjs-input-rangeTime-annotations"></span></li>';
        var newfield = Annotator.$(select);
        Annotator.$(this.field).replaceWith(newfield);
        this.field = newfield[0];
        
        // -- Listener for Open Video Annotator
        this.initListeners();
        
        return this.input = $(this.field).find(':input');
    };
    

    // New JSON for the database
    VideoJS.prototype.pluginSubmit = function(field, annotation) {
        console.log("Plug-pluginSubmit");
        // Select the new JSON for the Object to save
        if (this.EditVideoAn()) {
            var annotator = this.annotator;
            var index = annotator.editor.VideoJS;
            var player = AController.targetObjectController.vid;//annotator.mplayer[index];
            var rs = player.rangeslider;
            var time = rs.getValues();
            var isYoutube = (player && typeof player.techName !== 'undefined') ? (player.techName === 'Youtube') : false;
            var isNew = typeof annotation.media === 'undefined';
            var ext;
            var type = player.options_.sources[0].type.split("/") || "";
            
            if (isNew) 
                annotation.media = typeof type[0] !== 'undefined' ? type[0] : "video"; // - media (by default: video)
            
            annotation.target = annotation.target || {}; // - target
            annotation.target.container = player.id_ || ""; // - target.container
            annotation.target.src = player.options_.sources[0].src || ""; // - target.src (media source)
            ext = (player.options_.sources[0].src.substring(player.options_.sources[0].src.lastIndexOf("."))).toLowerCase(); 
            ext = isYoutube ? 'Youtube' : ext; // The extension for youtube
            annotation.target.ext = ext || ""; // - target.ext (extension)
            annotation.rangeTime =     annotation.rangeTime || {};    // - rangeTime
            annotation.rangeTime.start = time.start || 0; // - rangeTime.start
            annotation.rangeTime.end = time.end || 0; // - rangeTime.end
            annotation.updated = new Date().toISOString(); // - updated
            if (typeof annotation.created === 'undefined')
                annotation.created = annotation.updated; // - created
            
            // show the new annotation
            var eventAn = isNew ? "annotationCreated" : "annotationUpdated";
            function afterFinish(){
                player.annotations.showAnnotation(annotation);
                annotator.unsubscribe(eventAn, afterFinish);
            };
            annotator.subscribe(eventAn, afterFinish); // show after the annotation is in the back-end
        } else {
            if (typeof annotation.media === 'undefined')
                annotation.media = "text"; // - media
            
            annotation.updated = new Date().toISOString(); // - updated
            
            if (typeof annotation.created === 'undefined')
                annotation.created = annotation.updated; // - created
        }
        return annotation.media;
    };
    
    
    // ------ Methods    ------ //
    // Detect if we are creating or editing a video-js annotation
    VideoJS.prototype.EditVideoAn =  function () {
        var wrapper = $('.annotator-wrapper').parent()[0];
        var annotator = window.annotator = $.data(wrapper, 'annotator');
        var isOpenVideojs = (typeof AController.targetObjectController.vid !== 'undefined');
        return (isOpenVideojs && typeof VideoJS !== 'undefined');
    };
    
    
    // Detect if the annotation is a video-js annotation
    VideoJS.prototype.isVideoJS = function (an) {
        var wrapper = $('.annotator-wrapper').parent()[0];
        var annotator = window.annotator = $.data(wrapper, 'annotator');
        var rt = an.rangeTime;
        var isOpenVideojs = (typeof AController.targetObjectController.vid !== 'undefined');
        var isVideo = (typeof an.media !== 'undefined' && (an.media === 'video' || an.media === 'audio'));
        var isNumber = (typeof rt !== 'undefined' && !isNaN(parseFloat(rt.start)) && isFinite(rt.start) && !isNaN(parseFloat(rt.end)) && isFinite(rt.end));
        return (isOpenVideojs && isVideo && isNumber);
    };
    
    // Delete Video Annotation
    VideoJS.prototype._deleteAnnotation = function(an) {
        var target = an.target || {};
        var container = target.container || {};
        var player = AController.targetObjectController.vid;
        
        var annotator = this.annotator;
        var annotations = annotator.plugins.Store.annotations;
        var tot = typeof annotations !== 'undefined' ? annotations.length : 0;
        var attempts = 0; // max 100
            
        // This is to watch the annotations object, to see when is deleted the annotation
        var ischanged = function() {
            var new_tot = annotator.plugins.Store.annotations.length;
            if (attempts < 100)
                setTimeout(function() {
                    if (new_tot !== tot) {
                        player.annotations.refreshDisplay(); // Reload the display of annotation
                    } else {
                        attempts++;
                        ischanged();
                    }
                }, 100); // wait for the change in the annotations
        };
        ischanged();
        
        player.rangeslider.hide(); // Hide Range Slider
    };
    
    
    // --Listeners
    VideoJS.prototype.initListeners = function () {
        var wrapper = $('.annotator-wrapper').parent()[0];
        var annotator = $.data(wrapper, 'annotator');
        var EditVideoAn = this.EditVideoAn;
        var isVideoJS = this.isVideoJS;
        var self = this;
            
        // local functions
        // -- Editor
        function annotationEditorHidden(editor) {
            if (EditVideoAn()){
                AController.targetObjectController.vid.rangeslider.hide(); // Hide Range Slider
                AController.targetObjectController.vid.annotations.refreshDisplay(); // Reload the display of annotations
            }
            annotator.unsubscribe("annotationEditorHidden", annotationEditorHidden);
        };
        function annotationEditorShown(editor, annotation) {
            AController.targetObjectController.vid.annotations.editAnnotation(annotation, editor);
            annotator.subscribe("annotationEditorHidden", annotationEditorHidden);
        };
        // -- Annotations
        function annotationDeleted(annotation) {
            
            if (isVideoJS(annotation))
                self._deleteAnnotation(annotation);
        };
        // -- Viewer
        function hideViewer(){
            AController.targetObjectController.vid.annotations.AnDisplay.onCloseViewer();
            annotator.viewer.unsubscribe("hide", hideViewer);
        };
        function annotationViewerShown(viewer, annotations) {
            
            var separation = viewer.element.hasClass(viewer.classes.invert.y) ? 5 : -5;
            var newpos = {
                top: parseFloat(viewer.element[0].style.top)+separation,
                left: parseFloat(viewer.element[0].style.left)
            };
            viewer.element.css(newpos);
            
            // Remove the time to wait until disapear, to be more faster that annotator by default
            viewer.element.find('.annotator-controls').removeClass(viewer.classes.showControls);
            
            annotator.viewer.subscribe("hide", hideViewer);
        };    
        
        // subscribe to Annotator
        annotator.subscribe("annotationEditorShown", annotationEditorShown)
            .subscribe("annotationDeleted", annotationDeleted)
            .subscribe("annotationViewerShown", annotationViewerShown);
    };
    return VideoJS;

})(Annotator.Plugin);