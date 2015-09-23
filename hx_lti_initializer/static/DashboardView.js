(function($) {
    $.DashboardView = function(options) {
        var defaultOptions = {
            // set up template names that will be pulled
            TEMPLATENAMES: [
                "annotationSection",
                "annotationItem",
                "annotationModal",
                "replyItem",
                "editReplyItem",
                'annotationInstructions',
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
            'comment': 'replyItem',
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
            self.setUpEmptyDashboard();
            self.setUpButtons(self.tabs);
            self.setUpButtons(self.filterButtons);
            self.initOptions.controller.setUpButtons();
            jQuery(self.filterButtons[0]).addClass('disabled');
            var button = '#' + self.initOptions.default_tab.toLowerCase().replace(' ', '');
            jQuery(button).addClass('disabled');
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
        jQuery('img').unveil();
    };

    $.DashboardView.prototype.formatAnnotation = function(annotation) {
        
        var item = jQuery.extend(true, {}, annotation);
        var self = this;
        
        if (typeof item.updated !== 'undefined')
            item.updated = self.createDateFromISO8601(item.updated);
        
        var authorized = this.initOptions.endpoint.authorize('delete', annotation);
        var updateAuthorized = this.initOptions.endpoint.authorize('update', annotation);
        var is_instructor = this.initOptions.controller.initOptions.is_instructor === "True";
        item.authToDeleteButton = authorized || is_instructor;
        item.authToEditButton = updateAuthorized || is_instructor;
        item.authorized = authorized || updateAuthorized || is_instructor;
        item.thumbnail = false;
        if (item.media === "image" && item.thumb) {
            item.thumbnail = item.thumb;
        }
        return item;
    };

    $.DashboardView.prototype.addCreatedAnnotation = function(mediaType, annotation) {
        var self = this;
        var annotationItem = self.formatAnnotation(annotation);
        var html = self.initOptions.TEMPLATES[self.templateTypes[mediaType]](annotationItem);
        jQuery(self.holders[mediaType]).prepend(html);
        if (annotationItem.media === "comment") {
            var parentId = annotationItem.parent;
            var numReply = parseInt(jQuery('.item-' + parentId).find('.replyNum').html(), 10);
            jQuery('.item-' + parentId).find('.replyNum').html(numReply+1);
        };
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
        var divObject = ""
        if (typeof annotation !== "object") {
            divObject = '.annotationItem.item-'+annotation.toString();
        } else {
            divObject = '.annotationItem.item-'+annotation.id.toString();
        }
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
				section.css('width', '10px');
				section.css('right', 0);
			} else {
				jQuery('#leftCol').attr('class', 'col-xs-7');
				section.css('min-width', '150px');
			}
            jQuery('.test').css('width', section.offset().left);
            window.dispatchEvent(new Event('resize'));
		});
		jQuery('.annotationSection').scroll(function() {
			if(jQuery(this).scrollTop() + jQuery(this).innerHeight() >= this.scrollHeight){
                var offset = self.initOptions.endpoint.getNumOfAnnotationsOnScreen();
                var pagination = self.initOptions.pagination;
                var annotationList = self.initOptions.endpoint.annotationsMasterList;
                self.updateDashboard(offset, pagination, annotationList, true);
			}
		});
        jQuery('.handle-button').click( function(e) {
            var section = jQuery('.annotationSection');
            if (parseInt(section.css, 10) >= 150) {
                jQuery('#leftCol').attr('class', 'col-xs-11');
                section.css('min-width', '10px');
                section.css('width', '10px');
            } else {
                jQuery('#leftCol').attr('class', 'col-xs-7');
                section.css('min-width', '150px');
                section.css('width', '300px');
            }
            jQuery('.test').css('width', section.offset().left);
            window.dispatchEvent(new Event('resize'));
        });
        jQuery('.test').css('width', jQuery('.annotationSection').offset().left);
        window.dispatchEvent(new Event('resize'));
        if (typeof jQuery.subscribe === 'function') {
            jQuery.subscribe('windowUpdated', function(){
                var viewType = self.initOptions.endpoint.window.currentFocus;
                var section = jQuery('.annotationSection');

                if (viewType === "ImageView") {
                    jQuery('#leftCol').attr('class', 'col-xs-7');
                    section.css('min-width', '150px');
                    section.css('width', '300px');
                } else {
                    section.css('min-width', '10px');
                    section.css('width', '10px');
                }
                jQuery('.test').css('width', section.offset().left);
                window.dispatchEvent(new Event('resize'));
            });
        };
        jQuery(window).resize(function() {
            jQuery('.test').css('width', jQuery('.annotationSection').offset().left);
        })
        
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
		if (annotation_id === undefined) {
            if (return_target) {
                return this.findAnnotationId(target.parent(), true);
            } else {
    		    return this.findAnnotationId(target.parent(), false);
            }
    	}

    	if (return_target) {
    		return target;
    	};
		return annotation_id;
	};

	$.DashboardView.prototype.displayModalView = function(annotation, boundCallback) {
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
    		var options = {
    			left: button.offset().left,
    			top: button.offset().top,
                repliesList: jQuery('.repliesList'),
                templateReply: self.initOptions.TEMPLATES.editReplyItem(),
                onSuccess: boundCallback,
    		};
    		
    		self.initOptions.endpoint.openEditorForReply(options);
       	});

    	jQuery('.parentAnnotation .quoteText').click( function(e){
			jQuery('html, body').animate({
				scrollTop: jQuery(annotation.highlights[0]).offset().top },
				'slow'
			);
    	});

        jQuery('.parentAnnotation .zoomToImageBounds').click( function(e){
            jQuery.publish('fitBounds.' + self.initOptions.endpoint.window.id, annotationItem.bounds)
        });

    	jQuery('.parentAnnotation #edit').click(function (e){
    		if (annotationItem.authToEditButton) {
    			self.initOptions.endpoint.editAnnotation(annotation, jQuery(e.target));
    		};
    	});
		jQuery('.parentAnnotation [data-toggle="confirmation"]').confirmation({
			title: "Would you like to delete your annotation?",
            placement: 'left',
			onConfirm: function (){
				if(annotationItem.authToDeleteButton) {
					self.initOptions.endpoint.deleteAnnotation(annotation);
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
		
		var final_html = '';
        self.initOptions.endpoint.list_of_replies = {};

		
		replies.forEach(function(annotation) {
			var item = self.formatAnnotation(annotation);
			var html = self.initOptions.TEMPLATES.replyItem(item);
			final_html += html;
			self.initOptions.endpoint.list_of_replies[item.id.toString()] = annotation;
		});
		
		jQuery('.repliesList').html(final_html);
        if (replies.length > 0) {
            var parentId = replies[0].parent;
            jQuery('.item-' + parentId).find('.replyNum').html(replies.length);
        };

        jQuery(window).resize(function(){
            var replies_height = jQuery(window).height() - jQuery('.replybutton').height() - jQuery('.parentAnnotation').height() - jQuery('.modal-navigation').height();
            jQuery('.repliesList').css('height', replies_height);
        });
	};

    $.DashboardView.prototype.displayInstructions = function (instructions) {
        var self = this;
        var html = self.initOptions.TEMPLATES.annotationInstructions({'data':instructions});
        jQuery('.annotationSection').append(html);
        jQuery('.annotationModal #closeModal').click( function (e) {
            jQuery('.annotationModal').remove();
            jQuery('.annotationSection').css('y-scroll', 'scroll');
        });
    };

} (AController));