(function($) {
    $.Local = function(options, inst_id) {
        this.instance_id = inst_id;
        this.options = options;
        this.store = [];
        this.setUpListeners();
    };

    $.Local.prototype.onLoad = function() {
        var self = this;
        if (localStorage) {
            this.store = JSON.parse(localStorage.getItem('annotations-local.' + self.options.object_source));
            if (this.store == null) {
                this.store = [];
            }
            return this.store;
        } else {
            return this.store;
        }
    };

    $.Local.prototype.setUpListeners = function() {
        var self = this;
        hxSubscribe('retrieveReplies', self.instance_id, function(_, annotation_id, callback) {
            console.log('retrieved');
            var filteredAnnotations = self.store.filter(function(ann) {
                if (ann.media == "comment"){
                    var found = false;
                    jQuery.each(ann.ranges, function(_, range) {
                        if (range.parent == annotation_id) {
                            found = true;
                        }
                    })
                    if (found) {
                        return ann;
                    }
                }
            });
            callback(filteredAnnotations);
        });
    };

    $.Local.prototype.saveAnnotation = function(ann_to_save, elem) {
        var annotation = ann_to_save;
        var self = this;
        self.elem = elem;
        self.store = self.store.filter(function(ann) {
            if (annotation.id !== ann.id) {
                return ann;
            }      
        });
        
        self.store.push(annotation);
        
        self.storeCurrent();       
    };

    $.Local.prototype.deleteAnnotation = function(ann_to_delete, elem) {
        var self = this;
        var annotation = ann_to_delete.annotation;
        self.elem = elem;

        self.store = self.store.filter(function(ann) {
            if (annotation.id !== ann.id) {
                return ann;
            }      
        });
        self.storeCurrent();
    };

    $.Local.prototype.storeCurrent = function() {
        var self = this;
        var toSave = self.store.map(function(anno) {
            var ann = jQuery.extend({}, anno);
            if (!ann.serialized && ann.media !== "comment") {
                ann.ranges = self.serializeRanges(ann.ranges);
                ann.serialized = true;
            }
            delete ann._local;
            return ann;
        });
        localStorage.setItem('annotations-local.' + self.options.object_source, JSON.stringify(toSave));
    };

    $.Local.prototype.serializeRanges = function(ranges) {
        var self = this;
        if (ranges.length < 1) {
            return {
                ranges: []
            };
        }
        var text = [],
            serializedRanges = [],
            previous = "",
            next = "",
            extraRanges = [],
            contextEl = self.elem[0];

        for (var i = 0, len = ranges.length; i < len; i++) {
            text = [];
            var r = ranges[i];
            text.push(trim(r.text()));

            previous = ranges[i]['start']['previousSibling'] ? ranges[i]['start']['previousSibling'].textContent : '';
            next = ranges[i]['end']['nextSibling'] ? ranges[i]['end']['nextSibling'].textContent: '';

            var exact = text.join(' / ');
            var exactFullStart = jQuery(contextEl).text().indexOf(exact);
            var fullTextRange = {
                startOffset: exactFullStart,
                endOffset: exactFullStart + exact.length,
                exact: exact.replace('*',''),
                prefix: previous.substring(previous.length-20, previous.length).replace('*', ''),
                suffix: next.substring(0, 20).replace('*', '')
            };

            extraRanges.push(fullTextRange);
            serializedRanges.push(r.serialize(contextEl, '.annotator-hl'));
        }
        return serializedRanges;
    };
}(Hxighlighter));