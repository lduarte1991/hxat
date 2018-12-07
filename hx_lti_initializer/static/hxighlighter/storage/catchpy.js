(function($) {
    $.CatchPy = function(options, inst_id) {
        this.options = options;
        this.instance_id = inst_id;
        this.store = [];
        this.url_base = options.storageOptions.external_url.catchpy;
    };


    $.CatchPy.prototype.onLoad = function(element, opts) {
        var self = this;
        var callB = function(result) {
            jQuery.each(result.rows, function(_, ann) {
                var waAnnotation = self.convertFromWebAnnotation(ann, jQuery(element).find('.content'));
                setTimeout(function() {
                    hxPublish('shouldUpdateHighlight', self.instance_id, [waAnnotation, false])
                }, 250);
            });
        }
        self.search(opts, callB);
    };

    $.CatchPy.prototype.search = function(options, callBack) {
        var self = this;
        var data = jQuery.extend({}, {
            limit: -1,
            offset: 0,
            source_id: self.options.object_id,
            context_id: self.options.context_id,
            collection_id: self.options.collection_id,
        }, options);
        jQuery.ajax({
            url: self.url_base + '/search?resource_link_id=' + self.options.storageOptions.database_params.resource_link_id,
            method: 'GET',
            data: data,
            headers: {
                'x-annotator-auth-token': self.options.storageOptions.token,
            },
            success: function(result) {
                callBack(result);
            },
            error: function(xhr, status, error) {
                console.log(xhr, status, error);
                callBack([xhr, status, error]);
            }
        });

    }

    $.CatchPy.prototype.saveAnnotation = function(ann_to_save, elem) {
        var self = this;
        console.log(elem);
        var save_ann = self.convertToWebAnnotation(ann_to_save, jQuery(elem).find('.content'));
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
        var save_ann = self.convertToWebAnnotation(ann_to_update, jQuery(elem).find('.content'));
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

       
        var targetList = [];
        var source_id = this.options.object_id;
        var purpose = 'commenting';
        if (annotation.media === "Annotation") {
            jQuery.each(annotation.ranges, function(_, range){
                targetList.push({
                    'type': 'Annotation',
                    'source': range.parent
                })
                source_id = range.parent;
            });

            purpose = 'replying';
        } else {
            console.log(annotation.ranges);
            var serializedRanges = self.serializeRanges(annotation.ranges, elem);
            var mediatype = this.options.mediaType.charAt(0).toUpperCase() + this.options.mediaType.slice(1);
            jQuery.each(serializedRanges.serial, function(index, range){
                targetList.push({
                    'source': 'http://sample.com/fake_content/preview',
                    'type': mediatype,
                    'selector': {
                        'type': 'Choice',
                        'items': [{
                                'type': 'RangeSelector',
                                'start': {
                                    'type': 'XPathSelector',
                                    'value': range.start
                                },
                                'end': {
                                    'type': 'XPathSelector',
                                    'value': range.end,
                                },
                                'refinedBy': {
                                    'type': 'TextPositionSelector',
                                    'start': range.startOffset,
                                    'end': range.endOffset,
                                }
                            }, {
                                'type': 'TextPositionSelector',
                                'start': serializedRanges.extra[index].startOffset,
                                'end': serializedRanges.extra[index].endOffset,
                            }, {
                                'type': 'TextQuoteSelector',
                                'exact': serializedRanges.extra[index].exact,
                                'prefix': serializedRanges.extra[index].prefix,
                                'suffix': serializedRanges.extra[index].suffix
                        }],
                    }
                });
            });
        }

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
                'target_source_id': source_id,
            },
            'body': {
                'type': 'List',
                'items': [{
                    'type': 'TextualBody',
                    'format': 'text/html',
                    'language': 'en',
                    'value': annotation.annotationText,
                    'purpose': purpose
                }].concat(tags),
            },
            'target': {
                'type': 'List',
                'items': targetList
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
            media: self.getMediaType(webAnn),
            tags: self.getAnnotationTags(webAnn),
            ranges: self.getAnnotationTarget(webAnn, jQuery(element)),
            replyCount: webAnn.totalReplies,
        }
        console.log(annotation);
        return annotation;
    };

    $.CatchPy.prototype.getMediaType = function(webAnn, element) {
        return webAnn['target']['items'][0]['type'];
    };

    $.CatchPy.prototype.getAnnotationTargetItems = function(webAnn) {
        try {
            console.log("reached getAnnotationTargetItems", webAnn);
            if (webAnn['target']['items'][0]['type'] == "Annotation") {
                console.log([{'parent':webAnn['target']['items'][0]['source']}]);
                return [{'parent':webAnn['target']['items'][0]['source']}]
            }
            console.log("nope, something went wrong");
            return webAnn['target']['items'][0]['selector']['items'];
        } catch(e) {
            console.log(e);
            return [];
        }
    };

    $.CatchPy.prototype.getAnnotationTarget = function(webAnn, element) {
        var self = this;
        try {
            var ranges = []
            jQuery.each(this.getAnnotationTargetItems(webAnn), function(_, targetItem) {
                console.log('targetItem', targetItem);
                if (!('parent' in targetItem)) {
                    if (targetItem['type'] == "RangeSelector") {
                        ranges.push({
                            start: targetItem['oa:start'].value,
                            startOffset: targetItem['refinedBy'][0].start,
                            end: targetItem['oa:end'].value,
                            endOffset: targetItem['refinedBy'][0].end
                        });
                    }
                } else {
                    return ranges.push(targetItem)
                }
            });
            if (webAnn['target']['items'][0]['type'] == "Annotation") {
                return ranges;
            }
            console.log('getAnnotationTarget', ranges, element);
            return self.normalizeRanges(ranges, element);
        } catch(e) {
            console.log(e);
            return []
        }
    };

    $.CatchPy.prototype.getAnnotationText = function(webAnn) {
        try {
            var found = "";
            jQuery.each(webAnn['body']['items'], function(_, bodyItem) {
                if (bodyItem.purpose == "commenting") {
                    found = bodyItem.value;
                }
            });
            return found;
        } catch(e) {
            return "";
        }
    }

    $.CatchPy.prototype.getAnnotationCreated = function(webAnn) {
        try {
            return new Date(webAnn['created']);
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
        try {
            var tags = [];
            jQuery.each(webAnn['body']['items'], function(_, bodyItem) {
                if (bodyItem.purpose == "tagging") {
                    tags.push(bodyItem.value);
                }
            });
            return tags;
        } catch(e) {
            return [];
        }
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
            var foundRange = annotator.range.sniff(range);
            console.log(foundRange.normalize, JSON.stringify(elem));
            normalizedRanges.push(foundRange.normalize(elem[0]));
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