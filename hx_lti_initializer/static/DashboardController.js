/**
 *  DashboardController.js
 *	
 * This file contains all logic for the sidebar or bottombar in order to show
 * annotations in a table/list view instead of, or alongside, the mouseovers
 * in the target object. 
 **/
(function($) {

	$.DashboardController = function(options, commonInfo, dashboardView) {
		
		// sets up the default options
		var defaultOptions = {

			// media can be "text", "video", or "image"
			media: commonInfo.mediaType,
			userId: commonInfo.user_id,

			// if true, this will allow users to change between annotations for video, text,
			// or images that exist in the same page
			showMediaSelector: false,

			// if true this will allow users to switch between public/private
			showPublicPrivate: true,
			pagination: 50,
			flags: false,

			// adds a suffix to get the appropriate template
		};

		this.element = options.annotationElement;
		this.dashboardView = dashboardView;
		this.initOptions = jQuery.extend({}, defaultOptions, options.initOptions, commonInfo);
		this.annotationsMasterList = [];
		this.current_tab = this.initOptions.default_tab;
		
		this.writingReply = false;

		

		if (this.initOptions.mediaType !== "image") {
			this.endpoint = new AnnotatorEndpointController();
		} else {
			this.endpoint = new MiradorEndpointController();
		}

		this.init();
	};

	/* init
	 * 
	 */
	$.DashboardController.prototype.init = function() {

		var annotationsLoaded = self.__bind(this.annotationsLoaded, this);
		var annotationCreated = self.__bind(this.annotationCreated, this);
		var annotationUpdated = self.__bind(this.annotationUpdated, this);
		var annotationDeleted = self.__bind(this.annotationDeleted, this);

		// sets up all event listeners and their actions
		this.endpoint.setUpListener('annotationsLoaded', annotationsLoaded);
		this.endpoint.setUpListener('annotationCreated', annotationCreated);
		this.endpoint.setUpListener('annotationDeleted', annotationDeleted);
		this.endpoint.setUpListener('annotationUpdated', annotationUpdated);
		// actually compile templates
		
		// TODO: Allow instructor (or maybe even user) to switch between different dashboards
		this.viewer = new this.dashboardView({
			suffix: this.initOptions.dashboardVersion,
			template_urls: this.initOptions.template_urls,
			element: this.element,
			endpoint: this.endpoint,
			pagination: this.initOptions.pagination,
			controller: this,
		});

	};

	$.DashboardController.prototype.setUpButtons = function() {
		var self = this;

		jQuery('#public').click(function (e){
			self.endpoint.queryDatabase({
				"user_id": undefined,
			}, self.initOptions.pagination, self.initOptions.media);
		});
		jQuery('#mynotes').click(function (e){
			self.endpoint.queryDatabase({
				"user_id": self.initOptions.user_id,
			}, self.initOptions.pagination, self.initOptions.media);
		});
		jQuery('#instructor').click(function (e){
			self.endpoint.queryDatabase({
				"user_id": self.initOptions.instructors,
			}, self.initOptions.pagination, self.initOptions.media);
		});
		
		jQuery('button#search-submit').click(function (e) {
			var text = jQuery('#srch-term').val();
			var search_filter = self.viewer.getSelectedFilterValue().attr("id");
			if (search_filter === "users-filter"){
				self.endpoint.queryDatabase({
					"username": text,
				}, self.initOptions.pagination, self.initOptions.media);
			} else if (search_filter === "annotationtext-filter"){
				self.endpoint.queryDatabase({
					"text": text,
				}, self.initOptions.pagination, self.initOptions.media);
			} else if (search_filter === "tag-filter"){
				self.endpoint.queryDatabase({
					"tag": text,
				}, self.initOptions.pagination, self.initOptions.media)
			}
		});

		jQuery('button#search-clear').click(function (e) {
			jQuery('#srch-term').val("");
			self.getSelectedTabValue.trigger("click");
		});

		var annotationClicked = self.__bind(self.annotationClicked, self);
		var replyDeleteClicked = self.__bind(self.replyDeleteClicked, self);
		var el = self.element;
		el.on("click", ".annotationItem", annotationClicked);
		el.on("click", ".replyItem .replyeditgroup #delete", replyDeleteClicked);
	};


	$.DashboardController.prototype.loadMoreAnnotations = function() {
		var annotator = this.annotator;

		// TODO: Change below to be a call to the Core Controller
		var loadFromSearch = annotator.plugins.Store.options.loadFromSearch;
		var numberOfAnnotations = jQuery('.annotationSection .annotationItem').length;

		loadFromSearch.limit = this.initOptions.pagination + numberOfAnnotations;
		annotator.plugins.Store.loadAnnotationsFromSearch(loadFromSearch);
	};

	$.DashboardController.prototype.annotationsLoaded = function (annotations) {
		console.log("AnnotationsLoaded Triggered");
		console.log(this);
		this.endpoint.updateMasterList();
		this.viewer.clearDashboard();
		this.viewer.updateDashboard(0, this.initOptions.pagination, annotations, false);
	};

	$.DashboardController.prototype.annotationCreated = function (annotation) {
		console.log("AnnotationsCreated Triggered");
		var self = this;
		var attempts = 0;
		var isChanged = function (){
			if (attempts < 100){
				setTimeout( function() {
					if (typeof annotation.id !== 'undefined') {
						self.viewer.addCreatedAnnotation(annotation.media, annotation);
					} else {
						attempts++;
						isChanged();
					}
				}, 100);
			}
		};
		isChanged();
	};

	$.DashboardController.prototype.annotationUpdated = function (annotation) {
		this.endpoint.addNewAnnotationToMasterList(annotation);
		this.viewer.updateAnnotation(annotation);
	};

	$.DashboardController.prototype.annotationDeleted = function(annotation) {
		this.endpoint.removeAnnotationFromMasterList(annotation);
		this.viewer.deleteAnnotation(annotation);
	};

	$.DashboardController.prototype.__bind = function(fn, me) { 
	    return function() { 
	        return fn.apply(me, arguments); 
    	}
    }; 

	

	

    $.DashboardController.prototype.annotationClicked = function(e) {
    	var self = this;
    	var target = jQuery(e.target);
    	var annotation_id = this.viewer.findAnnotationId(target, false);

    	var annotationClicked = self.endpoint.getAnnotationById(annotation_id);
    	this.viewer.displayModalView(annotationClicked);
    	this.endpoint.loadRepliesForParentAnnotation(annotation_id, this.viewer.displayReplies);
    };

    $.DashboardController.prototype.replyDeleteClicked = function(e) {
    	var self = this;
    	var button = jQuery(e.target);
    	var replyItem = this.viewer.findAnnotationId(button, true);
    	var annotation_id = this.viewer.findAnnotationId(replyItem, false);
    	var annotation = self.endpoint.list_of_replies[annotation_id];

    	button.confirmation({
			title: "Would you like to delete your reply?",
			onConfirm: function (){
				self.endpoint.deleteReply(annotation, function(){ replyItem.remove(); });
			},
		});

		button.confirmation('show');
};

}(AController));