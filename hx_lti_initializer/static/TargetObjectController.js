/***
 * TargetObjectController.js
 *
 ***/

(function($) {
	$.TargetObjectController = function(options, commonInfo) {
		this.initOptions = jQuery.extend({}, options, commonInfo);
	};

	/* init
	 * 
	 */
	$.TargetObjectController.prototype.init = function(){

	};

	$.TargetObjectController.prototype.setUpTargetAsText = function(element, targetObject) {

	};

	$.TargetObjectController.prototype.setUpTargetAsVideo = function(element, targetObject) {

	};

	$.TargetObjectController.prototype.colorizeAnnotation = function(annotationId, rgbColor) {
		if (this.initOptions.mediaType === "image") {
			setTimeout(function(){
				jQuery(".annotation#" + annotationId.toString()).css("border", "2px solid rgba(" + rgbColor.red + ", " + rgbColor.green + ", " + rgbColor.blue + ", " + rgbColor.alpha + ")");
				window.tags = jQuery('.annotationItem.item-' + annotationId.toString()).find('.tag');
				window.tags.each(function (index, item) {
					var tag = jQuery.trim(jQuery(item).html());
					var rgbColor = window.AController.main.tags[tag];
					if (rgbColor !== undefined) {
						jQuery(item).css("background-color", "rgba(" + rgbColor.red + ", " + rgbColor.green + ", " + rgbColor.blue + ", " + rgbColor.alpha + ")");
					};
				})
			}, 60);
		};
	};

	$.TargetObjectController.prototype.colorizeViewer = function (){
		window.tags = jQuery('.qtip').find('.tag');
		window.tags.each(function (index, item) {
			var tag = jQuery.trim(jQuery(item).html());
			var rgbColor = window.AController.main.tags[tag];
			if (rgbColor !== undefined) {
				jQuery(item).css("background-color", "rgba(" + rgbColor.red + ", " + rgbColor.green + ", " + rgbColor.blue + ", " + rgbColor.alpha + ")");
			};
		});
	};

	$.TargetObjectController.prototype.toggleAnnotations = function() {
		if (this.initOptions.mediaType === "text") {
			var annotator = window.AController.annotationCore.annotation_tool;
			var store = annotator.plugins.Store;
			if (jQuery('.annotations-status').hasClass('on')) {
				jQuery('.annotations-status .hover-inst').html("Show annotations");
				jQuery('.annotations-status i').removeClass('fa-close');
				jQuery('.annotations-status i').addClass('fa-comments');
				this.annotationsSaved = store.annotations.slice();
				store.annotations.forEach(function (annotation) {
					window.AController.dashboardObjectController.endpoint._clearAnnotator();
				});
			} else {
				jQuery('.annotations-status .hover-inst').html("Hide annotations");
				jQuery('.annotations-status i').addClass('fa-close');
				jQuery('.annotations-status i').removeClass('fa-comments');
				this.annotationsSaved.forEach(function (annotation) {
					annotator.setupAnnotation(annotation);
					store.registerAnnotation(annotation);
				});
				annotator.publish("externalCallToHighlightTags");
			}
			jQuery('.annotations-status').toggleClass("on");
		};
	}

}(AController));
