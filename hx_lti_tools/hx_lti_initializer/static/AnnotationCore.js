/***
 * AnnotatorCore.js
 *
 * This file will contain the functions needed to access and use
 * whatever library is currently the norm for annotations.
 * As of Spring 2015, the norm is to use annotator.js
 * This is the page that should change if/when that tool changes.
 ***/

(function($) {
	$.AnnotationCore = function(options, commonInfo) {
		// HTMLElement that contains what should be annotated
		this.element = options.annotationElement;

		// contains any other options needed to initialize the tool
		this.initOptions = jQuery.extend({}, options.initOptions, commonInfo);

		// initializes tool
		this.init(this.initOptions.mediaType);

		return this;
	};

	/* init
	 * The following function initializes the annotation core library
	 * it should change depending on what the library we are using is.
	 * Currently we are using annotator.js and thus the following
	 * initializes and depends on those libraries being present.
	 */
	$.AnnotationCore.prototype.init = function(mediaType){
		// use this space to mold initOptions into whatever shape you need it to be
		annotatorOptions = this.initOptions;
		
		// sets up the store for the common settings for the tool, specifically Annotation Database
		this.setUpCommonAttributes();

		if (mediaType === "text") {
			// create the annotation core holder to be able to access it throughout the tool
			this.annotation_tool = jQuery(this.element).annotator(annotatorOptions).data('annotator');
			this.setUpPlugins();
		}
	};

	/* setUpCommonAttributes
	 * Init some plugins or options that are common between text, video, and image.
	 */
	$.AnnotationCore.prototype.setUpCommonAttributes = function(){
		annotatorOptions = this.initOptions

		// checks to make sure whether the store attribute exists
		if (typeof annotatorOptions.store === "undefined"){
			annotatorOptions.store = {};
		}

		// as with above, the store needs to be set up a specific way
		var store = annotatorOptions.store;
	    if (typeof store.annotationData === 'undefined'){
	        store.annotationData = {};
	    }

	    // new mechanic, the following three options contains all the information you would
	    // need to know to determine where the annotation belongs, object_id is the id of the
	    // target source, it can exist in multiple assignments and multiple courses. context_id
	    // refers to the course it belongs to and collection_id is the assignment the object belongs to
	    if (typeof store.annotationData.uri === 'undefined'){
	        store.annotationData.uri = annotatorOptions.object_id;
	    }
	    if (typeof store.annotationData.context_id === 'undefined'){
	        store.annotationData.context_id = annotatorOptions.context_id;
	    }
	    if (typeof store.annotationData.collection_id === 'undefined'){
	        store.annotationData.collection_id = annotatorOptions.collection_id;
	    }

	    // the following are options for the first retrieval of information from the Annotation Database
	    if (typeof store.loadFromSearch === 'undefined'){
	        store.loadFromSearch = {};
	    }
	    if (typeof store.loadFromSearch.uri === 'undefined'){
	        store.loadFromSearch.uri = store.annotationData.uri;
	    }
	    if (typeof store.loadFromSearch.limit === 'undefined'){
	        store.loadFromSearch.limit = 10000;
	    }
	};

	$.AnnotationCore.prototype.setUpPlugins = function() {
	    for (plugins in this.initOptions.plugins){
	    	options = {
	    		 // The endpoint of the store on your server.
                prefix: "",
                annotationData: {
                    uri: 'http://test.com',
                    citation: "${source}"
                },
                urls: {
                    // These are the default URLs.
                    create:  '/create',
                    read:    '/read/:id',
                    update:  '/update/:id',
                    destroy: '/delete/:id',
                    search:  '/search'
                },
                loadFromSearch:{
                    limit:1,
                    offset:0,
                    uri:'http://test.com',
                    media:'text',
                    userid:'${user.email}',
                }
	    	};
	    	this.annotation_tool.addPlugin(this.initOptions.plugins[plugins], options);

	    }
	}

}(AController));
