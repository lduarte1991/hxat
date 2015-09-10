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

		var endpointLoaded = jQuery.Deferred();
		if (this.initOptions.mediaType !== "image") {
			this.endpoint = new AnnotatorEndpointController(endpointLoaded);
		} else {
			this.endpoint = new MiradorEndpointController(endpointLoaded);
		}

		this.init(endpointLoaded);
	};

	/* init
	 *
	 */
	$.DashboardController.prototype.init = function(deferredObject) {
		var self = this;

		var annotationsLoaded = self.__bind(self.annotationsLoaded, self);
		var annotationCreated = self.__bind(self.annotationCreated, self);
		var annotationUpdated = self.__bind(self.annotationUpdated, self);
		var annotationDeleted = self.__bind(self.annotationDeleted, self);

		jQuery.when(deferredObject).done(function() {
			if (self.initOptions.mediaType === "image") {
				self.endpoint.setUpListener('catchAnnotationsLoaded', annotationsLoaded);
				self.endpoint.setUpListener('catchAnnotationCreated', annotationCreated);
				self.endpoint.setUpListener('catchAnnotationDeleted', annotationDeleted);
				self.endpoint.setUpListener('catchAnnotationUpdated', annotationUpdated);
			} else {
				// sets up all event listeners and their actions
				self.endpoint.setUpListener('annotationsLoaded', annotationsLoaded);
				self.endpoint.setUpListener('annotationCreated', annotationCreated);
				self.endpoint.setUpListener('annotationDeleted', annotationDeleted);
				self.endpoint.setUpListener('annotationUpdated', annotationUpdated);
			}

			// TODO: Allow instructor (or maybe even user) to switch between different dashboards
			self.viewer = new self.dashboardView({
				suffix: self.initOptions.dashboardVersion,
				template_urls: self.initOptions.template_urls,
				element: self.element,
				endpoint: self.endpoint,
				pagination: self.initOptions.pagination,
				controller: self,
				default_tab: self.initOptions.default_tab,
			});
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
			self.viewer.getSelectedTabValue().trigger("click");
		});

		var annotationClicked = self.__bind(self.annotationClicked, self);
		var replyDeleteClicked = self.__bind(self.replyDeleteClicked, self);
		var el = self.element;
		el.on("click", ".annotationItem", annotationClicked);
		el.on("click", ".replyItem .replyeditgroup #delete", replyDeleteClicked);
	};

	$.DashboardController.prototype.changeTab = function(def){
		if (def === "Public"){
			this.queryDatabase({
				"user_id": undefined,
			});
			jQuery('#public').addClass('disabled');
			jQuery('#mynotes').removeClass('disabled');
			jQuery('#instructor').removeClass('disabled');
		}
		else if (def === "My Notes"){
			this.queryDatabase({
				"user_id": this.initOptions.user_id,
			});
			jQuery('#mynotes').addClass('disabled');
			jQuery('#public').removeClass('disabled');
			jQuery('#instructor').removeClass('disabled');
		} else {
			var ids = this.initOptions.instructors;

			// Iterate over instructor ids, querying for their annotations
			for (var i = 0; i < ids.length; i++) {
				this.queryDatabase({
					"user_id": ids[i],
				});
			}
			jQuery('#instructor').addClass('disabled');
			jQuery('#public').removeClass('disabled');
			jQuery('#mynotes').removeClass('disabled');
		}
	};

	$.DashboardController.prototype.loadMoreAnnotations = function() {
		var annotator = this.annotator;

		// TODO: Change below to be a call to the Core Controller
		var loadFromSearch = annotator.plugins.Store.options.loadFromSearch;
		var numberOfAnnotations = jQuery('.annotationSection .annotationItem').length;

		loadFromSearch.limit = this.initOptions.pagination + numberOfAnnotations;
		annotator.plugins.Store.loadAnnotationsFromSearch(loadFromSearch);
	};

	$.DashboardController.prototype._subscribeAnnotator = function() {
		var self = this;
		var annotator = this.annotator;

		var annotationClicked = self.__bind(self.annotationClicked, self);
		var el = self.element;
		el.on("click", ".annotationItem", annotationClicked);
		annotator.subscribe("annotationsLoaded", function (annotations) {
			if (self.addingAnnotations){
				self.addAnnotations('.annotationsHolder', annotations, "after");
				self.addingAnnotations = false;
			} else {
				self.clearDashboard();
				self.createNewList(annotator.plugins.Store.annotations);
			}
		});
		annotator.subscribe("annotationCreated", function (annotation) {
			var attempts = 0;
			var isChanged = function (){
				if (attempts < 100){
					setTimeout(function(){
						if(typeof annotation.id !== 'undefined'){
							if(annotation.media === "comment") {
								self.addAnnotations('.repliesList', [annotation], "before");
							} else {
								self.addAnnotations('.annotationsHolder', [annotation], "before");
							}
						} else {
							attempts++;
							isChanged();
						}
					}, 100);
				}
			};
			isChanged();
		});
		annotator.subscribe("annotationUpdated", function (annotation) {
			var annotationItem = self.formatAnnotation(annotation);
			var date = new Date(annotationItem.updated);
			var dateAgo = jQuery.timeago(date);
			if( jQuery('.annotationModal').length > 0 ) {
				jQuery('.parentAnnotation .annotatedAt').html("last updated " + dateAgo);
				jQuery('.parentAnnotation .annotatedAt').attr("title", date);
				jQuery('.parentAnnotation .body').html(annotationItem.text);
			}

			var divObject = '.annotationItem.item-'+annotation.id.toString();
			console.log(divObject);
			jQuery(divObject + ' .annotatedAt').html("last updated" + dateAgo);
			jQuery(divObject + ' .annotatedAt').attr("title", date);
			jQuery(divObject + ' .body').html(annotationItem.text);
			var tagHtml = ""
			annotationItem.tags.forEach(function(tag){
				tagHtml += "<div class=\"tag side\">" + tag + "</div>"
			});
			jQuery(divObject + ' .tagList').html(tagHtml);
		});
		annotator.subscribe("annotationDeleted", function (annotation) {
			if (jQuery('.annotationModal').length > 0) {
				jQuery('.annotationModal').remove();
    			jQuery('.annotationSection').css('y-scroll', 'scroll');
			}
			var divObject = '.annotationItem.item-'+annotation.id.toString();
			jQuery(divObject).remove();
		});
	};

	$.DashboardController.prototype.clearDashboard = function(){
		var el = this.element;
		jQuery('.annotationsHolder').html("");
	};

	$.DashboardController.prototype.createNewList = function(annotations){
		var self = this;
		var el = self.element;
		var self = this;
		annotations.forEach(function(annotation) {
			var item = self.formatAnnotation(annotation);
			var html = self.TEMPLATES.annotationItem(item);
			jQuery('.annotationsHolder').append(html);
		});

	};

	$.DashboardController.prototype._compileTemplates = function(templateType){
    	var self = this;
    	self.TEMPLATENAMES.forEach(function(templateName) {
    		var template_url = self.initOptions.template_urls + templateName + '_' + templateType + '.html';
    		jQuery.ajax({
                url: template_url,
                success: function (data) {
    		        var template = _.template(data);
    		        self.TEMPLATES[templateName] = template;
    		    },
                async: false,
            });
    	});

    };

	$.DashboardController.prototype.annotationsLoaded = function (annotations) {
		console.log("AnnotationsLoaded Triggered");
		console.log(this);
		this.endpoint.updateMasterList();
		if (this.endpoint.getNumOfAnnotationsOnScreen() > this.initOptions.pagination) {
			this.endpoint.updateEndpointList({limit:this.initOptions.pagination});
		};
		this.viewer.clearDashboard();
		this.viewer.updateDashboard(0, this.initOptions.pagination, annotations, false);
	};


	$.DashboardController.prototype.setUpSideDisplay = function(annotations) {
		var self = this;
		var attempts = 0;
		var isChanged = function (){
			if (attempts < 100){
				setTimeout( function() {
					if (typeof annotation.id !== 'undefined') {
						self.endpoint.addNewAnnotationToMasterList(annotation);
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
		console.log("AnnotationsUpdated Triggered");
		this.viewer.updateAnnotation(annotation);
	};

	$.DashboardController.prototype.annotationDeleted = function(annotation) {
		console.log("AnnotationDeleted Triggered");
		var isReply = this.endpoint.removeAnnotationFromMasterList(annotation);
		if (!isReply) {
			this.viewer.deleteAnnotation(annotation);
		};

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

    	for (var index in annotations) {
    		var annotation = annotations[index];
    		if (annotation.id === annotationId){
    			if (formatted){
    				return self.formatAnnotation(annotation);
    			} else {
    				return annotation;
    			}
    		}
    	}
    	return undefined;
    };

    $.DashboardController.prototype.getRepliesOfAnnotation = function(annotation_id) {
    	var anId = parseInt(annotation_id, 10);
    	var self = this;
    	var annotator = self.annotator;
    	var store = annotator.plugins.Store;
    	var oldLoadFromSearch = annotator.plugins.Store.options.loadFromSearch;
    	var annotation_obj_id = oldLoadFromSearch.uri;
    	var context_id = oldLoadFromSearch.contextId;
    	var collection_id = oldLoadFromSearch.collectionId;

    	var newLoadFromSearch = {
    		limit: -1,
    		parentid: anId,
    		media: "comment",
    		uri: annotation_obj_id,
    		contextId: context_id,
    		collectionId: collection_id,
    	}

    	var onSuccess = function(data) {
    		if (data === null) {
    			data = {};
    		}
    		var annotations = data.rows || [];
    		var replies_offset = jQuery('.parentAnnotation').offset().top -jQuery('.annotationModal').offset().top + jQuery('.parentAnnotation').height();
    		var replies_height = jQuery(window).height() - jQuery('.replybutton').height() - jQuery('.parentAnnotation').height() - jQuery('.modal-navigation').height();
    		jQuery('.repliesList').css('margin-top', replies_offset);
    		jQuery('.repliesList').css('height', replies_height);
    		var final_html = '';
    		self.list_of_replies = {}
    		annotations.forEach(function(annotation) {
				var item = self.formatAnnotation(annotation);
				var html = self.TEMPLATES.replyItem(item);
				final_html += html;
				self.list_of_replies[item.id.toString()] = annotation;
			});
			jQuery('.repliesList').html(final_html);
    	}

    	var search_url = store._urlFor("search", annotation_id);
        var options = store._apiRequestOptions("search", newLoadFromSearch, onSuccess);
        var request = jQuery.ajax(search_url, options);

        var replyDeleteClicked = self.__bind(self.replyDeleteClicked, self);
		var el = self.element;
		el.on("click", ".replyItem .replyeditgroup #delete", replyDeleteClicked);
    };

    $.DashboardController.prototype.replyDeleteClicked = function(e) {
    	var self = this;
    	var button = jQuery(e.target);
    	var replyItem = this.viewer.findAnnotationId(button, true);
    	var annotation_id = this.viewer.findAnnotationId(replyItem, false);
    	var annotation = this.endpoint.list_of_replies[annotation_id];
    	console.log(this.endpoint);
    	var parentId = annotation.parent;

    	button.confirmation({
			title: "Would you like to delete your reply?",
			container: "body",
			onConfirm: function (){
				self.endpoint.deleteReply(annotation, function(){
					replyItem.remove();
            		var numReply = parseInt(jQuery('.item-' + parentId).find('.replyNum').html(), 10);
           		 	jQuery('.item-' + parentId).find('.replyNum').html(numReply-1);
				});
			},
		});

		button.confirmation('show');
};

}(AController));
