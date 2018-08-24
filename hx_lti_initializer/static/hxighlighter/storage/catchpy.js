(function($) {
    $.CatchPy = function(options, inst_id) {
        this.options = options;
        this.instance_id = inst_id;
        this.store = [];
        console.log(options);
        this.url_base = options.storageOptions.external_url.catchpy;
    };


    $.CatchPy.prototype.onLoad = function() {
        console.log(this.url_base);
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
                'x-annotator-auth-token': "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3N1ZWRBdCI6IjIwMTgtMDgtMDJUMjA6MDY6MzErMDA6MDAiLCJjb25zdW1lcktleSI6IjE5NTJlZmEyLTlkYTMtNGE2My04ZjAwLWQwY2M2YTkyZmFjZiIsInVzZXJJZCI6ImEyMjNmYTQzNTkyZjNkYzgxYWJhZTI3ZDVjYmE5NjBmIiwidHRsIjo4NjQwMH0.BiFznIYK4Dvv5bhMKrXjvXyR03d2h_IWKBHWFuowBLk"
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
              
    };

    $.CatchPy.prototype.deleteAnnotation = function(ann_to_delete, elem) {
        
    };

    $.CatchPy.prototype.storeCurrent = function() {
        
    };

    $.CatchPy.prototype.serializeRanges = function(ranges) {
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