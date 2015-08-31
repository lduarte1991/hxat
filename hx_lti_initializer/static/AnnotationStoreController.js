var AnnotationStoreController = function(deferredObject){
	if (this.constructor === AnnotationStoreController) {
		throw new Error("Can't instantiate abstract class");
	}
};

AnnotationStoreController.prototype.getDatabaseEndPoint = function() {
	throw new Error("Abstract method!");
};

AnnotationStoreController.prototype.getNumOfAnnotationsOnScreen = function(){
	throw new Error("Abstract method!");
};

AnnotationStoreController.prototype.setUpListener = function(listener, expected_fun) {
	throw new Error("Abstract method!");
};

AnnotationStoreController.prototype.updateMasterList = function() {
	throw new Error("Abstract method!");
};

AnnotationStoreController.prototype.loadMoreAnnotations = function(annotations) {
	throw new Error("Abstract method!");
};

AnnotationStoreController.prototype.addNewAnnotationToMasterList = function(annotation) {
	throw new Error("Abstract method!");
};

AnnotationStoreController.prototype.removeAnnotationFromMasterList = function(annotation) {
	throw new Error("Abstract method!");
};

AnnotationStoreController.prototype.getAnnotationById = function(id) {
	throw new Error("Abstract method!");
};

AnnotationStoreController.prototype.authorize = function(action, annotation) {
	throw new Error("Abstract method!");
};

AnnotationStoreController.prototype.openEditorForReply = function(location) {
	throw new Error("Abstract method!");
};

AnnotationStoreController.prototype.deleteAnnotation = function(annotation) {
	throw new Error("Abstract method!");
};

AnnotationStoreController.prototype.editAnnotation = function(annotation, button) {
	throw new Error("Abstract method!");
};

AnnotationStoreController.prototype.loadRepliesForParentAnnotation = function(annotation_id, displayFunction) {
	throw new Error("Abstract method!");
};

AnnotationStoreController.prototype.deleteReply = function(reply, callback) {
	throw new Error("Abstract method!");
};

/***
 ** Annotator Endpoint for Dashboard Interaction
 **
 ** Provides a way for the DashboardController.js to interact with the database via Annotator.
 ***/
var AnnotatorEndpointController = function(deferredObject) {
    AnnotationStoreController.apply(this, arguments);

    // gets the current instance of the wrapper around the target object and annotator
	var wrapper = jQuery('.annotator-wrapper').parent()[0];
	this.annotator = jQuery.data(wrapper, 'annotator');
	this.annotationsMasterList = [];
	deferredObject.resolve();
};

AnnotatorEndpointController.prototype = Object.create(AnnotationStoreController.prototype);

AnnotatorEndpointController.prototype.constructor = AnnotatorEndpointController;

AnnotatorEndpointController.prototype.getDatabaseEndPoint = function() {
	return this.annotator;
};

AnnotatorEndpointController.prototype.getNumOfAnnotationsOnScreen = function (){
	return this.annotator.plugins.Store.annotations.length;
};

AnnotatorEndpointController.prototype.setUpListener = function(listener, expected_fun) {
	var self = this;
	var annotator = this.annotator;

	annotator.subscribe(listener, function(annotations) {
		expected_fun(annotations);
	});
};

AnnotatorEndpointController.prototype.updateMasterList = function() {
	var self = this;
	var searchParameters = this.annotator.plugins.Store.options.loadFromSearch;
	searchParameters.limit = -1;
	searchParameters.offset = 0;
	var onSuccess = function(data) {
		if (data === null) {
			data = {}
		};
		self.annotationsMasterList = data.rows || [];
	};
	search_url = this.annotator.plugins.Store._urlFor("search");
	var options = this.annotator.plugins.Store._apiRequestOptions("search", searchParameters, onSuccess);
	var request = jQuery.ajax(search_url, options);
};

AnnotatorEndpointController.prototype.loadMoreAnnotations = function(annotations) {
	var self = this;
	annotations.forEach(function(annotation){
		self.annotator.setupAnnotation(annotation);
		self.annotator.plugins.Store.registerAnnotation(annotation);
	});
};

AnnotatorEndpointController.prototype.addNewAnnotationToMasterList = function(annotation) {
	self.annotationsMasterList.unshift(annotation);
};

AnnotatorEndpointController.prototype.removeAnnotationFromMasterList = function(annotation) {
	var index = self.annotationsMasterList.indexOf(annotation);
	if (index > -1) {
		self.annotationsMasterList.splice(index, 1);
	};
};

AnnotatorEndpointController.prototype.getAnnotationById = function(id) {
	var annotationId = parseInt(id, 10);
	var annotations = this.annotationsMasterList;

	for (index in annotations) {
		if (annotations[index].id === annotationId)
			return annotation;
	}

	return undefined;
};

AnnotatorEndpointController.prototype.authorize = function(action, annotation) {
	var permissions = this.annotator.plugins.Permissions;
	return permissions.options.userAuthorize(action, annotation, permissions.user);
};

AnnotatorEndpointController.prototype.openEditorForReply = function(location) {
	var position = location;
	position.display = "block";
	this.annotator.adder.css(position);
	this.annotator.onAdderClick();

	var parent = jQuery(this.annotator.editor.element).find('.reply-item span.parent-annotation');
    parent.html(annotation_id);
};

AnnotatorEndpointController.prototype.deleteAnnotation = function(annotation) {
	this.annotator.deleteAnnotation(annotation);
};

AnnotatorEndpointController.prototype.editAnnotation = function(annotation, button) {
	var self = this;
	var button = jQuery(event.target);

	var positionAdder = {
		display: "block",
		left: button.offset().left,
		top: button.scrollTop(),
	}

	var annotation_to_update = annotation;
	
	var update_parent = function() {
     	cleanup_parent();
    	var response = self.annotator.updateAnnotation(annotation_to_update);
    	return response;
    };
    var cleanup_parent = function() {
    	self.annotator.unsubscribe('annotationEditorHidden', cleanup_parent);
    	return self.annotator.unsubscribe('annotationEditorSubmit', update_parent);
    };

    self.annotator.subscribe('annotationEditorHidden', cleanup_parent);
    self.annotator.subscribe('annotationEditorSubmit', update_parent);
	self.annotator.showEditor(annotation_to_update, positionAdder);
	
	jQuery('.annotator-widget').addClass('fullscreen');
};

AnnotatorEndpointController.prototype.loadRepliesForParentAnnotation = function(annotation_id, displayFunction) {
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
	};

	var onSuccess = function(data) {
		if (data === null) {
			data = {};
		}
		self.list_of_replies = data.rows || [];
		displayFunction(self.list_of_replies);
	}

	search_url = store._urlFor("search", annotation_id);
    var options = store._apiRequestOptions("search", newLoadFromSearch, onSuccess);
    jQuery.ajax(search_url, options);

};

AnnotatorEndpointController.prototype.deleteReply = function(reply, callback) {
	this.annotator.plugins.Store._apiRequest("destroy", reply, callback);
};

AnnotatorEndpointController.prototype.queryDatabase = function(options, pagination, mediaType) {
	var setOptions = jQuery.extend({}, this.queryDefault, options);
	var annotator = this.annotator;

	// TODO: Change below to be a call to the Core Controller
	var loadFromSearch = annotator.plugins.Store.options.loadFromSearch;
	var numberOfAnnotations = jQuery('.annotationSection .annotationItem').length;
	loadFromSearch.limit = pagination;
	loadFromSearch.offset = 0;
	loadFromSearch.media = mediaType;
	loadFromSearch.userid = setOptions.user_id;
	loadFromSearch.username = setOptions.username;
	loadFromSearch.text = setOptions.text;
	loadFromSearch.tag = setOptions.tag;
	this._clearAnnotator();
	annotator.plugins.Store.loadAnnotationsFromSearch(loadFromSearch);
};

// TODO (Move to Annotator Core)
AnnotatorEndpointController.prototype._clearAnnotator = function() {
    var annotator = this.annotator;
    var store = annotator.plugins.Store;
    var annotations = store.annotations.slice();
    
    annotations.forEach(function(ann){
        var child, h, _i, _len, _ref;
        if (ann.highlights !== undefined) {
            _ref = ann.highlights;
            for (_i = 0, _len = _ref.length; _i < _len; _i++) {
                h = _ref[_i];
                if (!(h.parentNode !== undefined)) {
                    continue;
                }
                child = h.childNodes[0];
                jQuery(h).replaceWith(h.childNodes);
            }
        }
        store.unregisterAnnotation(ann);
    });
};


/***
 ** Mirador Endpoint for Dashboard Interaction
 **
 ** Provides a way for the DashboardController.js to interact with the database via Mirador.
 ***/

var MiradorEndpointController = function(deferredObject) {
    AnnotationStoreController.apply(this, arguments);
    var self = this;
    jQuery.subscribe('windowAdded', function (event, windowId, slotAddress) {
    	console.log("window was added");
    	// TODO (check id to make sure slot/window match initialized)
    	self.window = Mirador.viewer.workspace.slots[0].window;
		self.endpoint = self.window.endpoint;
		deferredObject.resolve();
	});
	self.annotationsMasterList = [];
};    

MiradorEndpointController.prototype = Object.create(AnnotationStoreController.prototype);

MiradorEndpointController.prototype.constructor = MiradorEndpointController;

MiradorEndpointController.prototype.getDatabaseEndPoint = function() {
	return this.endpoint;
};

MiradorEndpointController.prototype.getNumOfAnnotationsOnScreen = function (){
	return this.endpoint.annotationsListCatch.length;
};

MiradorEndpointController.prototype.setUpListener = function(listener, expected_fun) {
	var self = this;
	if (listener === "annotationListLoaded") {
		jQuery.subscribe(listener + '.' + self.window.id, function(event) {
			var annotations = self.endpoint.annotationsListCatch;
			expected_fun(annotations);
		});
	} else {
		jQuery.subscribe(listener + '.' + self.window.id, function(event, oaAnnotation) {
			expected_fun(annotations);
		});
	}
};

MiradorEndpointController.prototype.updateMasterList = function(){
	// make a call to mirador endpoint to call CATCH to get a new instance
};

MiradorEndpointController.prototype.loadMoreAnnotations = function(annotations) {
	var self = this;
	annotations.forEach(function(annotation){
		// Add annotations to annotationListCatch
		self.endpoint.annotationsListCatch.push(annotation);

		// trigger drawing here or once they're all loaded below
	});
	// trigger only after adding all items to annotationListCatch
};

MiradorEndpointController.prototype.addNewAnnotationToMasterList = function(annotation){
	this.annotationsMasterList.unshift(annotation);
};

MiradorEndpointController.prototype.removeAnnotationFromMasterList = function(annotation){
	var index = this.annotationsMasterList.indexOf(annotation);
	if (index > -1) {
		this.annotationsMasterList.splice(index, 1);
	};
};

MiradorEndpointController.prototype.getAnnotationById = function(id) {
	var annotationId = parseInt(id, 10);
	var annotations = this.annotationsMasterList;

	for (index in annotations) {
		if (annotations[index].id === annotationId)
			return annotation;
	}

	return undefined;
};

MiradorEndpointController.prototype.authorize = function(action, annotation) {
	var user = this.endpoint.catchOptions.user;
	var permissions = this.endpoint.catchOptions.permissions;
	var tokens = annotation.permissions[action] || [];
	if (tokens.length === 0) {
		return true;
	}
	for (item in tokens) {
		var token = tokens[item];
		if (user.id === token) {
			return true;
		}
	}
	return false;
};

MiradorEndpointController.prototype.openEditorForReply = function(location) {

};

MiradorEndpointController.prototype.deleteAnnotation = function(annotation) {

};

MiradorEndpointController.prototype.editAnnotation = function(annotation, button) {

};

MiradorEndpointController.prototype.loadRepliesForParentAnnotation = function(annotation_id, displayFunction) {

};

MiradorEndpointController.prototype.deleteReply = function(reply, callback) {

};

MiradorEndpointController.prototype.queryDatabase = function(options, pagination, mediaType) {

};

MiradorEndpointController.prototype._clearAnnotator = function() {

};
