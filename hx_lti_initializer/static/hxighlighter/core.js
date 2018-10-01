/**
 * 
 */

(function($) {

    $.Core = function(options, inst_id) {
        
        // options and instance ids are saved
        this.options = options;
        this.instance_id = inst_id;

        // keeps track of viewer/plugin modules for UI
        this.viewers = [];
        this.disabledViewers = [];
        this.plugins = [];
        this.disabledPlugins = [];

        // keeps track of annotations and storage modules for backend
        this.annotations = [];
        this.storage = [];
        this.disabledStorage;

        // initializes tool
        this.init(this.options.mediaType);
    };

    $.Core.prototype.init = function() {
        this.setUpViewers();
        this.setUpListeners();
        this.setUpStorage();
        this.setUpPlugins();
    };

    $.Core.prototype.setUpListeners = function() {
        var self = this;
        hxSubscribe('targetLoaded', self.instance_id, function(_, element) {
            // store element that contains target for easy retrieval
            self.element = element;
            jQuery.each(self.viewers, function(_, viewer) {
                viewer.element = element;
            });

            if (self.options.should_highlight) {
                self.initHighlighter();
                hxSubscribe('shouldHighlight', self.instance_id, function(_, annotation) {
                    if (annotation.media !== "comment") {
                        self.highlighter.draw(annotation);
                    }
                    self.annotationDrawn(annotation);
                });

                hxSubscribe('shouldUpdateHighlight', self.instance_id, function(_, annotation, isNew) {
                    if (annotation.media !== "comment") {
                        self.highlighter.redraw(annotation);
                    }
                    self.annotationDrawn(annotation);
                });

                hxSubscribe('shouldDeleteHighlight', self.instance_id, function(_, annotation) {
                    if (annotation.media !== "comment") {
                        self.highlighter.undraw(annotation);
                    }
                    self.annotationRemoved(annotation);
                });

                hxPublish('finishedHighlighterSetup', self.instance_id, []);
            }
        });

        hxSubscribe('selectAnnotation', self.instance_id, function(_, annotation) {
            self.selectedAnnotation = annotation;
        });

        hxSubscribe('editorShown', self.instance_id, function(_, editor, annotation) {
            self.editorShown(annotation, editor);
        });

        hxSubscribe('saveAnnotation', self.instance_id, function(_, annotation, text, isNew) {
            var updatedAnnotation = annotation;
            
            // all plugins have a chance to update the annotation before saving
            jQuery.each(self.plugins, function(_, plug) {
                updatedAnnotation = jQuery.extend({}, plug.saving(updatedAnnotation));
            });

            jQuery.each(self.storage, function(_, st) {
                st.saveAnnotation(updatedAnnotation, self.element);
            });

            hxPublish('shouldUpdateHighlight', self.instance_id, [updatedAnnotation, isNew]);
        });

        hxSubscribe('viewerShown', self.instance_id, function(_, annotations, viewer) {
            self.viewerShown(annotations, viewer);
        });

        hxSubscribe('deleteAnnotationById', self.instance_id, function(_, ann_id) {
            var found = self.getAnnotationById(ann_id);
            if (found) {
                hxPublish('shouldDeleteHighlight', self.instance_id, [found.annotation]);
                jQuery.each(self.storage, function(_, st) {
                    st.deleteAnnotation(found, self.element);
                });
            }
        });
    };

    $.Core.prototype.setUpViewers = function() {
        var self = this;
        var viewer;
        if (self.options.viewers.indexOf('floating') >= 0) {
            viewer = new Hxighlighter.FloatingViewer(self.options, self.instance_id);
            self.viewers.push(viewer);
        }

        if (self.options.viewers.indexOf('sidebar') >= 0) {
            viewer = new Hxighlighter.Sidebar(self.options, self.instance_id);
            self.viewers.push(viewer);
        }
    };

    $.Core.prototype.setUpStorage = function() {
        var self = this;
        if (self.options.storageOptions.backend.indexOf('catchpy') > -1) {
            // hxLogging('Connecting to external catchpy database');
            self.storage.push(new Hxighlighter.CatchPy(self.options, self.instance_id));
        }
        if (self.options.storageOptions.backend.indexOf('backup') > -1) {
            // hxLogging('Setting up backup feature using browser localStorage');
            // var backup1 = new Hxighlighter.Backup(self.options.storageOptions, self.instance_id);
        }
        if (self.options.storageOptions.backend.indexOf('local') > -1) {
            // hxLogging('Setting up temporary storage, usually reserved for demos or exporting');
            self.storage.push(new Hxighlighter.Local(self.options, self.instance_id));
        }

        hxSubscribe('finishedHighlighterSetup', self.instance_id, function(_) {
            var all_annotations = [];
            jQuery.each(self.storage, function(_, store) {
                var anns = store.onLoad() || [];
                jQuery.each(anns, function(_, ann) {
                    hxPublish('shouldHighlight', self.instance_id, [ann]);
                });
                all_annotations = all_annotations.concat(anns);
            });

            jQuery.each(self.viewers, function(_, viewer) {
                if (viewer.onLoad) {
                    viewer.onLoad(all_annotations);
                }
            });
        });
    };

    $.Core.prototype.setUpPlugins = function() {
        var self = this;
        if (typeof self.options.plugins !== undefined) {
            jQuery.each(self.options.plugins, function(pluginName, pluginOptions) {
                if (typeof window[pluginName] === "function") {
                    var plugin = new window[pluginName](pluginOptions, self.instance_id);
                    plugin.annotationListeners();
                    self.plugins.push(plugin);
                } else {
                    // hxLogging('Plugin "' + pluginName + '" was not loaded. Make sure the JavaScript and CSS files are included in this page.', 'error');
                }
            });
        }
    };

    $.Core.prototype.annotationDrawn = function(annotation) {
        var self = this;
        jQuery.each(self.plugins, function (_, plug) {
            if (typeof plug.annotationDrawn === "function") {
                plug.annotationDrawn(annotation);
            }
        });

        var ann_id = annotation.id;
        var found = self.getAnnotationById(ann_id);
        if (found) {
            self.annotations.splice(found.index, 1);
        }
        self.annotations.push(annotation);
        
    };

    $.Core.prototype.annotationRemoved = function(annotation) {
        var self = this;
        var ann_id = annotation.id;
        self.removeAnnotationById(ann_id);
    };

    $.Core.prototype.getAnnotationById = function(ann_id) {
        var self = this;
        var found;
        jQuery.each(self.annotations, function(index, ann) {
            if (ann.id == ann_id) {
                found = {
                    index: index,
                    annotation: ann
                };
            }
        });

        return found;
    };

    $.Core.prototype.removeAnnotationById = function(ann_id) {
        var self = this;

        self.annotations = self.annotations.filter(function(ann) {
            return ann.id !== ann_id;
        });
    };

    $.Core.prototype.editorShown = function(annotation, editor) {
        
        var self = this;
        jQuery.each(self.plugins, function (_, plug) {
            if (typeof plug.editorShown === "function") {
                plug.editorShown(annotation, editor);
            }
        });
    };

    $.Core.prototype.viewerShown = function(annotations, viewer) {
        var self = this;
        jQuery.each(self.plugins, function (_, plug) {
            if (typeof plug.viewerShown === "function") {
                plug.viewerShown(annotations, viewer);
            }
        });
    };

    $.Core.prototype.initHighlighter = function() {
        var self = this;

        self.highlighter = new annotator.ui.highlighter.Highlighter(self.element[0]);

        var highlightTogglers = {
            'mouseover': 'show',
            'mouseleave': 'hide',
            'click': 'toggle'
        };

        jQuery.each(highlightTogglers, function(eventType, value) {
            self.element.on(eventType, '.annotator-hl', function(event) {
                var annotations = self.getAnnotationsFromElement(event);
                hxPublish('toggleViewer', self.instance_id, [event, value, annotations]);
            });
        });
    };

    $.Core.prototype.getAnnotationsFromElement = function(event) {
        return jQuery(event.target).parents('.annotator-hl').addBack().map(function(_, elem) {
            return jQuery(elem).data('annotation');
        }).toArray();
    };

    $.Core.prototype.disable = function(itemId, activeList, disabledList) {
        var self = this;
        var itemToDisable = undefined;
        var indexFound = undefined;
        for (var i = activeList.length - 1; i >= 0; i--) {
            if (activeList[i].name == itemId) {
                indexFound = i;
            }
        }
        if (indexFound) {
            var foundItem = activeList.splice(indexFound)[0];
            if (typeof(foundItem.disable) == "function") {
                foundItem.disable();
            }
            disabledList.push(foundItem);
        }
    };

    $.Core.prototype.enable = function(itemId, activeList, disabledList) {
        var self = this;
        var itemToDisable = undefined;
        var indexFound = undefined;
        for (var i = disabledList.length - 1; i >= 0; i--) {
            if (disabledList[i].name == itemId) {
                indexFound = i;
            }
        }
        if (indexFound) {
            var foundItem = disabledList.splice(indexFound)[0];
            if (typeof(foundItem.enable) == "function") {
                foundItem.enable();
            }
            activeList.push(foundItem);
        }
    };

    $.Core.prototype.disableViewer = function(viewerId) {
        var self = this;
        self.disable(viewerId, self.viewers, self.disabledViewers);
    };

    $.Core.prototype.disablePlugins = function(pluginId) {
        var self = this;
        self.disable(pluginId, self.plugins, self.disabledPlugins);
    };

    $.Core.prototype.disableStorage = function(storageId) {
        var self = this;
        self.disable(storageId, self.storage, self.disabledStorage);
    };

    $.Core.prototype.enableViewer = function(viewerId) {
        var self = this;
        self.enable(viewerId, self.viewers, self.disabledViewers);
    };

    $.Core.prototype.enablePlugins = function(pluginId) {
        var self = this;
        self.enable(pluginId, self.plugins, self.disabledPlugins);
    };

    $.Core.prototype.enableStorage = function(storageId) {
        var self = this;
        self.enable(storageId, self.storage, self.disabledStorage);
    };

}(Hxighlighter));