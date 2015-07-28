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
		console.log(options);
		this.element = options.annotationElement;

		this.initOptions = jQuery.extend({}, defaultOptions, options.initOptions, commonInfo);

		this.current_tab = this.initOptions.default_tab;
		this.resizing = false;
		this.lastUp = 150;

		this.TEMPLATENAMES = [
			"annotationSection",
			"annotationItem",
		];

		this.init();
		
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

		annotator.subscribe("annotationsLoaded", function (annotations) {
			self.setUpSideDisplay(annotations);
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

	$.DashboardController.prototype.setUpSideDisplay = function(annotations) {
		var self = this;
		var el = self.element;
		var self = this;
		var annotationItems = [];
		annotations.forEach(function(annotation) {
			var item = jQuery.extend(true, {}, annotation);
			var html = self.TEMPLATES.annotationItem(annotation);
			annotationItems.push(html);
		});
		el.html(self.TEMPLATES.annotationSection({
			annotationItems: annotationItems,
		}));

		jQuery('.resize-handle.side').on('mousedown', function(e){
			self.resizing = true;
		});

		jQuery(document).on('mousemove', function(e){
			if (!self.resizing){
				return;
			}
			e.preventDefault();
			var section = jQuery('.annotationSection');
			section.css('min-width', '0px');
			var offset = section.width()-(e.clientX - section.offset().left);
			section.css('width', offset);
			section.css('right', 0);
			self.lastUp = offset;
		}).on('mouseup', function(e){
			self.resizing = false;
			var section = jQuery('.annotationSection');
			if(self.lastUp < 150){
				jQuery('#leftCol').attr('class', 'col-xs-11');
				section.css('width', '0px');
				section.css('right', -10);
			} else {
				jQuery('#leftCol').attr('class', 'col-xs-7');
				section.css('min-width', '150px');
			}
		});
	};

}(AController));