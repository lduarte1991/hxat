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
                "annotationInstructions",
                "importItems",
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
        this.moving = false;
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
            setTimeout(function(){jQuery(button).click();}, 500);
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

    $.DashboardView.prototype.clearDashboard = function() {
        jQuery('.annotationsHolder').html('');
    };

    $.DashboardView.prototype.addPrintButton = function() {
        if (this.initOptions.is_instructor) {
            jQuery('.handleAnnotations').show();
        }
    };

    $.DashboardView.prototype.removePrintButton = function() {
        jQuery('.handleAnnotations').hide();
    };

    $.DashboardView.prototype.printAnnotations = function() {
        var annotations = this.initOptions.controller.endpoint.annotationsMasterList;
        var html = "<style>table, th, td { border: 1px solid black;} table { border-collapse: collapse; } td, th {padding: 10px;} </style><table><tr><th>Username</th><th>Excerpt</th><th>Annotation</th><th>Tag</th><th>Timestamp</th></tr><tr>";
        jQuery.each(annotations, function(index, annotation) {
            html += "<td>" + annotation.user.name + "</td>";
            if (annotation.media === "text") {
                html += "<td>" + annotation.quote + "</td>";
            } else if(annotation.media === "image") {
                html += "<td><img src=\""+annotation.thumb+"\" style=\"max-width: 150px; max-height: 150px;\"/></td>"
            } else if (annotation.media === "video") {
                html += "<td>" + annotation.rangeTime.start + " - " + annotation.rangeTime.end + "</td>";
            }
            
            html += "<td>" + annotation.text + "</td><td>";
            if (annotation.tags && annotation.tags.length > 0) {
                jQuery.each(annotation.tags, function(tagIndex, tagName) {
                    html += tagName + "<br>";
                });
            };
            html += "<td>" + annotation.updated + "</td></tr>";
        });
        html += "</table>";
        var wnd = window.open("about:blank", "", "_blank");
        wnd.document.write(html);
    };

    $.DashboardView.prototype.exportAnnotations = function() {
        var annotations = this.initOptions.controller.endpoint.annotationsMasterList;
        html = "<textarea style='width:600px; height:600px;'>"+ JSON.stringify(annotations, null, 4)+"</textarea>";
        var wnd = window.open("about:blank", "", "_blank");
        wnd.document.write(html);
    };

    $.DashboardView.prototype.importAnnotations = function() {
        var self = this;
        var html = this.initOptions.TEMPLATES.importItems();
        var saved_section_scrolltop = jQuery('.annotationSection').scrollTop();
        jQuery('.annotationSection').append(html).scrollTop(0);
        jQuery('.annotationModal #closeModal').click( function (e) {
            jQuery('.group-wrap').removeClass("hidden");
            jQuery('.filter-options').removeClass("hidden");
            jQuery('.search-bar').removeClass("hidden");
            jQuery('.annotationsHolder').removeClass("hidden");
            jQuery('.annotationModal').remove();
            jQuery('.annotationSection').scrollTop(saved_section_scrolltop);
        });

        jQuery('.annotationModal #importarea').click( function(e) {
            var content = JSON.parse(jQuery('.annotationModal #importItems').val());
            // gets endpoint for image annotations
            var endpoint = self.initOptions.endpoint.endpoint;

            // below checks to see if it's supposed to come from annotator instead
            if (endpoint === undefined) {
                var endpoint = self.initOptions.endpoint.annotator.options;
                endpoint.userid = endpoint.user_id;
            }
            var time= 500;
            jQuery.each(content, function(index, value) {
                value.id = undefined;
                value.collectionId = endpoint.collection_id;
                value.contextId = endpoint.context_id;
                if (value.user.name === endpoint.username) {
                    value.user.id = endpoint.userid;
                }
                if (endpoint.createCatchAnnotation !== undefined) {
                    setTimeout(function(){
                        endpoint.createCatchAnnotation(value);
                    }, time);
                    time +=500;
                } else {
                    setTimeout(function(){
                        self.initOptions.endpoint.annotator.setupAnnotation(value);
                        self.initOptions.endpoint.annotator.publish('annotationCreated', [value]);
                    }, time);
                    time +=500; 
                }
                
            });
            jQuery('.annotationModal #closeModal').trigger('click');
            jQuery('.mirador-osd-refresh-mode').trigger('click');
        });
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
            var annotationItem = self.formatAnnotation(annotation);
            annotationItem.index = i+1;
            if (annotationItem.text === undefined) {
                annotationItem.text = "";
            }
            var html = self.initOptions.TEMPLATES.annotationItem(annotationItem);
            jQuery('.annotationsHolder').append(html);
            divObject = '.annotationItem.item-'+annotation.id.toString();

            var tagHtml = "";
            if (typeof annotationItem.tags !== "undefined") {
                annotationItem.tags.forEach(function(tag){
                    var style = "";
                    if (window.AController.main.tags[tag] !== undefined) {
                        var rgbColor = window.AController.main.tags[tag];
                        style = "style=\"background-color:rgba(" + rgbColor.red + ", " + rgbColor.green + ", " + rgbColor.blue + ", " + rgbColor.alpha + ")\"";
                    };
                    tagHtml += "<div class=\"tag side\" " + style + ">" + tag + "</div>"
                });
            };
            jQuery(divObject + ' .tagList').html(tagHtml);
            offsetList.push(annotation);
        };

        if (updateStore) {
            self.initOptions.endpoint.loadMoreAnnotations(offsetList);
            if (offsetList.length > 0) {
                jQuery('.annotationItem.item-' + offsetList[0].id).focus();
            };
        };
        if (typeof jQuery('img').unveil === "function") {
            jQuery('img').unveil();
        };
        if (annotationsList.length == 0) {
            //jQuery('.annotationsHolder').html('<div style="padding:20px;text-align:center;">There are currently no annotations in this document. Be the first!</div>');
        };
        
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
        } else if (item.media === "video") {
            item.rangeTime.start= typeof vjs !== 'undefined' ?
                vjs.formatTime(item.rangeTime.start) :
                item.rangeTime.start;
            item.rangeTime.end= typeof vjs !== 'undefined'?
                vjs.formatTime(item.rangeTime.end) :
                item.rangeTime.end;
        }
        return item;
    };

    $.DashboardView.prototype.addCreatedAnnotation = function(mediaType, annotation) {
        var self = this;
        var annotationItem = self.formatAnnotation(annotation);
        annotationItem.index = self.initOptions.endpoint.annotationsMasterList.length;
        var html = self.initOptions.TEMPLATES[self.templateTypes[mediaType]](annotationItem);
        if (jQuery('.annotationItem').length == 0) {
            jQuery(self.holders[mediaType]).html('');
        };
        jQuery(self.holders[mediaType]).prepend(html);
        if (typeof jQuery('img').unveil === "function") {
            jQuery('img').unveil('trigger');
        };
        if (annotationItem.media === "comment") {
            var parentId = annotationItem.parent;
            var numReply = parseInt(jQuery('.item-' + parentId).find('.replyNum').html(), 10);
            jQuery('.item-' + parentId).find('.replyNum').html(numReply+1);
        };
        divObject = '.annotationItem.item-'+annotation.id.toString();

        tagHtml = ""
        if (typeof annotationItem.tags !== "undefined") {
            annotationItem.tags.forEach(function(tag){
                var style = "";
                if (window.AController.main.tags[tag] !== undefined) {
                    var rgbColor = window.AController.main.tags[tag];
                    style = "style=\"background-color:rgba(" + rgbColor.red + ", " + rgbColor.green + ", " + rgbColor.blue + ", " + rgbColor.alpha + ")\"";
                };
                tagHtml += "<div class=\"tag side\" " + style + ">" + tag + "</div>"
            });
        };
        jQuery(divObject + ' .tagList').html(tagHtml);
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

        if (typeof annotationItem.tags !== "undefined") {
            annotationItem.tags.forEach(function(tag){
                var style = "";
                if (window.AController.main.tags[tag] !== undefined) {
                    var rgbColor = window.AController.main.tags[tag];
                    style = "style=\"background-color:rgba(" + rgbColor.red + ", " + rgbColor.green + ", " + rgbColor.blue + ", " + rgbColor.alpha + ")\"";
                };
                tagHtml += "<div class=\"tag side\" " + style + ">" + tag + "</div>"
            });
        };
        jQuery(divObject + ' .tagList').html(tagHtml);
    };

    $.DashboardView.prototype.deleteAnnotation = function(annotation) {
        if (jQuery('.annotationModal').length > 0) {
            jQuery('.group-wrap').removeClass("hidden");
            jQuery('.filter-options').removeClass("hidden");
            jQuery('.search-bar').removeClass("hidden");
            jQuery('.annotationsHolder').removeClass("hidden");
            jQuery('.annotationModal').remove();
        }
        var divObject = ""
        if (typeof annotation !== "object") {
            divObject = '.annotationItem.item-'+annotation.toString();
        } else {
            divObject = '.annotationItem.item-'+annotation.id.toString();
        }
        jQuery(divObject).remove();
        if (jQuery('.annotationItem').length == 0) {
            jQuery('.annotationsHolder').html('<div style="padding:20px;text-align:center;">There are currently no annotations in this document. Be the first!</div>')
        };
    };

    $.DashboardView.prototype.setUpEmptyDashboard = function() {
        var self = this;
        var el = self.initOptions.element;
        el.html(self.initOptions.TEMPLATES.annotationSection({
            annotationItems: [],
            show_instructor_tab: self.initOptions.show_instructor_tab,
            show_mynotes_tab: self.initOptions.show_mynotes_tab,
            show_public_tab: self.initOptions.show_public_tab
        }));
        console.log(self.initOptions);
        jQuery('.resize-handle').css('right', jQuery('.annotationSection').css('width'));
        jQuery('.resize-handle.side').on('mousedown', function(e){
            self.resizing = true;
            self.moving = false;
            jQuery('.modal-navigation').removeClass('hidden'); 
            jQuery('.editgroup').removeClass('hidden');
        });
        
        jQuery(document).on('mousemove', function(e){
            if (!self.resizing){
                self.resizing = false;
                self.moving = false;
                return;
            }
            e.preventDefault();
            self.moving = true;
            
            var section = jQuery('.annotationSection');
            var handle = jQuery('.resize-handle');
            section.css('min-width', '0px');
           
            var offset = section.width() - (e.clientX - section.offset().left);
            section.css('width', offset);
            section.css('right', '0px');
            handle.css('right', offset);
            self.lastUp = offset;

        }).on('mouseup', function(e){

            if (!self.resizing || !self.moving) {
                self.resizing = false;
                self.moving = false;
                return;
            };

            self.resizing = false;

            var section = jQuery('.annotationSection');
            var handle = jQuery('.resize-handle');

            if(self.lastUp < 150){
                jQuery('#leftCol').attr('class', 'col-xs-11');
                section.css('width', '0px');
                handle.css('right', '0px');
                section.css('right', '-5px');
                handle.find('i').removeClass('fa-arrow-right');
                handle.find('i').addClass('fa-arrow-left');
                jQuery('.modal-navigation').addClass('hidden'); 
                jQuery('.editgroup').addClass('hidden');

            } else {
                jQuery('#leftCol').attr('class', 'col-xs-7');
                section.css('min-width', '150px');
                section.css('right', '0px');
                handle.find('i').addClass('fa-arrow-right');
                handle.find('i').removeClass('fa-arrow-left');
            }

            jQuery('.test').css('width', section.offset().left);
            window.dispatchEvent(new Event('resize'));
        });
        var loadMore = function(){
            var offset = self.initOptions.endpoint.getNumOfAnnotationsOnScreen();
            var pagination = self.initOptions.pagination;
            var annotationList = self.initOptions.endpoint.annotationsMasterList;
            self.updateDashboard(offset, pagination, annotationList, true);
        };
        jQuery('.annotationSection').scroll(function() {
            if(jQuery(this).scrollTop() + jQuery(this).innerHeight() >= this.scrollHeight){
                loadMore();
            }
        });
        jQuery('#loadMoreButton').click(function(){
            loadMore();
        });
        jQuery('#printAnnotations').click(function(){
            self.printAnnotations();
        });
        jQuery('#exportAnnotations').click(function(){
            self.exportAnnotations();
        });
        jQuery('#importAnnotations').click(function(){
            self.importAnnotations();
        });
        jQuery('.handle-button').click( function(e) {
            if (self.moving) {
                return;
            };
            var section = jQuery('.annotationSection');
            var handle = jQuery('.resize-handle');
            if (parseInt(section.css('width'), 10) >= 150) {
                jQuery('#leftCol').attr('class', 'col-xs-11');
                section.css('min-width', '0px');
                section.css('width', '0px');
                handle.css('right', '0px');
                section.css('right', '-5px');
                jQuery('.modal-navigation').addClass('hidden'); 
                jQuery('.editgroup').addClass('hidden');
            } else {
                jQuery('#leftCol').attr('class', 'col-xs-7');
                section.css('min-width', '150px');
                section.css('width', '300px');
                handle.css('right', '300px');
                section.css('right', '0px');
                jQuery('.modal-navigation').removeClass('hidden'); 
                jQuery('.editgroup').removeClass('hidden');
            }
            handle.find('i').toggleClass('fa-arrow-right');
            handle.find('i').toggleClass('fa-arrow-left');
            
            jQuery('.test').css('width', section.offset().left);
            window.dispatchEvent(new Event('resize'));
        });
        jQuery('.test').css('width', jQuery('.annotationSection').offset().left);
        var evt;
        try {
            console.log("new Event works");
            evt = new Event('resize');
        } catch(e) {
            console.log("new Event doesn't work");
            var evt = window.document.createEvent('UIEvents');
            evt.initUIEvent('resize', true, false, window, 0);
        }
        window.dispatchEvent(evt);
        if (typeof mir !== "undefined" && typeof mir.eventEmitter !== "undefined" && typeof mir.eventEmitter.publish === "function") {
            mir.eventEmitter.subscribe('focusUpdated', function(){
                var viewType = self.initOptions.endpoint.window.currentFocus;
                var section = jQuery('.annotationSection');
                var handle = jQuery('.resize-handle');

                if (viewType === "ImageView") {
                    jQuery('#leftCol').attr('class', 'col-xs-7');
                    section.css('min-width', '150px');
                    section.css('width', '300px');
                    handle.css('right', '300px');
                    section.css('right', '0px');
                    handle.find('i').addClass('fa-arrow-right');
                    handle.find('i').removeClass('fa-arrow-left');
                } else {
                    section.css('min-width', '0px');
                    section.css('width', '0px');
                    handle.css('right', '0px');
                    section.css('right', '-5px');
                    handle.find('i').removeClass('fa-arrow-right');
                    handle.find('i').addClass('fa-arrow-left');
                }
                jQuery('.test').css('width', section.offset().left);
                window.dispatchEvent(new Event('resize'));
            });
        };

        if (self.initOptions.controller.initOptions.dashboard_hidden) {
            var section = jQuery('.annotationSection');
            var handle = jQuery('.resize-handle');
            section.css('min-width', '0px');
            section.css('width', '0px');
            handle.css('right', '0px');
            section.css('right', '-5px');
            handle.find('i').removeClass('fa-arrow-right');
            handle.find('i').addClass('fa-arrow-left');
            jQuery('.test').css('width', section.offset().left);
        };

        if (self.initOptions.controller.initOptions.transcript_hidden) {
            jQuery('#transcript').hide(10, function(){
              jQuery('#viewer').css('height', '100%');
            });
        }

        jQuery(window).resize(function() {
            jQuery('.test').css('width', jQuery('.annotationSection').offset().left);
            if (typeof mir !== "undefined" && typeof mir.eventEmitter !== "undefined" && typeof mir.eventEmitter.publish !== "undefined") {
                mir.eventEmitter.publish('resizeMirador');
            };
            
        });
        jQuery('.handle-button').hover(function() {
            jQuery('.hide_label').css("visibility", "visible");
        },function() {
            jQuery('.hide_label').css("visibility", "hidden");
        });

        if (AController.targetObjectController.initOptions.mediaType === "video") {
            jQuery('#timeRangeFilter').css('display', 'block');
        }

        jQuery('#startTimeFilter').change(function() {
            if (AController.targetObjectController.vid !== undefined) {
                var time = jQuery('#startTimeFilter').val().split(':');
                var timeSecs = 0;
                if (time.length == 3) {
                    timeSecs = parseInt(time[0], 10) * 60 * 60 + parseInt(time[1],10) * 60 + parseInt(time[2], 10);
                } else if (time.length == 2) {
                    timeSecs = parseInt(time[0], 10) * 60 + parseInt(time[1], 10);
                }
                timeSecs = AController.targetObjectController.vid.rangeslider._percent(timeSecs);
                AController.targetObjectController.vid.annotations.rsd.setPosition(0, timeSecs);
            } else {
                console.log("uh oh... or not if this isn't a video");
            }
        });

        jQuery('#endTimeFilter').change(function() {
            if (AController.targetObjectController.vid !== undefined) {
                var time = jQuery('#endTimeFilter').val().split(':');
                var timeSecs = 0;
                if (time.length == 3) {
                    timeSecs = parseInt(time[0], 10) * 60 * 60 + parseInt(time[1],10) * 60 + parseInt(time[2], 10);
                } else if (time.length == 2) {
                    timeSecs = parseInt(time[0], 10) * 60 + parseInt(time[1], 10);
                }
                timeSecs = AController.targetObjectController.vid.rangeslider._percent(timeSecs);
                AController.targetObjectController.vid.annotations.rsd.setPosition(1, timeSecs);
            } else {
                console.log("uh oh... or not if this isn't a video");
            }
        });

        if (window.Annotator !== undefined && window.Annotator.prototype.isPrototypeOf(AController.annotationCore.annotation_tool)) {
            console.log('it was all defined. problem is probably not here.');
            AController.annotationCore.annotation_tool.subscribe('annotationHidden', function(annotationId) {
                jQuery('.annotationItem.item-' + annotationId).hide();
            });
            AController.annotationCore.annotation_tool.subscribe('annotationShown', function(annotationId) {
                jQuery('.annotationItem.item-' + annotationId).show();
            });
        }

        self.initOptions.controller.dashboardReady.resolve();
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
        var saved_section_scrolltop = jQuery('.annotationSection').scrollTop();
        jQuery('.annotationSection').append(html).scrollTop(0);
        jQuery('.group-wrap').addClass("hidden");
        jQuery('.filter-options').addClass("hidden");
        jQuery('.search-bar').addClass("hidden");
        jQuery('.annotationsHolder').addClass("hidden");
        jQuery('.annotationModal #closeModal').focus();
        jQuery('.annotationModal #closeModal').click( function (e) {
            jQuery('.group-wrap').removeClass("hidden");
            jQuery('.filter-options').removeClass("hidden");
            jQuery('.search-bar').removeClass("hidden");
            jQuery('.annotationsHolder').removeClass("hidden");
            jQuery('.annotationModal').remove();
            jQuery('.annotationSection').scrollTop(saved_section_scrolltop);
        });
        jQuery('.annotationModal #hideParent').click( function (e) {
            jQuery('.parentAnnotation').toggleClass("hidden");
        });

        jQuery('.annotationModal button.replybutton').click( function (e) {
            var button = jQuery(e.target);
            var options = {
                left: button.offset().left,
                top: button.offset().top,
                repliesList: jQuery('.repliesList'),
                templateReply: self.initOptions.TEMPLATES.editReplyItem({"isNewAnnotation": false}),
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
            console.log(self.initOptions.endpoint.window.id);
            mir.eventEmitter.publish('fitBounds.' + self.initOptions.endpoint.window.id, annotationItem.rangePosition)
        });

        jQuery('.parentAnnotation .playMediaButton ').click ( function(e) {
            var player = AController.targetObjectController.vid;
            player.annotator = AController.annotationCore.annotation_tool;
            //player.annotations.showAnnotation(annotation);
            var playFunction = function() {
                // Fix problem with youtube videos in the first play. The plugin don't have this trigger
                if (player.techName === 'Youtube') {
                    var startAPI = function() {
                        player.annotations.showAnnotation(annotation);
                    }
                    if (player.annotations.loaded)
                        startAPI();
                    else
                        player.one('loadedRangeSlider', startAPI); // show Annotations once the RangeSlider is loaded
                } else {
                    player.annotations.showAnnotation(annotation);
                }
            };
            if (player.paused()) {
                player.play();
                player.one('playing', playFunction);
            } else {
                playFunction();
            }
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

    $.DashboardView.prototype.sortAnnotationsByCreated = function(annotations) {
        var compareCreated = function(a, b) {
            if (!("created" in a && "created" in b)) {
                return 0;
            }
            // get the ISO8601 time w/o the TZ so it's parseable by Date()
            // and then compare the millisecond values.
            // Ex: "2015-09-22T16:30:00 UTC" => Date.parse("2015-09-22T16:30:00") => 1442939400000
            t1 = Date.parse(a.created.split(' ', 2)[0]);
            t2 = Date.parse(b.created.split(' ', 2)[0]);
            return t1 > t2;
        };

        sorted_annotations = (annotations||[]).slice(); // shallow copy to preserve order of original array
        sorted_annotations.sort(compareCreated); // sort in place
        return sorted_annotations;
    };

    $.DashboardView.prototype.displayReplies = function(replies_unsorted) {
        var self = this;
        var replies = self.sortAnnotationsByCreated(replies_unsorted);
        
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
    };

    $.DashboardView.prototype.displayInstructions = function (instructions) {
        var self = this;
        var html = self.initOptions.TEMPLATES.annotationInstructions({'data':instructions});
        jQuery('.annotationSection').append(html);
        jQuery('.annotationModal #closeModal').focus();
        jQuery('.annotationModal #closeModal').click( function (e) {
            jQuery('.annotationModal').remove();
        });
    };

    $.DashboardView.prototype.toggleFullscreen = function () {
        var self = this;
        var enterFullscreen = function() {
          var el = document.documentElement;
          if (el.requestFullscreen) {
            el.requestFullscreen();
          } else if (el.mozRequestFullScreen) {
            el.mozRequestFullScreen();
          } else if (el.webkitRequestFullscreen) {
            el.webkitRequestFullscreen(Element.ALLOW_KEYBOARD_INPUT);
          } else if (el.msRequestFullscreen) {
            el.msRequestFullscreen();
          }
        };

        var exitFullscreen = function() {
            if (document.exitFullscreen) {
                document.exitFullscreen();
            } else if (document.mozCancelFullScreen) {
                document.mozCancelFullScreen();
            } else if (document.webkitExitFullscreen) {
                document.webkitExitFullscreen();
            }
            
        };

        var isFullscreen = function() {
          var $fullscreen = $(fullscreenElement());
          return ($fullscreen.length > 0);
        };

        var fullscreenElement = function() {
            return (document.fullscreenElement || document.mozFullScreenElement || document.webkitFullscreenElement);
        };

        fullscreenElement() ? exitFullscreen() : enterFullscreen();
    };

    $.DashboardView.prototype.annotationViaKeyboardInput = function(){
        var self = this;
        var html = self.initOptions.TEMPLATES.editReplyItem({"isNewAnnotation": true});
        jQuery('.annotationSection').append(html);
        jQuery('.annotationModal #closeModal').click( function (e) {
            jQuery('.annotationModal').remove();
            jQuery('#keyboard-input-button').css('color', 'white');
            jQuery('#keyboard-input-button')[0].focus();
        });
        jQuery('.annotationModal textarea')[0].focus();
    };

} (AController));
