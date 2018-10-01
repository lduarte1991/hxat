/**
 * 
 */

(function($) {
    $.FloatingViewer = function(options, inst_id) {
        // sets default options
        var defaultOptions = {
            // set up template names that will be pulled
            TEMPLATENAMES: [
                "editor",
                "viewer",
            ],
            TEMPLATES: {},
            template_suffix: "v2",
            template_urls: ""
        };
        this.name = 'Floating';
        this.options = jQuery.extend({}, defaultOptions, options);
        this.instance_id = inst_id;
        this.annotation_tool = {
            interactionPoint: null,
            editing: false,
            editor: null,
            viewer: null
        };
        this.init();
    };

    $.FloatingViewer.prototype.init = function() {
        var self = this;
        switch(self.options.mediaType) {
            case 'text':
                // from Annotator v2.0 draws the button to make an annotation
                self.annotation_tool.adder = new annotator.ui.adder.Adder({
                    // if pserson clicks on the adder
                    onCreate: function(annotation) {
                        // the annotation is drawn to the page
                        //hxPublish('shouldHighlight', self.instance_id, [annotation]);

                        // clears the selection of the text
                        if (window.getSelection) {
                          if (window.getSelection().empty) {  // Chrome
                            window.getSelection().empty();
                          } else if (window.getSelection().removeAllRanges) {  // Firefox
                            window.getSelection().removeAllRanges();
                          }
                        } else if (document.selection) {  // IE?
                          document.selection.empty();
                        }

                        // signals that the editor should be shown
                        hxPublish('showEditor', self.instance_id, [annotation, self.annotation_tool.interactionPoint, false]);
                    }
                });

                // attaches the adder to the current dom instance
                self.annotation_tool.adder.attach();

                // loads all the annotations given a theme suffix
                self.setUpTemplates(self.options.template_suffix);

                break;
            case 'image':
                break;
            case 'video':
                break;
        }

        self.setUpListeners();
        self.setUpPinAndMove();
    };

    $.FloatingViewer.prototype.setUpTemplates = function (suffix) {
        var self = this;
        var deferreds = jQuery.map(self.options.TEMPLATENAMES, function (templateName){
            var options = {
                url: self.options.template_urls + templateName + '-' + suffix + '.html',
                type: "GET",
                contentType:"charset=utf-8",
                success: function (data) {
                    var template = _.template(data);
                    self.options.TEMPLATES[templateName] = template;
                },
                async: true
            };
            return jQuery.ajax(options);
        });

        jQuery.when.apply(jQuery, deferreds).done(function (){
            self.annotation_tool.editorTemplate = self.options.TEMPLATES.editor({
                editorid: self.instance_id.replace(/:/g, '-')
            });
        });
    };

    $.FloatingViewer.prototype.setUpListeners = function() {
        var self = this;

        hxSubscribe('selectionMade', self.instance_id, function(_, element, ranges, event) {
            if (self.annotation_tool.editing || (self.annotation_tool.viewer && self.annotation_tool.viewer.hasClass('static'))) {
                return;
            }
            var annotation = {
                annotationText: [],
                ranges: ranges,
                id: Hxighlighter.getUniqueId(),
                exact: getQuoteFromHighlights(ranges).exact,
                media: self.options.mediaType,
                created: new Date()
            };
            
            self.annotation_tool.interactionPoint = mouseFixedPosition(event);
            self.annotation_tool.adder.load(annotation, self.annotation_tool.interactionPoint);
            self.annotation_tool.adder.checkOrientation();

            hxPublish('selectAnnotation', self.instance_id, [annotation]);
        });

        hxSubscribe('rangesEmpty', self.instance_id, function(_) {
            if (self.annotation_tool && self.annotation_tool.adder) {
                self.annotation_tool.adder.hide();
            }
        });

        hxSubscribe('showEditor', self.instance_id, function(_, annotation, interactionPoint, updating) {
            // set editing mode
            self.annotation_tool.editing = true;
            self.annotation_tool.updating = updating;

            // actually set up and draw the Editor
            var wrapperElement = self.element.find('.annotator-wrapper');
            wrapperElement.append(self.annotation_tool.editorTemplate);

            // save the element to call upon later
            self.annotation_tool.editor = jQuery('#annotation-editor-' + self.instance_id.replace(/:/g, '-'));

            // situate it on its proper location
            self.annotation_tool.editor.css({
                'top': interactionPoint.top - jQuery(window).scrollTop(),
                'left': interactionPoint.left
            });

            // closes the editor tool and does not save annotation
            self.annotation_tool.editor.find('.cancel').click(function () {
                hxPublish('hideEditor', self.instance_id, [annotation, false, true]);
            });

            // closes the editor and does save annotations
            self.annotation_tool.editor.find('.save').click(function () {
                var text = annotator.util.escapeHtml(self.annotation_tool.editor.find('#annotation-text-field').val());

                hxPublish('saveAnnotation', self.instance_id, [annotation, text, !self.annotation_tool.updating]);
                hxPublish('hideEditor', self.instance_id, [annotation, false, false]);
            });

            self.checkOrientation(self.annotation_tool.editor);

            hxPublish('editorShown', self.instance_id, [self.annotation_tool.editor, annotation]);
        });

        // handles when the editor should be hidden
        hxSubscribe('hideEditor', self.instance_id, function (_, annotation, redraw, should_erase) {
            if (self.annotation_tool.editor) {
                self.annotation_tool.editor.remove();
            }
            self.annotation_tool.editing = false;
            if (redraw) {
                hxPublish('shouldUpdateHighlight', self.instance_id, [annotation]);
            } else if(!self.annotation_tool.updating && should_erase) {
                hxPublish('shouldDeleteHighlight', self.instance_id, [annotation]);
                self.annotation_tool.updating = false;
            } else if (!self.annotation_tool.updating && !should_erase) {
                self.annotation_tool.updating = false;
            }
            delete self.annotation_tool.editor;
            jQuery('body').css('overflow', 'inherit');
        });

        hxSubscribe('toggleViewer', self.instance_id, function(_, event, status, annotations) {
            self.toggleViewer(event, status, annotations);
        });
    };

    $.FloatingViewer.prototype.setUpPinAndMove = function() {
        var self = this;
        // keeps track of when mouse button is pressed
        jQuery('body').on('mousedown', function (event) {
            self.buttonDown = true;
        });

        // keeps track of when mouse button is let go
        jQuery('body').on('mouseup', function (event) {
            self.buttonDown = false;
        });

        // handles moving the editor by clicking and dragging
        jQuery('body').on('mousedown', '.annotation-editor-nav-bar', function (event){
            self.prepareToMove(true, event);
        });

        // handles moving the editor by clicking and dragging
        jQuery('body').on('mousedown', '.annotation-viewer-nav-bar', function (event){
            self.prepareToMove(false, event);
        });

        jQuery('body').on('mousemove', function (event){
            self.moving(event);
        });

        jQuery('body').on('mouseup', function (event){
           self.finishedMoving(event);
        });

        jQuery('body').on('mouseover', '.annotation-editor', function(event) {
            jQuery('body').css('overflow', 'hidden');
        });

        jQuery('body').on('mouseleave', '.annotation-editor', function(event) {
            jQuery('body').css('overflow', 'inherit');
        });

    };

    $.FloatingViewer.prototype.prepareToMove = function(isEditor, event) {
        var self = this;
        self.itemMoving = isEditor ? self.annotation_tool.editor : self.annotation_tool.viewer;

        if (self.itemMoving) {
            pauseEvent(event);

            //turns on moving mode
            self.itemMoving.moving = true;

            // set initial mouse position offset by where on the editor the user clicked
            var move = annotator.util.mousePosition(event);
            var editorTop = parseInt(self.itemMoving.css('top'), 10);
            var editorLeft = parseInt(self.itemMoving.css('left'), 10);
            self.itemMoving.offsetTopBy = move.top - editorTop;
            self.itemMoving.offsetLeftBy = move.left - editorLeft;
        }
    };

    $.FloatingViewer.prototype.moving = function(event) {
        var self = this;
        if (self.itemMoving && self.itemMoving.moving) {
            pauseEvent(event);

            // gets the userlocation (where they've dragged to)
            var move = annotator.util.mousePosition(event);

            // sets the editor to that location (fixing offset)
            self.itemMoving.css({
                top: move.top - self.itemMoving.offsetTopBy,
                left: move.left - self.itemMoving.offsetLeftBy
            });
        } else if(self.buttonDown && self.annotation_tool.viewer && !self.annotation_tool.viewer.hasClass('static')) {
            self.annotation_tool.viewer.remove();
        }
    };

    $.FloatingViewer.prototype.finishedMoving = function(event) {
        var self = this;
        if (self.itemMoving) {
            pauseEvent(event);

            //turns on moving mode
            self.itemMoving.moving = false;

            var move = annotator.util.mousePosition(event);
            self.annotation_tool.interactionPoint = {
                top: move.top - self.itemMoving.offsetTopBy,
                left: move.left - self.itemMoving.offsetLeftBy
            };
        }
    };

    $.FloatingViewer.prototype.checkOrientation = function(element) {
        var $win = jQuery(window),
            $widget = element,
            offset = $widget.offset(),
            viewport = {
                top: $win.scrollTop(),
                bottom: $win.height() + $win.scrollTop(),
                left: $win.scrollLeft(),
                right: $win.width() + $win.scrollLeft()
            },
            current = {
                top: offset.top,
                bottom: offset.top + $widget.outerHeight(),
                left: offset.left,
                right: offset.left + $widget.outerWidth()
            };

        if ((current.bottom - viewport.bottom) > 0) {
            if (current.top - $widget.outerHeight() - viewport.top > 0) {
                element.addClass('annotator-invert-y');
            }
        }

        if ((current.right - viewport.right) > 0) {
            element.addClass('annotator-invert-x');
        }

        return this;
    };

    $.FloatingViewer.prototype.toggleViewer = function(event, status, annotations) {
        var self = this;
        var hasStatic = self.annotation_tool.viewer && self.annotation_tool.viewer.hasClass('static');

        // if the timer is set for the tool to be hidden, this intercepts it
        if (self.hideTimer !== undefined) {
            clearTimeout(self.hideTimer);
        }

        if (hasStatic && !jQuery(self.annotation_tool.viewer).is(':visible')) {
            self.annotation_tool.viewer.removeClass('static');
            self.toggleViewer(event, 'show', annotations);
        }

        if (!jQuery(self.annotation_tool.viewer).is(':visible') && status == 'toggle') {
            self.toggleViewer(event, 'show', annotations);
        }

        self.annotation_tool.interactionPoint = mouseFixedPosition(event);
        

        // show viewer when hovered over it
        if (!self.annotation_tool.editing && status === "show") {
            if (hasStatic && jQuery(self.annotation_tool.viewer).is(':visible')) {return;}
            self.deemphasizeAll();

            self.emphasizeAnnotations(annotations);

            self.annotation_tool.annotations = jQuery.extend(true, [], annotations);

            // load templates with annotations
            var template_to_use = 'viewer';
            self.annotation_tool.viewerTemplate = self.options.TEMPLATES[template_to_use]({
                'viewerid': self.instance_id.replace(/:/g, '-'),
                'annotations': self.annotation_tool.annotations
            });

            // add the viewer to the DOM
            self.element.find('.annotator-wrapper').append(self.annotation_tool.viewerTemplate);

            // collect the object for manipulation and coordinates of where it should appear
            if (self.annotation_tool.viewer) {
                self.annotation_tool.viewer.remove();
            }
            self.annotation_tool.viewer = jQuery('#annotation-viewer-' + self.instance_id.replace(/:/g, '-'));
            self.annotation_tool.viewer.css({
                'top': annotator.util.mousePosition(event).top - jQuery(window).scrollTop(),
                'left': annotator.util.mousePosition(event).left + 30
            });

            self.annotation_tool.viewer.data('annotations', annotations);

            // close viewer when user hits cancel
            self.annotation_tool.viewer.find('.cancel').click(function (event1) {
                if (self.annotation_tool.viewer) {
                    jQuery('.annotation-viewer').remove();
                    delete self.annotation_tool.viewer;
                }
                hxPublish('toggleViewer',self.instance_id, [event1, 'hide', annotations]);
            });

            self.checkOrientation(self.annotation_tool.viewer);

            // make sure the viewer doesn't disappear when the person moves their mouse over it
            self.element.on('mouseover', '.annotation-viewer', function (event1) {
                clearTimeout(self.hideTimer);

                // lock the parent window's scrolling so when they scroll past the end it doesn't
                // trigger the scrolling of the parent window by accident
                jQuery('body').css('overflow', 'hidden');
            });

            // once they leave the viewer hide it
            self.element.on('mouseleave', '.annotation-viewer', function (event1) {
                clearTimeout(self.hideTimer);
                // if they leave the viewer, but they've locked it open, ignore it
                if (!self.annotation_tool.viewer.hasClass('static')) {
                    hxPublish('toggleViewer', self.instance_id, [event1, 'hide', annotations]);
                }

                // once the mouse leaves the viewer area then allow the parent window to scroll
                jQuery('body').css('overflow', 'inherit');
            });

            self.element.find('.annotation-viewer .delete').confirm({
                title: 'Delete Annotation?',
                content: 'Would you like to delete your annotation? This is permanent.',
                buttons: {
                    confirm: function() {
                        var annotation_id = this.$target[0].id.replace('delete-', '');
                        hxPublish('deleteAnnotationById', self.instance_id, [annotation_id]);
                        if (self.annotation_tool.viewer) {
                            jQuery('.annotation-viewer').remove();
                            delete self.annotation_tool.viewer;
                        }
                        self.toggleViewer(event, 'hide', annotations);
                    },
                    cancel: function () {
                    }
                }
            });

            jQuery('.annotation-viewer .edit').click(function(event) {
                var id = jQuery(event.currentTarget).attr('id').replace('edit-', '');
                var found = undefined;
                jQuery.each(annotations, function(index, ann) {
                    if (ann.id === id) {
                        found = ann;
                    }
                });
                if (self.annotation_tool.viewer) {
                    jQuery('.annotation-viewer').remove();
                    delete self.annotation_tool.viewer;
                }
                self.toggleViewer(event, 'hide', annotations);
                hxPublish('showEditor', self.instance_id, [found, self.annotation_tool.interactionPoint, true]);
            });

            hxPublish('viewerShown', self.instance_id, [annotations, self.annotation_tool.viewer]);
        } else if (!self.annotation_tool.editing && status === "hide") {
            if (self.annotation_tool.viewer && self.annotation_tool.viewer.hasClass('static')) {return;}
            self.hideTimer = setTimeout(function () {
                self.deemphasizeAnnotations(annotations);
                if (self.annotation_tool.viewer) {
                    self.annotation_tool.viewer.removeClass('static');
                    self.annotation_tool.viewer.remove();
                    delete self.annotation_tool.viewer;
                }
                jQuery('body').css('overflow', 'inherit');
            }, 250);


        } else if (!self.annotation_tool.editing && status === "toggle") {

            // makes the viewer not move when hovering over something
            if (self.annotation_tool.viewer) { self.annotation_tool.viewer.addClass('static'); }
        }
    };

    $.FloatingViewer.prototype.colorAnnotationsDefault = function() {
        var self = this;
        jQuery.each(jQuery(self.element).find('.annotator-hl'), function(_, highlight) {
            jQuery(highlight).css('background', 'rgba(255, 255, 10, 0.3)');
        });
    };

    $.FloatingViewer.prototype.colorAnnotations = function(color, annotations) {
        var self = this;
        jQuery.each(annotations, function(_, ann) {
            jQuery.each(ann._local['highlights'], function(_, highlight) {
                jQuery(highlight).css('background', color);
            });
        });
    };

    $.FloatingViewer.prototype.emphasizeAnnotations = function(annotations) {
        jQuery.each(annotations, function(_, ann) {
            jQuery.each(ann._local['highlights'], function(_, highlight) {
                var changedColor = jQuery(highlight).css('background').replace('.3', '.6');
                jQuery(highlight).css('background', changedColor);
            });
        });
    };

    $.FloatingViewer.prototype.deemphasizeAnnotations = function(annotations) {
        jQuery.each(annotations, function(_, ann) {
            jQuery.each(ann._local['highlights'], function(_, highlight) {
                var changedColor = jQuery(highlight).css('background').replace('.6', '.3');
                jQuery(highlight).css('background', changedColor);
            });
        });
    };

    $.FloatingViewer.prototype.deemphasizeAll = function() {
        var self = this;
        jQuery.each(jQuery(self.element).find('.annotator-hl'), function(_, highlight) {
            var changedColor = jQuery(highlight).css('background').replace('.6', '.3');
            jQuery(highlight).css('background', changedColor);
        });
    };


}(Hxighlighter));