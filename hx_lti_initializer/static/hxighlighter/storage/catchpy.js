(function($) {
    $.CatchPy = function(options, inst_id) {
        this.options = options;
        this.instance_id = inst_id;
        this.store = [];
        this.url_base = options.storageOptions.external_url.catchpy;
    };


    $.CatchPy.prototype.onLoad = function(element) {
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
                jQuery.each(result.rows, function(_, ann) {
                    hxPublish('shouldUpdateHighlight', self.instance_id, [self.convertFromWebAnnotation(ann, element), false])
                });
            },
            error: function(xhr, status, error) {
                console.log(xhr, status, error);
            }
        });
    };

    $.CatchPy.prototype.saveAnnotation = function(ann_to_save, elem) {
        var self = this;
        var save_ann = self.convertToWebAnnotation(ann_to_save, elem)
        jQuery.ajax({
            url: self.url_base + '/create?resource_link_id=' + self.options.storageOptions.database_params.resource_link_id,
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
        var self = this;
        jQuery.ajax({
            url: self.url_base + '/delete/'+ann_to_delete.annotation['id']+'?catchpy=true&resource_link_id=' + self.options.storageOptions.database_params.resource_link_id,
            method: 'DELETE',
            headers: {
                'x-annotator-auth-token': self.options.storageOptions.token,
            },
            success: function(result) {
                console.log(result)
            }
        })
    };

    $.CatchPy.prototype.updateAnnotation = function(ann_to_update, elem) {
        var self = this;
        var save_ann = self.convertToWebAnnotation(ann_to_update, elem)
        jQuery.ajax({
            url: self.url_base + '/update/'+ann_to_update.id+'?resource_link_id=' + self.options.storageOptions.database_params.resource_link_id,
            method: 'PUT',
            contentType: 'application/json',
            data: JSON.stringify(save_ann),
            headers: {
                'x-annotator-auth-token': self.options.storageOptions.token,
            },
            success: function(result) {
                console.log(result)
            }
        })
    };

    $.CatchPy.prototype.convertToWebAnnotation = function(annotation, elem) {
        var self = this;

        var tags = []
        jQuery.each(annotation.tags, function(_, t) {
            var t_el = {
                'type': 'TextualBody',
                'value': t,
                'purpose': 'tagging'
            };
            tags.push(t_el);
        })
        var serializedRanges = self.serializeRanges(annotation.ranges, elem);
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
                'can_read': [],
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

    $.CatchPy.prototype.convertFromWebAnnotation = function(webAnn, element) {
        var self = this;
        var annotation = {
            annotationText: self.getAnnotationText(webAnn),
            created: self.getAnnotationCreated(webAnn),
            creator: self.getAnnotationCreator(webAnn),
            exact: self.getAnnotationExact(webAnn),
            id: self.getAnnotationId(webAnn),
            media: self.options.mediaType,
            tags: self.getAnnotationTags(webAnn),
            ranges: self.getAnnotationTarget(webAnn, element),
        }
        return annotation;
    };

    $.CatchPy.prototype.getAnnotationTargetItems = function(webAnn) {
        try {
            return webAnn['target']['items'][0]['selector']['items'];
        } catch(e) {
            console.log(e);
            return [];
        }
    }

    $.CatchPy.prototype.getAnnotationTarget = function(webAnn, element) {
        var self = this;
        try {
            var ranges = []
            jQuery.each(this.getAnnotationTargetItems(webAnn), function(_, targetItem) {
                
                if (targetItem['type'] == "RangeSelector") {
                    ranges.push({
                        start: targetItem['oa:start'].value,
                        startOffset: targetItem['refinedBy'][0].start,
                        end: targetItem['oa:end'].value,
                        endOffset: targetItem['refinedBy'][0].end
                    });
                } else {
                    return [];
                }
            });
            return self.normalizeRanges(ranges, element);
        } catch(e) {
            console.log(e);
            return []
        }
    };

    $.CatchPy.prototype.getAnnotationText = function(webAnn) {
        try {
            return webAnn['body']["items"][0].value;
        } catch(e) {
            return "";
        }
    }

    $.CatchPy.prototype.getAnnotationCreated = function(webAnn) {
        try {
            return Data.parse(webAnn['created']);
        } catch(e) {
            return new Date();
        }
    }

    $.CatchPy.prototype.getAnnotationCreator = function(webAnn) {
        try {
            return webAnn['creator'];
        } catch(e) {
            return {username:'Unknown', id:'error'};
        }
    };

    $.CatchPy.prototype.getAnnotationExact = function(webAnn) {
        try {
            var quote = '';
            jQuery.each(this.getAnnotationTargetItems(webAnn), function(_, targetItem) {
                
                if (targetItem['type'] == "TextQuoteSelector") {
                    quote += targetItem['exact'];
                } else {
                    return '';
                }
            });
            return quote;
        } catch(e) {
            return "";
        }
    };

    $.CatchPy.prototype.getAnnotationId = function(webAnn) {
        try {
            return webAnn['id'];
        } catch(e) {
            return "";
        }
    };


    $.CatchPy.prototype.getAnnotationTags = function(webAnn) {
        // try {
        //     var tags = [];
        //     jQuery(webAnn['body']['items'])
        // } catch(e) {
            return [];
        // }
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
            if (r.text !== undefined) {
                text.push(trim(r.text()));
            } else {
                text.push(trim(self.text(r)));
            }
            try {
                previous = ranges[i]['start']['previousSibling'] ? ranges[i]['start']['previousSibling'].textContent : '';
                next = ranges[i]['end']['nextSibling'] ? ranges[i]['end']['nextSibling'].textContent: '';
            } catch(e) {
                previous = ranges[i]['startContainer']['previousSibling'] ? ranges[i]['startContainer']['previousSibling'].textContent : '';
                next = ranges[i]['endContainer']['nextSibling'] ? ranges[i]['endContainer']['nextSibling'].textContent: '';
            }

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

    $.CatchPy.prototype.normalizeRanges = function(ranges, elem) {
        var self = this;

        var normalizedRanges = [];

        jQuery.each(ranges, function(_, range) {
            var startElement = self.getElementViaXpath(range.start, elem);
            var endElement = self.getElementViaXpath(range.end, elem);

            var startNodes = self.getTextNodes(jQuery(startElement));
            var endNodes = self.getTextNodes(jQuery(endElement));
            var startNode = undefined;
            var endNode = undefined;
            var offs = range.startOffset;
            jQuery.each(startNodes, function(_, node) {
                if (offs > node.length) {
                    offs -= node.length;
                } else {
                    startNode = node;
                    return false;
                }
            });
            var startOffset = offs;
            offs = range.endOffset;
            jQuery.each(endNodes, function(_, node) {
                if (offs > node.length) {
                    offs -= node.length;
                } else {
                    endNode = node;
                    return false;
                }
            });
            var endOffset = offs;

            var normalizedRange = document.createRange();
            normalizedRange.setStart(startNode, startOffset);
            normalizedRange.setEnd(endNode, endOffset);
            normalizedRanges.push(annotator.range.sniff(normalizedRange).normalize(elem));
        });

        return normalizedRanges;
    };

    $.CatchPy.prototype.getElementViaXpath = function(xpath, rootElem) {
        var res = document.evaluate('.' + xpath, jQuery(rootElem)[0], null, XPathResult.ANY_TYPE, null);
        return res.iterateNext();
    };

    $.CatchPy.prototype.contains = function(elem1, elem2) {
        if (document.compareDocumentPosition != null) {
        return a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_CONTAINED_BY;
      }
      return false;
    };

    $.CatchPy.prototype.flatten = function(array) {
        var flatten;
        flatten = function(ary) {
          var el, flat, _i, _len;
          flat = [];
          for (_i = 0, _len = ary.length; _i < _len; _i++) {
            el = ary[_i];
            flat = flat.concat(el && jQuery.isArray(el) ? flatten(el) : el);
          }
          return flat;
        };
        return flatten(array);
    };

    $.CatchPy.prototype.getTextNodes = function(nodeContainer) {
        var self = this;
        var getTextNodes;
        getTextNodes = function(node) {
          var nodes;
          if (node && node.nodeType !== 3) {
            nodes = [];
            if (node.nodeType !== 8) {
              node = node.lastChild;
              while (node) {
                nodes.push(getTextNodes(node));
                node = node.previousSibling;
              }
            }
            return nodes.reverse();
          } else {
            return node;
          }
        };
        return nodeContainer.map(function() {
          return self.flatten(getTextNodes(this));
        });
    };

    $.CatchPy.prototype.getTextNodesFromRange = function(node) {
      var end, start, textNodes, _ref;
      var self = this;
      textNodes = self.getTextNodes(jQuery(node.commonAncestorContainer));
      _ref = [textNodes.index(node.start), textNodes.index(node.end)], start = _ref[0], end = _ref[1];
      return jQuery.makeArray(textNodes.slice(start, +end + 1 || 9e9));
    };

    $.CatchPy.prototype.text = function(node) {
        var self = this;
          return ((function() {
            var _i, _len, _ref, _results;
            _ref = self.getTextNodesFromRange(node);
            _results = [];
            for (_i = 0, _len = _ref.length; _i < _len; _i++) {
              node = _ref[_i];
              _results.push(node.nodeValue);
            }
            return _results;
          }).call(this)).join('');
    }
}(Hxighlighter));