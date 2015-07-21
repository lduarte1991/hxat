(function($) {
	$.DashboardController = function(options, commonInfo) {
		var defaultOptions = {
			media: commonInfo.mediaType,
			userId: commonInfo.user_id,
			showMediaSelector: true,
			showPublicPrivate: true,
			pagintation: 50,
			flags: false,
		}

		this.element = options.annotationElement;

		this.initOptions = jQuery.extend({}, defaultOptions, options.initOptions, commonInfo);

		this.current_tab = this.initOptions.default_tab;

		this.TEMPLATENAMES = [
			"annotationSection",
		];

		this.init();
		
		this.loadAnnotations();		
	};

	/* init
	 * 
	 */
	$.DashboardController.prototype.init = function() {
		var wrapper = jQuery('.annotator-wrapper').parent()[0];
		var annotator = jQuery.data(wrapper, 'annotator');
		this.annotator = annotator;
		this._subscribeAnnotator();
		this.TEMPLATES = {};
		this._compileTemplates("side");
	};

	$.DashboardController.prototype.loadAnnotations = function() {
		var annotator = this.annotator;

		// TODO: Change below to be a call to the Core Controller
		var loadFromSearch = annotator.plugins.Store.options.loadFromSearch;

		loadFromSearch.limit = this.initOptions.pagination;
		loadFromSearch.offset = 0;
		loadFromSearch.media = this.initOptions.mediaType;
		loadFromSearch.userid = this.initOptions.user_id;
		annotator.plugins.Store.loadAnnotationsFromSearch(loadFromSearch);
	};

	$.DashboardController.prototype._subscribeAnnotator = function() {
		var self = this;
		var annotator = this.annotator;

		annotator.subscribe("annotationsLoaded", function (annotations){
			console.log(annotator.plugins.Store.annotations);
			self.setUpSideDisplay();
		})
	};

	$.DashboardController.prototype._compileTemplates = function(templateType){
    	var self = this;
    	self.TEMPLATENAMES.forEach(function(templateName) {
    		var template_url = self.initOptions.template_urls + templateName + '_' + templateType + '.html';
    		jQuery.ajax({
                url: template_url, 
                success: function (data) {
    		        template = _.template(data);
    		        self.TEMPLATES[templateName] = template;
    		    },
                async: false,
            });
    	});
    	
    };

	$.DashboardController.prototype.setUpSideDisplay = function() {
		var self = this;
		var el = self.element;
		el.html(self.TEMPLATES.annotationSection());
	};

}(AController));