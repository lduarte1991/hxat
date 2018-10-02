/**
 * 
 */

(function($) {
    $.Sidebar = function(options, inst_id) {
        // sets default options
        var defaultOptions = {
            // set up template names that will be pulled
            TEMPLATENAMES: [
                "editor",
                "viewer",
                "annotationSection",
                "annotationItem"
            ],
            TEMPLATES: {},
            template_suffix: "side",
            template_urls: ""
        };
        this.name = 'Sidebar';
        this.options = jQuery.extend({}, defaultOptions, options);
        this.instance_id = inst_id;
        this.annotation_tool = {
            interactionPoint: null,
            editing: false,
            editor: null,
            viewer: null,
            annotations: []
        };
        this.init();
    };

    $.Sidebar.prototype.init = function() {
        var self = this;
        switch(self.options.mediaType) {
            case 'text':
                break;
            case 'image':
                break;
            case 'video':
                break;
        }
        self.setUpTemplates();
    };

    $.Sidebar.prototype.setUpTemplates = function () {
        var self = this;
        var deferreds = jQuery.map(self.options.TEMPLATENAMES, function (templateName){
            var options = {
                url: self.options.template_urls + templateName + '-' + self.options.template_suffix + '.html',
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
            self.setUpListeners();
            
        });
    };

    $.Sidebar.prototype.setUpListeners = function() {
        var self = this;
        if (!self.element) {
            hxSubscribe('targetLoaded', self.instance_id, function(_, element) {
                self.element = element;
                self.setUpSidebar();
                
            });
        } else {
            self.setUpSidebar();
        }

        hxSubscribe('selectionMade', self.instance_id, function(_, element, ranges, event){
            if (self.annotation_tool.editing) {
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

            self.currentSelection = annotation;
        });

        hxSubscribe('showReplyEditor', self.instance_id, function(_, annotation) {
            self.showEditor(annotation, false);
        });

        hxSubscribe('shouldUpdateHighlight', self.instance_id, function(_, annotation, isNew) {
            if (annotation.media !== "comment") {
                if (!isNew) {
                    jQuery('.annotationItem.item-' + annotation.id).remove();
                    self.annotation_tool.annotations = self.annotation_tool.annotations.filter(function(ann) {
                        return ann.id !== annotation.id
                    });
                }
                jQuery('.annotationsHolder').prepend(self.options.TEMPLATES.annotationItem(jQuery.extend({}, annotation, {'index': 0})));
                hxPublish('viewerShown', self.instance_id, [[annotation], jQuery('.annotationItem.item-' + annotation.id)]);
                jQuery('#empty-alert').hide();
                self.element.find('.delete').confirm({
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
                        },
                        cancel: function () {
                        }
                    }
                });
                self.annotation_tool.annotations.push(annotation);
            }
        });

        hxSubscribe('shouldDeleteHighlight', self.instance_id, function (_, annotation) {
            jQuery('.annotationItem.item-' + annotation.id).remove();
            if (jQuery('.annotationItem').length == 0) {
                jQuery('#empty-alert').show();
            }
            self.annotation_tool.annotations = self.annotation_tool.annotations.filter(function(ann) {
                return ann.id !== annotation.id
            });
        });
    };

    $.Sidebar.prototype.setUpSidebar = function() {
        var self = this;
        self.element.append(self.options.TEMPLATES.annotationSection({
            'show_mynotes_tab': "True",
            'show_instructor_tab': "True",
            'show_public_tab': "True",
            'annotationItems': []
        }));

        self.element.on('mouseover', '.annotationsHolder', function(event) {
            jQuery('body').css('overflow', 'hidden');
        });

        self.element.on('mouseleave', '.annotationsHolder', function(event) {
            jQuery('body').css('overflow', 'inherit');
        });

        if (self.options.viewersOptions && self.options.viewersOptions['use_external_button']) {
            console.log(jQuery('.annotationSection.side #search'));
            jQuery('.annotationSection.side #search').parent().addClass('two-button-version');
        }

        if (self.options.viewersOptions && self.options.viewersOptions['sidebar_button_class']) {
            jQuery(self.options.viewersOptions['sidebar_button_class']).click(function() {
                if (jQuery('.annotationSection.side:visible').length > 0) {
                    jQuery('.annotationSection.side').hide();
                } else {
                    jQuery('.annotationSection.side').show();
                }
            }); 
        }

        // jQuery(window).on('scroll', function(event) {
        //     console.log(self.element);
        //     var slot =  self.element;
        //     var elementTop = jQuery(slot).offset().top;
        //     var elementBottom = elementTop + jQuery(slot).outerHeight();

        //     var viewTop = jQuery(window).scrollTop();
        //     var viewBottom = viewTop + jQuery(window).height();

        //     var sidebarHeight = viewBottom - viewTop;
        //     var encroachAmount = elementBottom - viewTop
        //     if (encroachAmount < sidebarHeight) {
        //         var amount = '-' + (sidebarHeight - encroachAmount) + 'px';
        //         jQuery('.annotationSection').css('top', amount);
        //     } else {
        //         jQuery('.annotationSection').css('top', '0');
        //     }

        //     console.log(elementTop, elementBottom, viewTop, viewBottom);
        // });


        self.element.on('click', '.annotationItem .edit', function(event) {
            var id = jQuery(event.currentTarget).attr('id').replace('edit-', '');
            var found = undefined;
            jQuery.each(self.annotation_tool.annotations, function(index, ann) {
                if (ann.id === id) {
                    found = ann;
                }
            });
            
            self.showEditor(found, true);
        });

        self.setUpButtons();
    };

    $.Sidebar.prototype.setUpButtons = function() {
        var self = this;
        self.element.on('click', '#create-annotation-side', function(event) {
            if (self.currentSelection) {
                hxPublish('shouldHighlight', self.instance_id, [self.currentSelection]);
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
                self.showEditor(self.currentSelection, false);
            }
        });

        self.element.on('click', '#search', function(event) {
            jQuery('.annotationsHolder').css('height', '100%');
            jQuery('.search-toggle').toggle();
            setTimeout(function() {
                if (jQuery('.search-toggle:visible').length > 0) {
                    jQuery('.annotationsHolder').css('height', 'calc(100% - 66px)');
                }
            }, 100);
        });

        self.element.on('click', '#search-clear', function(event) {
           jQuery('#srch-term').val('');
           jQuery('#search-submit').trigger('click');
           jQuery('#tag-search-alert').remove();
        });

        self.element.on('click', '#tag-search-alert', function(event) {
           jQuery('#search-clear').trigger('click');
        });

        self.element.on('keypress', '#srch-term', function(event) {
            var press = event.which || event.keyCode;
            if (press == 13) {
                jQuery('#search-submit').trigger('click');
            }
        });

        self.element.on('click', '.annotation-tag', function(event) {
            var filter = jQuery(this).text().trim();
            jQuery('#srch-term').val(filter);
            jQuery('.search-bar select').val('Tag');
            jQuery('#search-submit').trigger('click');
            jQuery('.search-bar').after("<div id='tag-search-alert'>You are currently viewing only annotations marked with the tag \""+filter +"\". Click this box to view all annotations.</div>")
        });

        self.element.on('click', '#search-submit', function(event) {
            jQuery('#tag-search-alert').remove();
            var query = jQuery('#srch-term').val();
            var type = jQuery('.search-bar select').val();
            var filteredAnnotations = self.annotation_tool.annotations;
            
            if(query.trim().length > 0) {
                if(type === "User") {
                    filteredAnnotations = self.annotation_tool.annotations.filter(function(ann) {
                        if (ann.username) {
                            return ann.username === query;
                        } else {
                            return false;
                        }
                    });
                } else if(type === "Annotation") {
                    filteredAnnotations = self.annotation_tool.annotations.filter(function(ann) {
                        return ann.annotationText.indexOf(query) > -1;
                    });
                } else if (type === "Tag") {
                    filteredAnnotations = self.annotation_tool.annotations.filter(function(ann) {
                        var found = false;
                        jQuery.each(ann.tags, function(_, tag) {
                            if (tag === query) {
                                found = true;
                            }
                        });
                        return found;
                    });
                }
            }

            var annotations_html = '';

            jQuery.each(filteredAnnotations, function(index, annotation) {
                var annotationItem = jQuery.extend({}, annotation, {'index': index});
                annotations_html += self.options.TEMPLATES.annotationItem(annotationItem);
            });

            jQuery('.annotationsHolder').html(annotations_html);
            hxPublish('viewerShown', self.instance_id, [self.annotation_tool.annotations, jQuery('.annotationsHolder')])
        });


        if (self.annotation_tool.annotations) {
            self.onLoad(self.annotation_tool.annotations);
        }
    };

    $.Sidebar.prototype.showEditor = function(annotation, updating) {
        var self = this;

        // set editing mode
        self.annotation_tool.editing = true;
        self.annotation_tool.updating = updating;

        self.element.append(self.annotation_tool.editorTemplate);

        // save the element to call upon later
        self.annotation_tool.editor = jQuery('#annotation-editor-' + self.instance_id.replace(/:/g, '-'));

        self.annotation_tool.editor.css({
            'position': 'fixed',
            'top': 0,
            'right': 0,
            'left': 'auto',
            'width': '400px',
            'height': '100%',
            'height': 'calc(100%)'
        });

        // closes the editor tool and does not save annotation
        self.annotation_tool.editor.find('.cancel').click(function () {
            self.hideEditor(annotation, false, true);
        });

        // closes the editor and does save annotations
        self.annotation_tool.editor.find('.save').click(function () {
            var text = annotator.util.escapeHtml(self.annotation_tool.editor.find('#annotation-text-field').val());

            hxPublish('saveAnnotation', self.instance_id, [annotation, text, !self.annotation_tool.updating]);
            self.hideEditor(annotation, false, false);
        });

        hxPublish('editorShown', self.instance_id, [self.annotation_tool.editor, annotation]);
    };

    $.Sidebar.prototype.hideEditor = function(annotation, redraw, should_erase) {
        var self = this;
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
    };

    $.Sidebar.prototype.onLoad = function(annotations1) {
        var self = this;
        var annotations = annotations1.sort(function compare(a, b) {
            var dateA = new Date(a.created);
            var dateB = new Date(b.created);
            return dateB > dateA;
        });

        if (annotations.length > 0) {
            jQuery('#empty-alert').remove();
        }

        if (self.options.TEMPLATES.viewer) {
            var annotations_html = '';

            jQuery.each(annotations, function(index, annotation) {
                if (annotation.media !== "comment") {
                    var annotationItem = jQuery.extend({}, annotation, {'index': index});
                    annotations_html += self.options.TEMPLATES.annotationItem(annotationItem);
                    self.annotation_tool.annotations.push(annotation)
                }
            });
            // var annotations_html = self.options.TEMPLATES.viewer({
            //     'viewerid': self.instance_id.replace(/:/g, '-'),
            //     'annotations': annotations
            // });
            jQuery('.annotationsHolder').append(annotations_html);
            self.element.find('.delete').confirm({
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
                    },
                    cancel: function () {
                    }
                }
            });
            hxPublish('viewerShown', self.instance_id, [annotations1, jQuery('.annotationsHolder')])
        } else {
            self.annotation_tool.annotations = annotations; 
        }
    };


}(Hxighlighter));