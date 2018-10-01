(function($) {
    $.CatchPy = function(options, inst_id) {
        this.options = options;
        this.instance_id = inst_id;
        this.store = [];
        this.url_base = options.storageOptions.external_url.catchpy;
        console.log(options);
    };


    $.CatchPy.prototype.onLoad = function() {
        var self = this;
        jQuery.ajax({
            url: this.url_base,
            method: 'GET',
            data: {
                limit: 10,
                offset: 0,
                userid: this.options.user_id,
                context_id: this.options.context_id,
                collection_id: this.options.collection_id
            },
            headers: {
                'x-annotator-auth-token': self.options.storageOptions.token,
            },
            success: function(result) {
                console.log(result);
            },
            error: function(xhr, status, error) {
                console.log(xhr, status, error);
            }
        });
    };

    $.CatchPy.prototype.saveAnnotation = function(ann_to_save, elem) {
        var self = this;
        console.log(ann_to_save);
        console.log(self.convertToWebAnnotation(ann_to_save, elem));
        // jQuery.ajax({
        //     url: this.url_base,
        //     method: 'POST',
        //     data: ann_to_save,
        //     headers: {
        //         'x-annotator-auth-token': self.options.storageOptions.token,
        //     },
        //     success: function(result) {
        //         console.log(result);
        //     },
        //     error: function(xhr, status, error) {
        //         console.log(xhr, status, error);
        //     }
        // });
    };

    $.CatchPy.prototype.deleteAnnotation = function(ann_to_delete, elem) {
        
    };

    $.CatchPy.prototype.convertToWebAnnotation = function(annotation, elem) {
        var self = this;

        var tags = []
        jQuery.each(annotation.tags, function(_, t) {
            var t_el = {
                'type': 'Tag',
                'value': t
            };
            tags.push(t_el);
        })
        var serializedRanges = self.serializeRanges(annotation.ranges, elem);
        console.log(serializedRanges);
        var webAnnotationVersion = {
            "@context": "http://catch-dev.harvardx.harvard.edu/catch-context.jsonld",
            'type': 'Annotation',
            'schema_version': '1.1.0',
            'creator':  {
                'id': self.options.user_id,
                'name': this.options.username,
            },
            'permissions': {
                'can_read': [],
                'can_update': [this.options.username],
                'can_delete': [this.options.username],
                'can_admin': [this.options.username],
            },
            'platform': {
                'platform_name': 'edX',
                'context_id': this.options.context_id,
                'collection_id': this.options.collection_id,
                'target_source_id': this.options.object_id,
            },
            'body': {
                'type': 'List',
                'items': [{
                    'type': 'TextualBody',
                    'format': 'text/html',
                    'language': 'en',
                    'value': annotation.annotationText
                }].concat(tags),
            },
            // 'target': {
            //     'type': 'List',
            //     'items': [{
            //         'source': 'http://sample.com/fake_content/preview',
            //         'type': this.options.mediaType,
            //         'selectors': {
            //             'type': 'List',
            //             'items': [{
            //                 'type': "Choice",
            //                 'items': [{
            //                     'type': 'RangeSelector',
            //                     'start': {
            //                         'type': 'XPathSelector',
            //                         'value': annotation.ranges[0].start,
            //                     },
            //                     'end': {
            //                         'type': 'XPathSelector',
            //                         'value': annotation.ranges[0].end,
            //                     },
            //                     'refinedBy': {
            //                         'type': 'TextPositionSelector',
            //                         'start': annotation.ranges[0].startOffset,
            //                         'end': annotation.ranges[0].endOffset,
            //                     }
            //                 }, {
            //                     'type': 'TextPositionSelector',
            //                     'start': annotation.fullTextRanges.startOffset,
            //                     'end': annotation.fullTextRanges.endOffset,
            //                 }, {
            //                     'type': 'TextQuoteSelector',
            //                     'exact': annotation.exact,
            //                     'prefix': annotation.prefix,
            //                     'suffix': annotation.suffix
            //                 }]
            //             }],
            //         }
            //     }],
            // }
        };
        return webAnnotationVersion;
    };

    $.CatchPy.prototype.storeCurrent = function() {
        
    };

    $.CatchPy.prototype.serializeRanges = function(ranges, elem) {
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
            contextEl = elem[0];

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
        return {
            serial: serializedRanges,
            extra: extraRanges
        }
    };
}(Hxighlighter));