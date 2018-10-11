/**
 *  Permissions
 *
 */

(function($){

    /**
     * @constructor
     * @params {Object} options - specific options for this plugin
     */
    $.Permissions = function(options, instanceID) {
        this.options = jQuery.extend({}, options);
        this.init();
        this.instance_id = instanceID;
        return this;
    };

    /**
     * Initializes instance
     */
    $.Permissions.prototype.init = function() {
        var self = this;
        console.log(self.options);
    };

    $.Permissions.prototype.returnValue = function() {

    };

    $.Permissions.prototype.destroy = function(element, selector) {

    };

    // Annotation specific functions

    $.Permissions.prototype.annotationListeners = function() {
        var self = this;
    };

    $.Permissions.prototype.editorShown = function(annotation, editor) {

    };
 
    $.Permissions.prototype.viewerShown = function(annotations, viewer) {
        var self = this;
        jQuery.each(annotations, function(_, annotation) {
            if(annotation.creator.id !== self.options.user_id) {
                jQuery('#delete-' + annotation.id).remove();
                jQuery('#edit-' + annotation.id).remove();
            }
        });
    };

    $.Permissions.prototype.annotationDrawn = function(annotation) {
        
    };

    $.Permissions.prototype.retrieveReplies = function(annotation_id, selector) {

    };

    $.Permissions.prototype.saving = function(annotation) {
        return annotation;
    };

}(window));