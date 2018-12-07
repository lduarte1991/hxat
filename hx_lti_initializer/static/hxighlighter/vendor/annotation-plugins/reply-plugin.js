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
        this.instance_id = instanceID;

        this.init();
        return this;
    };

    /**
     * Initializes instance
     */
    $.Reply.prototype.init = function() {
        var self = this;

        var options = {
            url: self.options.template_urls + "reply-v2.html",
            type: "GET",
            contentType: "charset=utf-8",
            success: function(data) {
                self.replyTemplate = _.template(data);
            },
            async: true,
        }

        jQuery.ajax(options);
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
                reply_html += " " + annotation.replyCount;
            } else {
                reply_html += " 0";
            }
            reply_html += "</div>";

            viewer.find('#annotation-' + annotation.id + ' .annotation-plugin-area-bottom').html(reply_html);
            jQuery('#annotation-' + annotation.id + ' .annotation-plugin-area-bottom .reply-list-count-' + annotation.id).on('click', function() {
                self.retrieveReplies(annotation.id, this);
            });
        });
    };

    $.Reply.prototype.annotationDrawn = function(annotation) {
        var self = this;
        if (annotation.media == "Annotation") {
            console.log(annotation);
            var par = annotation.ranges[0].parent;
            if (jQuery('.item-' + par + ' .annotation-replies:visible').length > 0) {
                jQuery('.item-' + par + ' .annotation-replies').append(self.replyTemplate(annotation));
            } else {
                jQuery('.ann-item#annotation-' + par + ' .annotation-replies').append(self.replyTemplate(annotation));
            }

            jQuery('.delete:not([jc-attached])').confirm({
                title: 'Delete Annotation?',
                content: 'Would you like to delete your annotation? This is permanent.',
                buttons: {
                    confirm: function() {
                        var annotation_id = this.$target[0].id.replace('delete-', '');
                        hxPublish('deleteAnnotationById', self.instance_id, [annotation_id]);
                        jQuery('.reply-' + annotation_id).remove();
                        var currentCount = parseInt(jQuery('.reply-list-count-' + par).text().trim(), 10) - 1;
                        jQuery('.reply-list-count-' + par).html(" <span class='glyphicon glyphicon-comment'></span> " + currentCount);
                    },
                    cancel: function () {
                    }
                }
            });
            setTimeout(function() {
                jQuery('.reply-' + annotation.id).data('annotation', annotation);
                jQuery('.reply-' + annotation.id).on('click', '.edit-reply#edit-' + annotation.id, function(event){
                    var reply = jQuery('.reply-' + annotation.id).data('annotation');
                    hxPublish('showReplyEditor', self.instance_id, [reply, true]);                    
                });
            }, 750);
            
            return;
        }

        var reply_html = "<div class='reply-list-count-" + annotation.id + "'> <span class='glyphicon glyphicon-comment'></span>";
        if (typeof annotation.replyCount !== 'undefined') {
            reply_html += " " + annotation.replyCount;
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
        // console.log(annotation_id, selector);
        // this is when a call would be made to the storages for replies
        var reply_html = '<div class="annotation-replies"><button id="replies-close-'+annotation_id+'">Close</button>';
        hxPublish('searchRequestInitiated', self.instance_id, [{
            'source_id': annotation_id
        }, function(results) {
            // console.log(results);
            // var reply_html = "";
            // jQuery.each(results, function(_, reply) {
            //     reply_html += "<div class='replyItem reply-item-" + reply.id + "' tabindex='0' role='listitem' aria-label='reply to annotation'><div class='replytext field'>" + reply.annotationText + "</div></div>"
            // });
            // console.log(reply_html);
            // jQuery('#create-reply-' + annotation_id).after(reply_html);
        }])


        //add the create new reply button
        reply_html += '<div class="reply-row" id="create-reply-'+annotation_id+'"><button>Reply</button></div></div>';
        jQuery(selector).parent().append(reply_html);
        jQuery('#replies-close-' + annotation_id).on('click', function(event){
            jQuery(selector).show();
            jQuery('.reply-list-count-' + annotation_id).show();
            jQuery('.annotation-replies').remove();
        });

        jQuery('#create-reply-' + annotation_id).on('click', function(event){
            console.log(self.options);
            hxPublish('showReplyEditor', self.instance_id, [{
                annotationText: [],
                ranges: [{
                    'parent': annotation_id
                }],
                id: Hxighlighter.getUniqueId(),
                media: "Annotation",
                created: new Date(),
                creator: {
                    'id': self.options.user_id,
                    'name': self.options.username
                }
            }, false]);
        });
        jQuery(selector).hide();
        // hxPublish('retrieveReplies', self.instance_id, [annotation_id, function(replies) {
        //     var reply_html = "";
        //     jQuery.each(replies, function(_, rep) {
        //         reply_html += "<div class='reply-row reply-" + rep.id + "'>" + rep.annotationText + "</div>";
        //     });
        //     jQuery(selector).parent().find('.annotation-replies').append(reply_html);
        // }]);
    };

    $.Reply.prototype.saving = function(annotation) {
        if (annotation.media == "Annotation") {
            var par = annotation.ranges[0].parent;
            var currentCount = parseInt(jQuery('.reply-list-count-' + par).text().trim(), 10) + 1;
            jQuery('.reply-list-count-' + par).html(" <span class='glyphicon glyphicon-comment'></span> " + currentCount);
            return annotation;
        } else {
            return annotation;
        }
    }

}(window));