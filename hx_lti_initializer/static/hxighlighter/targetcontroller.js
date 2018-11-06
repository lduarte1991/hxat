/**
 * 
 */

(function($) {
    /**
     * @constructor
     * @param      {dict} <options> { Contains all the options for setting up target }
     * @param      {dict} <inst_id> { Contains the id for the appropriate instance }
     */
    $.Target = function(options, inst_id) {
        this.options = options;
        this.instance_id = inst_id;
        this.init();

        //hxLogging('Target for instance "' + inst_id + '" has been created.')
    };

    $.Target.prototype.init = function() {
        var self = this;
        self.setUpListeners();

        var media = self.options.mediaType;
        var target_selector = self.options.target_selector;

        switch(media) {
            case 'text':
                if (self.options.method == "url") {
                    self.makeQuery(self.options.object_source, self.createTextSlot, target_selector);
                } else if (self.options.method = "html") {
                    var guid = Hxighlighter.getUniqueId();
                    jQuery(target_selector).find('.annotation-slot').attr("id", guid);
                    jQuery(target_selector).find('.annotations-section').addClass('annotator-wrapper').removeClass('annotations-section');
                    setTimeout(function(){
                        hxPublish('targetLoaded', self.instance_id, [jQuery('#' + guid)]);
                    }, 1000);
                }
                break;
            case 'image':
                break;
            case 'video':
                break;
        }
    };

    $.Target.prototype.createTextSlot = function(content, selector, instance_id) {
        var guid = Hxighlighter.getUniqueId();
        // creates a new section given the data retrieved
        var slot = "<div class='annotation-slot' id='" + guid + "'>" + content + "</div>";
        
        // adds it to the page and turns on the wrapper
        jQuery(selector).append(slot);
        jQuery('.annotations-section').addClass('annotator-wrapper').removeClass('annotations-section');        
        hxPublish('targetLoaded', instance_id, [jQuery('#' + guid)]);
    };

     $.Target.prototype.makeQuery = function(url, callback, selector) {
        var self= this;
        var defer = jQuery.ajax({
            url: url,
            type: 'GET',
            contentType: 'charset=utf-8',
            success: function(data) {
                callback(data, selector, self.instance_id);
            },
            async: true
        });
        return defer;
    };

    $.Target.prototype.setUpSelector = function(element) {
        var self = this;

        if (self.options.mediaType === "text") {
            self.selector = new annotator.ui.textselector.TextSelector(element, {
                onSelection: function(ranges, event) {
                    // checks to make sure correct element is picked depending on mouse vs keyboard usage
                    var commonAncestor = event.type === "mouseup" || ranges.length === 0 ? jQuery(event.target) : jQuery(ranges[0].commonAncestor);
                    // checks to make sure event comes from the correct target object being selected
                    if(commonAncestor.closest('.annotator-wrapper').parent().attr('id') === element.id) {
                        if (ranges.length > 0) {
                            hxPublish('selectionMade', self.instance_id, [element, ranges, event]);
                        } else {
                            hxPublish('rangesEmpty', self.instance_id, []);
                        }
                    }
                }
            });
        }
    };

    $.Target.prototype.setUpListeners = function() {
        var self = this;
        hxSubscribe('targetLoaded', self.instance_id, function(_, element) {
            //annotation element gets data that may be needed later
            self.element = element;
            self.element.data('source', self.options.object_source);
            self.element.data('source_type', self.options.mediaType);

            // finish setting up selectors
            self.setUpSelector(self.element[0]);

            jQuery('#annotations-text-size-plus').click(function() {
                self.toggleTextSize(20);
            });
            jQuery('#annotations-text-size-minus').click(function() {
                self.toggleTextSize(-20);
            });
        });


    };

    $.Target.prototype.toggleTextSize = function(step) {
        var self = this;
        var $content = jQuery(self.element).find('.content');
        var fontsize = parseInt($content.data('textsize'), 10);
        step = step || 0;

        if (!fontsize) {
            fontsize = 100;
        }
        fontsize = (fontsize + step) + "%";
        $content.data('textsize', fontsize).css("font-size", fontsize);
    }

}(Hxighlighter))