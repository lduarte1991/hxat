/**
 *  Colored Token Tags Plugin
 *  
 *  Should be generic, but its main purpose is to be used in tandem with annotations.
 *
 */

(function($){

    /**
     * @constructor
     * @params {Object} options - specific options for this plugin
     */
    $.Reply = function(options, instanceID) {
        this.options = jQuery.extend({}, options);
        this.init();
        this.instance_id = instanceID;
        return this;
    };

    /**
     * Initializes instance
     */
    $.Reply.prototype.init = function() {
    };

    $.Reply.prototype.returnValue = function() {
    };

    $.Reply.prototype.destroy = function(element, selector) {
    };

    // Annotation specific functions

    $.Reply.prototype.annotationListeners = function() {
        var self = this;
    };

    $.Reply.prototype.editorShown = function(annotation, editor) {
    };

    $.Reply.prototype.viewerShown = function(annotations, viewer) {
        var self = this;
        jQuery.each(annotations, function(_, annotation) {
            var reply_html = "<div class='reply-list-count-" + annotation.id + "'> <span class='glyphicon glyphicon-comment'></span>";
            if (typeof annotation.replyCount !== 'undefined') {
                reply_html += annotation.replyCount;
            } else {
                reply_html += " 0";
            }
            reply_html += "</div>";
            viewer.find('#annotation-' + annotation.id + ' .annotation-plugin-area-bottom').html(reply_html);
            viewer.find('.item-' + annotation.id + ' .annotation-plugin-area-bottom').html(reply_html);
            jQuery('.item-' + annotation.id + ' .annotation-plugin-area-bottom .reply-list-count-' + annotation.id).on('click', function() {
                self.retrieveReplies(annotation.id, this);
            });
            jQuery('#annotation-' + annotation.id + ' .annotation-plugin-area-bottom .reply-list-count-' + annotation.id).on('click', function() {
                self.retrieveReplies(annotation.id, this);
            });
        });
    };

    $.Reply.prototype.annotationDrawn = function(annotation) {
        var self = this;
        console.log(annotation);
        if (annotation.media == "comment") {
            var par = annotation.ranges[0].parent;
            jQuery('.item-' + par + ' .annotation-replies').append("<div class='reply-row reply-" + annotation.id + "'>" + annotation.annotationText + "</div>")
            return;
        }

        var reply_html = "<div class='reply-list-count-" + annotation.id + "'> <span class='glyphicon glyphicon-comment'></span>";
        if (typeof annotation.replyCount !== 'undefined') {
            reply_html += annotation.replyCount;
        } else {
            reply_html += " 0";
        }
        reply_html += "</div>";
        jQuery('.annotation-slot').find('#annotation-' + annotation.id + ' .annotation-plugin-area-bottom').html(reply_html);
        jQuery('#annotation-' + annotation.id + ' .annotation-plugin-area-bottom .reply-list-count-' + annotation.id).on('click', function() {
            self.retrieveReplies(annotation.id, this);
        });
        setTimeout(function() {
            jQuery('.annotation-slot').find('.item-' + annotation.id + ' .annotation-plugin-area-bottom').html(reply_html);
            jQuery('.item-' + annotation.id + ' .annotation-plugin-area-bottom .reply-list-count-' + annotation.id).on('click', function() {
                self.retrieveReplies(annotation.id, this);
            });
        }, 150);
    };

    $.Reply.prototype.retrieveReplies = function(annotation_id, selector) {
        var self = this;
        // this is when a call would be made to the storages for replies
        var annotations = [];
        var reply_html = '<div class="annotation-replies"><button id="replies-close-'+annotation_id+'">Close</button>';
        jQuery.each(annotations, function(_, ann) {
            //draws the replies
        });

        //add the create new reply button
        reply_html += '<div class="reply-row" id="create-reply-'+annotation_id+'"><button>Reply</button></div></div>';
        jQuery(selector).parent().append(reply_html);
        jQuery('#replies-close-' + annotation_id).on('click', function(event){
            jQuery(selector).show();
            jQuery('.annotation-replies').remove();
        });

        jQuery('#create-reply-' + annotation_id).on('click', function(event){
            hxPublish('showReplyEditor', self.instance_id, [{
                annotationText: [],
                ranges: [{
                    'parent': annotation_id
                }],
                id: Hxighlighter.getUniqueId(),
                media: "comment",
                created: new Date()
            }]);
        });
        jQuery(selector).hide();
        hxPublish('retrieveReplies', self.instance_id, [annotation_id, function(replies) {
            var reply_html = "";
            jQuery.each(replies, function(_, rep) {
                reply_html += "<div class='reply-row reply-" + rep.id + "'>" + rep.annotationText + "</div>";
            });
            jQuery(selector).parent().find('.annotation-replies').append(reply_html);
        }]);
    };

    $.Reply.prototype.saving = function(annotation) {
        return annotation;
    }

}(window));