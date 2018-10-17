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
            url: this.url_base + '/search?resource_link_id=' + self.options.storageOptions.database_params.resource_link_id,
            method: 'GET',
            data: {
                limit: -1,
                offset: 0,
                uri: this.options.object_id,
                context_id: this.options.context_id,
                collection_id: this.options.collection_id,
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
        var save_ann = self.convertToWebAnnotation(ann_to_save, elem)
        console.log(save_ann)
        jQuery.ajax({
            url: this.url_base + '/create?resource_link_id=' + self.options.storageOptions.database_params.resource_link_id,
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(save_ann),
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
            '@id': annotation['id'],
            'creator':  {
                'id': self.options.user_id,
                'name': this.options.username,
            },
            'permissions': {
                'can_read': [this.options.user_id],
                'can_update': [this.options.user_id],
                'can_delete': [this.options.user_id],
                'can_admin': [this.options.user_id],
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
                    'value': annotation.annotationText,
                    'purpose': 'commenting'
                }].concat(tags),
            },
            'target': {
                'type': 'List',
                'items': [{
                    'source': 'http://sample.com/fake_content/preview',
                    'type': this.options.mediaType.charAt(0).toUpperCase() + this.options.mediaType.slice(1),
                    'selector': {
                        'type': 'Choice',
                        'items': [{
                                'type': 'RangeSelector',
                                'start': {
                                    'type': 'XPathSelector',
                                    'value': serializedRanges.serial[0].start
                                },
                                'end': {
                                    'type': 'XPathSelector',
                                    'value': serializedRanges.serial[0].end,
                                },
                                'refinedBy': {
                                    'type': 'TextPositionSelector',
                                    'start': serializedRanges.serial[0].startOffset,
                                    'end': serializedRanges.serial[0].endOffset,
                                }
                            }, {
                                'type': 'TextPositionSelector',
                                'start': serializedRanges.extra[0].startOffset,
                                'end': serializedRanges.extra[0].endOffset,
                            }, {
                                'type': 'TextQuoteSelector',
                                'exact': serializedRanges.extra[0].exact,
                                'prefix': serializedRanges.extra[0].prefix,
                                'suffix': serializedRanges.extra[0].suffix
                        }],
                    }
                }],
            }
        };
        return webAnnotationVersion;
    };

    // $.CatchPy.prototype.convertFromWebAnnotation = function(webAnn, elem) {
    //     // var self = this;
    //     // var annotation = {
    //     //     annotationText: self.getAnnotationText(),
    //     //     created: self.getAnnotationCreated(),
    //     //     creator: self.getAnnotationCreator(),
    //     //     exact: [],
    //     //     id: ""
    //     //     media: "".
    //     //     tags: [],
    //     // }

    // };

    // $.CatchPy.prototype.getAnnotationText = function(webAnn) {
    //     try() {
    //         return webAnn['body'][0].value;
    //     } catch(e) {
    //         return "";
    //     }
    // }

    // $.CatchPy.prototype.getAnnotationCreated = function(webAnn) {
    //     try() {
    //         return Data.parse(webAnn['created']);
    //     } catch(e) {
    //         return new Date();
    //     }
    // }

    // $.CatchPy.prototype.getAnnotationCreator = function(webAnn) {
    //     try() {
    //         return webAnn['creator'];
    //     } catch(e) {
    //         return {username:'Unknown', id:'error'};
    //     }
    // };

    // $.CatchPy.prototype.getAnnotationExact = function(webAnn) {
    //     try() {
    //         return webAnn['target'][0].value;
    //     } catch(e) {
    //         return "";
    //     }
    // }

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