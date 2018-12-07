(function($) {
    $.Accessibility = function(options, inst_id) {
        this.options = options;
        this.instance_id = inst_id;

        this.init(this.options.mediaType);
    };

    $.Accessibility.prototype.init = function(mediaType) {
        var self = this;
        if (mediaType == 'text') {
            self.keyinput = new HxKeyboardTextSelection(this.instance_id);
            self.keyinput.init(jQuery(self.options.element).find('.content'));

            jQuery('#keyboard-input-toggle-text').click(function(e) {
                jQuery('#annotations-status').trigger('click');
                self.keyinput.turnSelectionModeOn();
                self.compensateForNVDAACessKeyBug(e.target);
            });
        }

        self.setUpListeners();
    };

    $.Accessibility.prototype.compensateForNVDAACessKeyBug = function(element, delay = 50) {
        element.blur();
        setTimeout(function() {
            element.focus();
        }, delay);
    };

    $.Accessibility.prototype.setUpListeners = function() {
        var self = this;
        hxSubscribe('keyboardSelectionMade', self.instance_id, function(_, range) {
            var normalizedRange = annotator.range.sniff(range).normalize(self.options.element.find('.content'));
            var annotation = {
                annotationText: [],
                ranges: [normalizedRange],
                id: Hxighlighter.getUniqueId(),
                media: self.options.mediaType,
                created: new Date(),
                creator: {
                    name: self.options.username,
                    id: self.options.user_id
                },
                exact: normalizedRange.text(),
                tags: []
            }
            self.currentSelection = annotation;

            jQuery(self.options.element).prepend('<div id="keyboard-annotation-region"><label for="quote-to-be">Quote Being Annotated: </label><div id="quote-to-be">'+self.currentSelection.exact+'</div><label for="ann-text">Annotation for Selection:</label> <input id="ann-text" /> <br> <label for="ann-tags">Tags (separate tags with spaces):</label> <input id="ann-tags" /><br><button id="make-annotation-using-keyboard">Save Annotation</button><button id="cancel-annotation">Discard Annotation</button></div>');
        });

        jQuery(self.options.element).on('click', '#make-annotation-using-keyboard', function(){
            if (self.currentSelection) {
                self.currentSelection.annotationText = jQuery('#ann-text').val();
                var tagString = jQuery('#ann-tags').val();
                var tags = [];
                if (tagString.length > 0) {
                    tags = tagString.split(' ');
                }
                
                self.currentSelection.tags = tags;
                console.log(self.currentSelection);
                hxPublish('saveAnnotation', self.instance_id, [self.currentSelection, null, true]);
                self.currentSelection = undefined;
            }

            jQuery('#keyboard-annotation-region').remove();
        });

        jQuery(self.options.element).on('click', '#cancel-annotation', function(){
            self.currentSelection = undefined;
        });
    };
}(Hxighlighter));