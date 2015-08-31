(function($) {
    $.DashboardView = function(options) {
        var defaultOptions = {
            // set up template names that will be pulled
            TEMPLATENAMES: [
                "annotationSection",
                "annotationItem",
                "annotationModal",
                "replyItem",
            ],
            TEMPLATES: {},
            suffix: "side",
            template_urls: "",
        };

        this.initOptions = jQuery.extend({}, defaultOptions, options);
        this.init();

        this.filterButtons = [
            '#users-filter',
            '#annotationtext-filter',
            '#tag-filter',
        ];

        this.tabs = [
            '#public',
            '#mynotes',
            '#instructor',
        ];

        this.holders = {
            'comment': '.repliesList',
            'text': '.annotationsHolder',
            'image': '.annotationsHolder',
            'video': '.annotationsHolder',
        };

        this.templateTypes = {
            'replies': 'replyItem',
            'text': 'annotationItem',
            'image': 'annotationItem',
            'video': 'annotationItem',
        }

        // variables used when resizing dashboards
		this.resizing = false;
		this.lastUp = 150;

    };

    $.DashboardView.prototype.init = function () {
        this.setUpTemplates(this.initOptions.suffix);

    };

    $.DashboardView.prototype.setUpTemplates = function(suffix){
        var self = this;
        var deferreds = jQuery.map(self.initOptions.TEMPLATENAMES, function(templateName){
            var options = {
                url: self.initOptions.template_urls + templateName + '_' + suffix + '.html',
                success: function (data) {
                    template = _.template(data);
                    self.initOptions.TEMPLATES[templateName] = template;
                },
                async: true,
            };
            return jQuery.ajax(options);
        });
        jQuery.when.apply(jQuery, deferreds).done(function(){
            console.log('All done');
            self.setUpEmptyDashboard();
            jQuery(self.filterButtons[0]).addClass('disabled');
            self.setUpButtons(self.tabs);
            self.setUpButtons(self.filterButtons);
            self.initOptions.controller.setUpButtons();
        });
    };

    $.DashboardView.prototype.setUpButtons = function(list) {
        var self = this;
        list.forEach(function(current) {
            jQuery(current).click( function (evt){
                self.enableAllOthers(list, current);
            });
        });
    };

    $.DashboardView.prototype.enableAllOthers = function(arr, disabled) {
        arr.forEach(function (item) {
            jQuery(item).removeClass('disabled');
        });
        jQuery(disabled).addClass('disabled');
    };

    $.DashboardView.prototype.getSelectedFilterValue = function() {
        return jQuery("button.query-filter.disabled");
    };

    $.DashboardView.prototype.getSelectedTabValue = function() {
        return jQuery("button.user-filter.disabled");
    };

    $.DashboardView.prototype.clearDashboard = function(){
        jQuery('.annotationsHolder').html("");
    };

    $.DashboardView.prototype.updateDashboard = function(offset, pagination_limit, annotationsList, updateStore){
        var self = this;
        if (offset > annotationsList.length) {
            return;
        }
        var startIndex = offset;
        var endIndex = offset+pagination_limit;
        if (endIndex > annotationsList.length) {
            endIndex = annotationsList.length;
        };
        var offsetList = []
        for (var i = startIndex; i < endIndex; i++) {
            var annotation = annotationsList[i];
            var item = self.formatAnnotation(annotation);
            var html = self.initOptions.TEMPLATES.annotationItem(item);
            jQuery('.annotationsHolder').append(html);
            offsetList.push(annotation);
        };
        if (updateStore) {
            self.initOptions.endpoint.loadMoreAnnotations(offsetList);
        };
    };

    $.DashboardView.prototype.formatAnnotation = function(annotation) {
        
        var item = jQuery.extend(true, {}, annotation);
        var self = this;
        
        if (typeof item.updated !== 'undefined')
            item.updated = self.createDateFromISO8601(item.updated);
        
        var authorized = this.initOptions.endpoint.authorize('delete', annotation);
        var updateAuthorized = this.initOptions.endpoint.authorize('update', annotation);
        
        item.authToDeleteButton = authorized;
        item.authToEditButton = updateAuthorized;
        item.authorized = authorized || updateAuthorized;
        
        return item;
    };

    $.DashboardView.prototype.addCreatedAnnotation = function(mediaType, annotation) {
        var self = this;
        var annotationItem = self.formatAnnotation(annotation);
        var html = self.initOptions.TEMPLATES[self.templateTypes[mediaType]](annotationItem);
        jQuery(self.holders[mediaType]).prepend(html);
    };

    $.DashboardView.prototype.updateAnnotation = function(annotation) {
        var self = this;
        var annotationItem = self.formatAnnotation(annotation);
        var date = new Date(annotationItem.updated);
        var dateAgo = jQuery.timeago(date);
        if( jQuery('.annotationModal').length > 0 ) {
            jQuery('.parentAnnotation .annotatedAt').html("last updated " + dateAgo);
            jQuery('.parentAnnotation .annotatedAt').attr("title", date);
            jQuery('.parentAnnotation .body').html(annotationItem.text);
        }

        divObject = '.annotationItem.item-'+annotation.id.toString();

        jQuery(divObject + ' .annotatedAt').html("last updated" + dateAgo);
        jQuery(divObject + ' .annotatedAt').attr("title", date);
        jQuery(divObject + ' .body').html(annotationItem.text);

        tagHtml = ""
        annotationItem.tags.forEach(function(tag){
            tagHtml += "<div class=\"tag side\">" + tag + "</div>"
        });
        jQuery(divObject + ' .tagList').html(tagHtml);
    };

    $.DashboardView.prototype.deleteAnnotation = function(annotation) {
        if (jQuery('.annotationModal').length > 0) {
            jQuery('.annotationModal').remove();
            jQuery('.annotationSection').css('y-scroll', 'scroll');
        }
        divObject = '.annotationItem.item-'+annotation.id.toString();
        jQuery(divObject).remove();
    };

    $.DashboardView.prototype.setUpEmptyDashboard = function() {
    	var self = this;
		var el = self.initOptions.element;
		el.html(self.initOptions.TEMPLATES.annotationSection({
			annotationItems: [],
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
		jQuery('.annotationSection').scroll(function() {
			if(jQuery(this).scrollTop() + jQuery(this).innerHeight() >= this.scrollHeight){
                var offset = self.initOptions.endpoint.getNumOfAnnotationsOnScreen();
                var pagination = self.initOptions.pagination;
                var annotationList = self.initOptions.endpoint.annotationsMasterList;
                self.updateDashboard(offset, pagination, annotationList, true);
			}
		});
    };

    $.DashboardView.prototype.createDateFromISO8601 = function(string) {
		var d, date, offset, regexp, time, _ref;
		regexp = "([0-9]{4})(-([0-9]{2})(-([0-9]{2})" + "(T([0-9]{2}):([0-9]{2})(:([0-9]{2})(\\.([0-9]+))?)?" 
		       + "(Z|(([-+])([0-9]{2}):([0-9]{2})))?)?)?)?";
		d = string.match(new RegExp(regexp));
		offset = 0;
		date = new Date(d[1], 0, 1);
		if (d[3]) {
			date.setMonth(d[3] - 1);
		}
		if (d[5]) {
			date.setDate(d[5]);
		}
		if (d[7]) {
			date.setHours(d[7]);
		}
		if (d[8]) {
			date.setMinutes(d[8]);
		}
		if (d[10]) {
			date.setSeconds(d[10]);
		}
		if (d[12]) {
			date.setMilliseconds(Number("0." + d[12]) * 1000);
		}
		if (d[14]) {
			offset = (Number(d[16]) * 60) + Number(d[17]);
			offset *= (_ref = d[15] === '-') != null ? _ref : {
				1: -1
			};
		}
		offset -= date.getTimezoneOffset();
		time = Number(date) + (offset * 60 * 1000);
		date.setTime(Number(time));
		return date;
	};

	$.DashboardView.prototype.findAnnotationId = function(target, return_target) {
		annotation_id = target.find('.idAnnotation').html();
		// this next part is to double check that idannotation is grabbed from
    	// within the tags and the quotes section
		while (annotation_id === undefined) {
    		target = target.parent();
    		annotation_id = this.viewer.findAnnotationId(target);
    	}
    	if (return_target) {
    		return target;
    	};
		return annotation_id;
	};

	$.DashboardView.prototype.displayModalView = function(annotation) {
		var self = this;
		var annotationItem = self.formatAnnotation(annotation);

		var html = self.initOptions.TEMPLATES.annotationModal(annotationItem);
    	jQuery('.annotationSection').append(html);
    	jQuery('.annotationSection').css('y-scroll', 'hidden');
    	jQuery('.annotationModal #closeModal').click( function (e) {
    		jQuery('.annotationModal').remove();
    		jQuery('.annotationSection').css('y-scroll', 'scroll');
    	});

    	jQuery('.annotationModal button.replybutton').click( function (e) {
    		var button = jQuery(e.target);
    		var positionAdder = {
    			left: button.offset().left,
    			top: button.offset().top,
    		};
    		
    		self.endpoint.openEditorForReply(positionAdder, annotation_id);
       	});

    	jQuery('.parentAnnotation .quoteText').click( function(e){
			jQuery('html, body').animate({
				scrollTop: jQuery(annotation.highlights[0]).offset().top },
				'slow'
			);
    	});

    	jQuery('.parentAnnotation #edit').click(function (e){
    		if (annotationItem.authToEditButton) {
    			self.endpoint.editAnnotation(annotation, jQuery(e.target));
    		};
    	});

		jQuery('.parentAnnotation [data-toggle="confirmation"]').confirmation({
			title: "Would you like to delete your annotation?",
			onConfirm: function (){
				if(annotationItem.authToDeleteButton) {
					self.endpoint.deleteAnnotation(annotation);
				}
			},
		});
	};

	$.DashboardView.prototype.displayReplies = function(replies) {
		var self = this;
        var replies_offset = jQuery('.parentAnnotation').offset().top -jQuery('.annotationModal').offset().top + jQuery('.parentAnnotation').height();
		var replies_height = jQuery(window).height() - jQuery('.replybutton').height() - jQuery('.parentAnnotation').height() - jQuery('.modal-navigation').height();
		jQuery('.repliesList').css('margin-top', replies_offset);
		jQuery('.repliesList').css('height', replies_height);
		
		var final_html = ''
		self.endpoint.list_of_replies = {}
		
		annotations.forEach(function(annotation) {
			var item = self.formatAnnotation(annotation);
			var html = self.initOptions.TEMPLATES.replyItem(item);
			final_html += html;
			self.endpoint.list_of_replies[item.id.toString()] = annotation;
		});
		
		jQuery('.repliesList').html(final_html);
	};

} (AController));