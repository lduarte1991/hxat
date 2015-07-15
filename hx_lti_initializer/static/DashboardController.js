(function($) {
	$.DashboardController = function(options, commonInfo) {
		var defaultOptions = {
			media: commonInfo.mediaType,
			userId: commonInfo.user_id,
			externalLink: false,
			showMediaSelector: true,
			showPublicPrivate: true,
			pagination: 50,
			flags: false,
		}

		this.TEMPLATENAMES = [
            "annotationList", // Main
            "annotationPublicPrivate", // Main->PublicPrivate
            "annotationPublicPrivateInstructor", // Main->PublicPrivateInstructor
            "annotationMediaSelector", // Main->MediaSelector
            "annotationItem", // Main->ContainerRow
            "annotationReply", // Main->ContainerRow->Reply
            "annotationRow", // Main->ContainerRow->Row
            "annotationDetail", // Main->ContainerRow->DetailRow
        ];

		// HTMLElement that contains what should be annotated
		this.element = options.annotationElement;
		this.clean = false;

		// contains any other options needed to initialize the tool
		this.initOptions = jQuery.extend({}, defaultOptions, options.initOptions, commonInfo);
        this.current_tab = this.initOptions.default_tab;
        var self = this;
		jQuery( document ).ready(function() {
            self.init();
            self.refreshCatch(true);
            var moreBut = self.element.find('.annotationListButtons .moreButtonCatch');
            moreBut.hide(); 
        });
	};

	/* init
	 * 
	 */
	$.DashboardController.prototype.init = function(){
		// annotator
        var wrapper = jQuery('.annotator-wrapper').parent()[0];
        var annotator = jQuery.data(wrapper, 'annotator');
        this.annotator = annotator;

        // Subscribe to annotator
        this._subscribeAnnotator();

        this.TEMPLATES = {};
        this._compileTemplates();

	};

    /**
     * This function makes sure that the annotations loaded are only the ones that we are
     * currently looking for. Annotator has a habit of loading the user's annotations
     * immediately without checking to see if we are doing some filtering or otherwise.
     * Since it's a vendor file, this is the workaround for that bug.
     */
    $.DashboardController.prototype.cleanUpAnnotations = function(){
        var annotator = this.annotator;
        var store = annotator.plugins.Store;
        var annotations = store.annotations;
        var self = this;
        
        // goes through all the annotations currently loaded
        jQuery.each(annotations, function(key, value){
            // if the options.userID (i.e. the value we are searching for) is empty signifying
            // public or is equal to the person with update access, then we leave it alone,
            // otherwise we need to clean them up (i.e. disable them).
            if (self.initOptions.user_id !== '' && self.initOptions.user_id !== value.permissions.update[0]) {
                if (value.highlights !== undefined) {
                    jQuery.each(value.highlights, function(key1, value1){
                        jQuery(value1).removeClass('annotator-hl');
                    });
                }
            }
        });
    };



    $.DashboardController.prototype.changeMedia = function(media) {
        var media = media || 'text';
        this.initOptions.mediaType = media;
        this._refresh();
        this.refreshCatch(true);
        this.checkTotAnnotations();
    };

    $.DashboardController.prototype.changeUserId = function(userId) {
        var userId = userId || '';
        this.initOptions.user_id = userId;
        this._refresh();
        this.refreshCatch(true);
        this.checkTotAnnotations();
    };

    /**
     * This function makes sure that the annotations loaded are only the ones that we are
     * currently looking for. Annotator has a habit of loading the user's annotations
     * immediately without checking to see if we are doing some filtering or otherwise.
     * Since it's a vendor file, this is the workaround for that bug.
     */
    $.DashboardController.prototype.cleanUpAnnotations = function(){
        var annotator = this.annotator;
        var store = annotator.plugins.Store;
        var annotations = store.annotations;
        var self = this;
        
        // goes through all the annotations currently loaded
        jQuery.each(annotations, function(key, value){
            // if the options.userID (i.e. the value we are searching for) is empty signifying
            // public or is equal to the person with update access, then we leave it alone,
            // otherwise we need to clean them up (i.e. disable them).
            if (self.initOptions.user_id !== '' && self.initOptions.user_id !== value.permissions.update[0]) {
                if (value.highlights !== undefined) {
                    jQuery.each(value.highlights, function(key1, value1){
                        jQuery(value1).removeClass('annotator-hl');
                    });
                }
            }
        });
    };

    $.DashboardController.prototype.loadAnnotations = function() {
        var annotator = this.annotator;
        var loadFromSearch = annotator.plugins.Store.options.loadFromSearch;
        var loadedAn = this.element.find('.annotationList .annotationItem').length;
        loadedAn = typeof loadedAn !== 'undefined' ?loadedAn:0;
        
        loadFromSearch.limit = this.initOptions.pagination;
        loadFromSearch.offset = loadedAn;
        loadFromSearch.media = this.initOptions.mediaType;
        loadFromSearch.userid = this.initOptions.user_id;
        
        // Dani had this for some reason. we can't remember. but if something
        // breaks, uncomment next line.
        // annotator.plugins['Store'].loadAnnotationsFromSearch(loadFromSearch);
        
        // Make sure to be openned all annotations for this pagination
        loadFromSearch.limit = this.initOptions.pagination+loadedAn;
        loadFromSearch.offset = 0;
        annotator.plugins['Store'].loadAnnotationsFromSearch(loadFromSearch);
        
        // text loading annotations
        var moreBut = this.element.find('.annotationListButtons .moreButtonCatch');
        moreBut.html('Please wait, loading...');
    },
            
    // check whether is necessary to have a more button or not
    $.DashboardController.prototype.checkTotAnnotations = function() {
        var annotator = this.annotator;
        var loadFromSearch = annotator.plugins.Store.options.loadFromSearch;
        var oldLimit = loadFromSearch.limit;
        var oldOffset = loadFromSearch.offset;
        var self = this;
            
        loadFromSearch.limit = 0;
        loadFromSearch.offset = 0;
        loadFromSearch.media = this.initOptions.mediaType;
        loadFromSearch.userid = this.initOptions.user_id;
        var onSuccess = function(response) {
            var totAn = self.element.find('.annotationList .annotationItem').length;
            var maxAn = response.total;
            var moreBut = self.element.find('.annotationListButtons .moreButtonCatch');
            if (totAn<maxAn && totAn > 0)
                moreBut.show();
            else
                moreBut.hide();
        }
        
        var obj = loadFromSearch;
        var action = 'search';
    
        var id, options, url;
        id = obj && obj.id;
        url = annotator.plugins['Store']._urlFor(action, id);
        options = annotator.plugins['Store']._apiRequestOptions(action, obj, onSuccess);
        jQuery.ajax(url, options);
        
        // reset values
        loadFromSearch.limit = oldLimit;
        loadFromSearch.offset = oldOffset;
        
        // set More button text
        var moreBut = this.element.find('.annotationListButtons .moreButtonCatch');
        moreBut.html('More');
        
    },

	$.DashboardController.prototype._subscribeAnnotator = function() {
        var self = this;
        var annotator = this.annotator;
        // Subscribe to Annotator changes
        annotator.subscribe("annotationsLoaded", function (annotations) {
            self.cleanUpAnnotations();
            self.refreshCatch(self.clean);
            // hide or show more button
            self.checkTotAnnotations();
        });
        annotator.subscribe("annotationUpdated", function (annotation) {
            self.refreshCatch(true);
            self.checkTotAnnotations();
        });
        annotator.subscribe("annotationDeleted", function (annotation) {
            var annotations = annotator.plugins['Store'].annotations;
            var tot = typeof annotations !== 'undefined' ?annotations.length : 0;
            var attempts = 0; // max 100
            if(annotation.media === "image") {
                self.refreshCatch(true);
                self.checkTotAnnotations();
            } else {
            // This is to watch the annotations object, to see when is deleted the annotation
                var ischanged = function() {
                    var new_tot = annotator.plugins['Store'].annotations.length;
                    if (attempts<100)
                        setTimeout(function() {
                            if (new_tot !== tot) {
                                self.refreshCatch(true);
                                self.checkTotAnnotations();
                            } else {
                                attempts++;
                                ischanged();
                            }
                        }, 100); // wait for the change in the annotations
                };
                ischanged();
            }
        });
        annotator.subscribe("annotationCreated", function (annotation) {
            var attempts = 0; // max 100
            // There is a delay between calls to the backend--especially reading after
            // writing. This function listens to when a function is created and waits
            // until the server provides it with an annotation id before doing anything
            // with it. 
            var ischanged = function(){
                if (attempts<100)
                    setTimeout(function() {
                        if (typeof annotation.id !== 'undefined'){
                        
                            // once it gets the annotation id, the table refreshes to show
                            // the edits
                            self.refreshCatch();
                            if (typeof annotation.parent !== 'undefined' && annotation.parent !== '0'){
                                
                                // if annotation made was actually a replay to an annotation
                                // i.e. the only difference is that annotations that are
                                // not replies have no "parent"
                                var replies = jQuery("[annotationid="+annotation.parent+"]").find(".controlReplies .hideReplies");
                                
                                // forces "Show replies" section to show and then refreshes
                                // via two clicks
                                replies.show();
                                replies.click();
                                replies.click();
                            }
                        } else {
                            attempts++;
                            ischanged();
                        }
                    }, 100); // wait for annotation id
            };
            ischanged();
        });
    };

    $.DashboardController.prototype._compileTemplates = function(templateList){
    	var self = this;
    	self.TEMPLATENAMES.forEach(function(templateName) {
    		var template_url = self.initOptions.template_urls + templateName + '.html';
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
    
    $.DashboardController.prototype.__bind = function(fn, me) { return function(){ return fn.apply(me, arguments); }; };

    $.DashboardController.prototype._isInList = function (an){
        var annotator = this.annotator;
        var isInList = false;
        var list = jQuery('#dashboard .annotationList .annotationRow.item');
        for (_i = 0, _len = list.length; _i < _len; _i++) {
             if (parseInt(jQuery(list[_i]).parent().attr('annotationid'), 10) === an.id)
                  isInList = true;
        }
        return isInList;
    };

    $.DashboardController.prototype._formatCatch = function(item) {
        var item = item || {};
        
        if (this._isVideoJS(item)) {
            // format time
            item.rangeTime.start= typeof vjs !== 'undefined' ?
                vjs.formatTime(item.rangeTime.start) :
                item.rangeTime.start;
            item.rangeTime.end= typeof vjs !== 'undefined'?
                vjs.formatTime(item.rangeTime.end) :
                item.rangeTime.end;
        }
        // format date
        if (typeof item.updated !== 'undefined' && typeof createDateFromISO8601 !== 'undefined')
            item.updated = createDateFromISO8601(item.updated);
        // format geolocation
        if (typeof item.geolocation !== 'undefined' && (typeof item.geolocation.latitude === 'undefined' || item.geolocation.latitude === ''))
            delete item.geolocation;
        
        /* NEW VARIABLES */
        // set plainText for Catch
        item.plainText = item.text.replace(/&(lt|gt);/g, function (strMatch, p1){
            return (p1 === "lt")? "<" : ">";
        }); // Change to < and > tags
        item.plainText = item.plainText.replace(/<\/?[^>]+(>|$)/g, "").replace('&nbsp;', ''); // remove all the html tags
        
        item.mediatypeforgrid = {};
        item.mediatypeforgrid[item.media] = true;

        if (item.mediatypeforgrid.image) {
            item.thumbnailLink = item.target.thumb;
        };

        // Flags
        if (!this.initOptions.flags && typeof item.tags !== 'undefined' && item.tags.length > 0) {
            for (var len = item.tags.length, index = len-1; index >= 0; --index) {
                var currTag = item.tags[index];
                if (currTag.indexOf("flagged-") !== -1) {
                    item.tags.splice(index);
                }
            }
        }
    };

    $.DashboardController.prototype._isVideoJS = function (an) {
        var annotator = this.annotator;
        var rt = an.rangeTime;
        var isOpenVideojs = (typeof annotator.mplayer !== 'undefined');
        var isVideo = (typeof an.media !== 'undefined' && an.media === 'video');
        var isNumber = (typeof rt !== 'undefined' && !isNaN(parseFloat(rt.start)) && isFinite(rt.start) && !isNaN(parseFloat(rt.end)) && isFinite(rt.end));
        return (isOpenVideojs && isVideo && isNumber);
    };

    $.DashboardController.prototype.getTemplate = function(templateName) {
        return this.TEMPLATES[templateName]() || '';
    };

    $.DashboardController.prototype.refreshCatch = function(newInstance) {
        var mediaType = this.initOptions.mediaType || 'text';
        var annotationItems = [];
        var index = 0;
        var annotations = this.annotator.plugins['Store'].annotations || [];
        var el = jQuery("#dashboard.annotationListContainer");
        var self = this;
        var newInstance = newInstance || false;
        annotations.forEach(function(annotation) {
            var isMedia = annotation.media === self.initOptions.mediaType;
            var isUser = (typeof self.initOptions.user_id !== 'undefined' && self.initOptions.user_id !== '' && self.initOptions.user_id !== null)?
                    self.initOptions.user_id === annotation.user.id:true;
            var isInList = newInstance?false:self._isInList(annotation);
            if (isMedia && isUser && !isInList) {
                var item = jQuery.extend(true, {}, annotation);
                self._formatCatch(item);
                
                // Authorized
                var permissions = self.annotator.plugins.Permissions;
                var authorized = permissions.options.userAuthorize('delete', annotation, permissions.user);
                var updateAuthorized = permissions.options.userAuthorize('update', annotation, permissions.user);
                
                item.authToDeleteButton = authorized;
                item.authToEditButton = updateAuthorized;
                item.hasReplies = (item.totalComments > 0);
                item.root = self.initOptions.imageRootUrl;
                var html = self.TEMPLATES.annotationItem({
                    item: item,
                    id: item.id,
                    evenOrOdd: index % 2 ? "odd" : "even",
                    openOrClosed: "closed",
                    annotationRow: self.TEMPLATES.annotationRow(item),
                    annotationDetail: self.TEMPLATES.annotationDetail(item),
                });
                index++;
                annotationItems.push(html);
            }
        });
        
        if (newInstance) {
            var videoFormat = (mediaType === "video") ? true : false;
            var publicPrivateTemplate = '';
            if (self.initOptions.showPublicPrivate) {
                var templateName = this.initOptions.instructor_email ? 
                    "annotationPublicPrivateInstructor" : 
                    "annotationPublicPrivate";
            }
            el.html(self.TEMPLATES.annotationList({ 
                annotationItems: annotationItems, 
                videoFormat: videoFormat,
                PublicPrivate: this.getTemplate(templateName),
                MediaSelector: self.initOptions.showMediaSelector?self.TEMPLATES.annotationMediaSelector():'',
            }));
        } else {
            var list = jQuery("#dashboard .annotationList");
            annotationItems.forEach(function(annotation) {
                list.append(jQuery(annotation));
            });
        }
        
        // Set SelButtons to media
        var SelButtons = el.find('.annotationList li').removeClass('active'); // reset
        for (var index=0;index<SelButtons.length;index++) {
            var span = jQuery(SelButtons[index]);
            if (span.attr("media") === this.initOptions.mediaType) jQuery(SelButtons[index]).addClass('active');
        }
        // Set PublicPrivate
        var PublicPrivateButtons = el.find('.annotationListButtons .PublicPrivate').removeClass('active'); // reset
        for (var index=0;index<PublicPrivateButtons.length;index++) {
            var span = jQuery(PublicPrivateButtons[index]).find('span');
            if (span.html().toLowerCase() === self.current_tab.toLowerCase()) {
                switch (self.current_tab.toLowerCase()){
                    case 'public':
                        self.initOptions.user_id = '';
                        break;
                    case 'instructor':
                        self.initOptions.user_id = 'c8720cac6c7f59380abeb5f7758b6882065124a5';//this.initOptions.instructor_email;
                        break;
                    default:
                        self.initOptions.user_id = this.annotator.plugins.Permissions.user.id;
                        break;
                }
                jQuery(PublicPrivateButtons[index]).addClass('active');
            }
        }
        
        // reset all old events
        el.off();
        
        // Bind functions
        var openAnnotationItem = this.__bind(this._openAnnotationItem, this);
        var closeAnnotationItem = this.__bind(this._closeAnnotationItem, this);
        var onGeolocationClick = this.__bind(this._onGeolocationClick, this);
        var onPlaySelectionClick = this.__bind(this._onPlaySelectionClick, this);
        var onShareControlsClick = this.__bind(this._onShareControlsClick, this);
        var onSelectionButtonClick = this.__bind(this._onSelectionButtonClick, this);
        var onPublicPrivateButtonClick = this.__bind(this._onPublicPrivateButtonClick, this);
        var onQuoteMediaButton = this.__bind(this._onQuoteMediaButton, this);
        var onControlRepliesClick = this.__bind(this._onControlRepliesClick, this);
        var onMoreButtonClick = this.__bind(this._onMoreButtonClick, this);
        var onSearchButtonClick = this.__bind(this._onSearchButtonClick, this);
        var onClearSearchButtonClick = this.__bind(this._onClearSearchButtonClick, this);
        var onDeleteReplyButtonClick = this.__bind(this._onDeleteReplyButtonClick, this);
        var onZoomToImageBoundsButtonClick = this.__bind(this._onZoomToImageBoundsButtonClick, this);
        var openLoadingGIF = this.__bind(this.openLoadingGIF, this);
        //Open Button
        el.on("click", ".annotationItem .annotationRow", openAnnotationItem);
        // Close Button
        el.on("click", ".annotationItem .detailHeader", closeAnnotationItem);
        // Geolocation button
        el.on("click", ".annotationItem .detailHeader .geolocationIcon img", onGeolocationClick);
        // controlPanel buttons
        el.on("click", ".annotationItem .annotationDetail .controlPanel", onShareControlsClick);
        // VIDEO
        if (this.initOptions.mediaType === 'video') {
            // PlaySelection button
            el.on("click", ".annotationItem .annotationDetail .playMediaButton", onPlaySelectionClick);
        }
        // TEXT
        if (this.initOptions.mediaType === 'text') {
            // PlaySelection button
            el.on("click", ".annotationItem .annotationDetail .quote", onQuoteMediaButton);
        }

        // IMAGE
        if (this.initOptions.mediaType === 'image') {
            // PlaySelection button
            el.on("click", ".annotationItem .annotationDetail .zoomToImageBounds", onZoomToImageBoundsButtonClick);
        }
        
        // controlReplies
        el.on("click", ".annotationItem .controlReplies", onControlRepliesClick);
        
        // Selection Buttons
        el.on("click", ".annotationList li", onSelectionButtonClick);
        // PublicPrivate Buttons
        el.on("click", ".annotationListButtons .PublicPrivate", onPublicPrivateButtonClick);
        // More Button
        el.on("click", ".annotationListButtons .moreButtonCatch", onMoreButtonClick);
        
        // Search Button
        el.on("click", ".searchbox .search-icon", onSearchButtonClick);
        // Search should also run when user hits ENTER
        jQuery('input[name=search]').keyup(function(e) {
            // ENTER == 13
            if(e.which == 13) {
                onSearchButtonClick();
            }
        });

        // Clear Search Button
        el.on("click", ".searchbox .clear-search-icon", onClearSearchButtonClick);
        
        // Delete Reply Button
        el.on("click", ".replies .replyItem .deleteReply", onDeleteReplyButtonClick);
        
        el.on("click", ".annotationListButtons .PublicPrivate", openLoadingGIF);
    };

    $.DashboardController.prototype._openAnnotationItem = function(evt) {
        var isClosed = jQuery(evt.currentTarget).closest(".annotationItem").hasClass("closed");
        if (isClosed) {
            jQuery(evt.currentTarget).closest(".annotationItem").removeClass("closed").addClass("open");
            // Add Share button
            /*var shareControl = jQuery(evt.currentTarget).closest(".annotationItem").find('.annotationDetail .controlPanel:first'),
                annotator = this.annotator,
                idAnnotation = shareControl.parent().find('.idAnnotation').html(),
                uri = shareControl.parent().find('.uri').html();*/
            // remove the last share container
            //shareControl.find('.share-container-annotator').remove();
            //shareControl.append(annotator.plugins.Share.buildHTMLShareButton("", idAnnotation));
            // Set actions button
            //annotator.plugins.Share.buttonsActions(shareControl[0], 1, uri);
        } else {
            jQuery(evt.currentTarget).closest(".annotationItem").removeClass("open").addClass("closed");
        }
    };

   $.DashboardController.prototype._closeAnnotationItem = function(evt) {
        var existEvent = typeof evt.target !== 'undefined' && typeof evt.target.localName !== 'undefined';
        if (existEvent && evt.target.parentNode.className !== 'geolocationIcon') {
            this._openAnnotationItem(evt);
        }
   };

   $.DashboardController.prototype._onQuoteMediaButton = function(evt) {
        var quote = jQuery(evt.target).hasClass('quote')?jQuery(evt.target):jQuery(evt.target).parents('.quote:first');
        var id = parseInt(quote.find('.idAnnotation').html(), 10);
        var uri = quote.find('.uri').html();
        if (typeof id === 'undefined' || id === ''){
            this.refreshCatch();
            this.checkTotAnnotations();
            id = quote.find('.idAnnotation').html();
            // clickPlaySelection(evt);
        }
        if (this.initOptions.externalLink) {
            uri += (uri.indexOf('?') >= 0)?'&ovaId='+id:'?ovaId='+id;
            location.href = uri;
        } else {
            var allannotations = this.annotator.plugins['Store'].annotations;
            var ovaId = id;
            for (var item in allannotations) {
                var an = allannotations[item];
                if (typeof an.id !== 'undefined' && an.id === ovaId) { // this is the annotation
                    if(!this._isVideoJS(an)) {

                        var hasRanges = typeof an.ranges !== 'undefined' && typeof an.ranges[0] !== 'undefined',
                            startOffset = hasRanges?an.ranges[0].startOffset:'',
                            endOffset = hasRanges?an.ranges[0].endOffset:'';

                        if (typeof startOffset !== 'undefined' && typeof endOffset !== 'undefined' && typeof an.highlights) { 

                            jQuery(an.highlights).parent().find('.annotator-hl').removeClass('api'); 
                            // change the color
                            jQuery(an.highlights).addClass('api'); 
                            // animate to the annotation
                            jQuery('html, body').animate({
                                scrollTop: jQuery(an.highlights[0]).offset().top},
                                'slow');
                        }
                    }
                }
            }
        }
    };

    $.DashboardController.prototype._onPlaySelectionClick = function(evt) {
        var id = parseInt(jQuery(evt.target).find('.idAnnotation').html(), 10);
        var uri = jQuery(evt.target).find('.uri').html();
        var container = jQuery(evt.target).find('.container').html();
        if (this.initOptions.externalLink) {
            uri += (uri.indexOf('?') >= 0) ? '&ovaId=' + id : '?ovaId=' + id;
            location.href = uri;
        } else {
            var isContainer = typeof this.annotator.an !== 'undefined' && typeof this.annotator.an[container] !== 'undefined';
            var ovaInstance = isContainer ? this.annotator.an[container] : null;
            if (ovaInstance !== null) {
                var allannotations = this.annotator.plugins['Store'].annotations,
                    ovaId = id,
                    player = ovaInstance.player;

                for (var item in allannotations) {
                    var an = allannotations[item];
                    if (typeof an.id !== 'undefined' && an.id === ovaId) { // this is the annotation
                        if (this._isVideoJS(an)) { // It is a video
                            if (player.id_ === an.target.container && player.tech.options_.source.src === an.target.src) {
                                var anFound = an;

                                var playFunction = function(){
                                    // Fix problem with youtube videos in the first play. The plugin don't have this trigger
                                    if (player.techName === 'Youtube') {
                                        var startAPI = function() {

                                            ovaInstance.showAnnotation(anFound);
                                        }
                                        if (ovaInstance.loaded)
                                            startAPI();
                                        else
                                            player.one('loadedRangeSlider', startAPI); // show Annotations once the RangeSlider is loaded
                                    } else {

                                        ovaInstance.showAnnotation(anFound);
                                    }

                                    jQuery('html, body').animate({
                                        scrollTop: jQuery("#" + player.id_).offset().top},
                                        'slow');
                                };
                                if (player.paused()) {
                                    player.play();
                                    player.one('playing', playFunction);
                                } else {
                                    playFunction();
                                }

                                return false; // this will stop the code to not set a new player.one.
                            }
                        }
                    }
                }
            }
        }
    };

    $.DashboardController.prototype._onZoomToImageBoundsButtonClick = function(evt){
        var zoomToBounds = jQuery(evt.target).hasClass('zoomToImageBounds')?jQuery(evt.target):jQuery(evt.target).parents('.zoomToImageBounds:first');
        var osdaId = parseInt(zoomToBounds.find('.idAnnotation').html(), 10);
        var uri = zoomToBounds.find('.uri').html();

        var allannotations = this.annotator.plugins['Store'].annotations;
        var osda = this.annotator.osda;

        if (this.initOptions.externalLink) {
            uri += (uri.indexOf('?') >= 0) ?'&osdaId=' + osdaId : '?osdaId=' + osdaId;
            location.href = uri;
        }
        for(var item in allannotations) {
            var an = allannotations[item];
            // Makes sure that all images are set to transparent in case one was
            // previously selected.
            if (an.highlights) {
               an.highlights[0].style.background = "rgba(0, 0, 0, 0)";
            }
            if (typeof an.id !== 'undefined' && an.id === osdaId) { // this is the annotation
                var bounds = new OpenSeadragon.Rect(an.bounds.x, an.bounds.y, an.bounds.width, an.bounds.height);
                osda.viewer.viewport.fitBounds(bounds, false);

                jQuery('html, body').animate({scrollTop: jQuery("#"+an.target.container).offset().top},
                                        'slow');
                // signifies a selected annotation once OSD has zoomed in on the
                // appropriate area, it turns the background a bit yellow
                if (an.highlights !== undefined) {
                    an.highlights[0].style.background = "rgba(255, 255, 10, 0.2)";
                }
            }
        }
    };

    $.DashboardController.prototype._onPublicPrivateButtonClick = function(evt) {
        var action = jQuery(evt.target).find('span');
        var userId = '';
    
        // Get userI
        switch (action.html()){
            case 'public':
                userId = '';
                break;
            case 'instructor':
                userId = 'c8720cac6c7f59380abeb5f7758b6882065124a5';//this.initOptions.instructor_email;
                break;
            default:
                userId = this.annotator.plugins.Permissions.user.id;
                break;
        }
        this.current_tab = action.html();
        
        // checks to make sure that Grouping is redone when switching tags in text annotations
        if (this.initOptions.media === 'text') {
            if (typeof this.annotator.plugins.Grouping !== 'undefined') {
                // this is to check if user is is MyNotes instead of the annotation component
                this.annotator.plugins.Grouping.useGrouping = this.current_tab === 'public' ? 0 : 1;
            } 
            this.annotator.publish("changedTabsInCatch");
        }
        // Change userid and refresh
        this.changeUserId(userId);
    };

    $.DashboardController.prototype._onSelectionButtonClick = function(evt) {
        var but = jQuery(evt.target);
        var action = but.attr('media');
    
        // Get action
        if (action.length<=0) action="text"; // By default
        
        
        // Change media and refresh
        this.changeMedia(action);
    };

    $.DashboardController.prototype._onMoreButtonClick = function(evt) {
        this.clean = false;
        var moreBut = this.element.find('.annotationListButtons .moreButtonCatch');
        var isLoading = moreBut.html() === 'More'?false:true;
        if(!isLoading)
            this.loadAnnotations();
    };
            
    $.DashboardController.prototype._refresh = function(searchtype, searchInput) {
        var searchtype = searchtype || "";
        var searchInput = searchInput || ""; 
        this.clean = true;

        // the following cannot run in notes for there are no highlights
        if (jQuery("#notesHolder").length === 0) {
            this._clearAnnotator();
        }
        
        var annotator = this.annotator;
        var loadFromSearch = annotator.plugins.Store.options.loadFromSearch;
        
        loadFromSearch.limit = this.initOptions.pagination;
        loadFromSearch.offset = 0;
        loadFromSearch.media = this.initOptions.mediaType;
        loadFromSearch.userid = this.initOptions.user_id;
        
        loadFromSearch.username = "";
        loadFromSearch.tag = "";
        loadFromSearch.text = "";
        
        if (searchtype === "Users") {
            loadFromSearch.username = searchInput;
        } else if(searchtype === "Tags") {
            loadFromSearch.tag = searchInput;
        } else {
            loadFromSearch.text = searchInput;
        }
        annotator.plugins['Store'].loadAnnotationsFromSearch(loadFromSearch);
    };
    
    $.DashboardController.prototype._onSearchButtonClick = function(evt) {
        var searchtype = this.element.find('.searchbox .dropdown-list').val();
        var searchInput = this.element.find('.searchbox input').val();
        this._refresh(searchtype, searchInput);
        
    };

    $.DashboardController.prototype._onClearSearchButtonClick = function(evt) {
        this._refresh('', '');    
    };

    $.DashboardController.prototype._clearAnnotator = function() {
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

    $.DashboardController.prototype._onDeleteReplyButtonClick = function(evt) {
        var annotator = this.annotator;
        var item = jQuery(evt.target).parents('.replyItem:first');
        var id = item.attr('annotationid');
        var permissions = annotator.plugins.Permissions;
        var annotation = item.data('annotation');
        var authorized = permissions.options.userAuthorize('delete', annotation, permissions.user);
        if(authorized){
            if(confirm('Would you like to delete this reply?')){
                annotator.plugins['Store']._apiRequest('destroy', annotation, function(){});
                item.remove();
            }
        }
    };

    $.DashboardController.prototype.openLoadingGIF = function() {
        jQuery('#dashboard').append('<div class=\'annotations-loading-gif\'><img src="'+this.initOptions.imageRootUrl+'/loading_bar.gif" /><br />Annotations Data Loading... Please Wait.</div>');
    };

    $.DashboardController.prototype._onControlRepliesClick = function(evt) {
        var action = jQuery(evt.target)[0].className;
        
        if (action === 'newReply') {
            var item = jQuery(evt.target).parents('.annotationItem:first');
            var id = item.attr('annotationId');
            // Pre-show Adder
            this.annotator.adder.show();
            
            // Get elements
            var replyElem = jQuery(evt.target).parents('.annotationItem:first').find('.annotationDetail');
            var adder =this.annotator.adder;
            var wrapper = jQuery('.annotator-wrapper');

            // Calculate Editor position
            var positionLeft = this.findPosition(jQuery(evt.target).parent().find('.newReply')[0]);
            var positionAnnotator = this.findPosition(wrapper[0]);
            var positionAdder = {};

            // the following addition to display makes sure the editor shows up
            // after opening TinyMCE/editor within the image source
            positionAdder.display = "block";
            positionAdder.left = positionLeft.left - positionAnnotator.left;
            positionAdder.top = positionLeft.top + 20 - positionAnnotator.top;

            adder.css(positionAdder);

            // Open a new annotator dialog
            this.annotator.onAdderClick();
            
            // Set vertical editor
            jQuery(this.annotator.editor.element).css(positionAdder);
            this.annotator.editor.resetOrientation();
            this.annotator.editor.invertY();

            // set parent 
            var parentValue = jQuery(this.annotator.editor.element).find(".reply-item span.parent-annotation");
            parentValue.html(id);
            var self = this;
            
        } else if (action === 'hideReplies') {
            var oldAction = jQuery(evt.target).html();
            
            if (oldAction === 'Show Replies'){
                jQuery(evt.target).html('Hide Replies');
            } else {
                jQuery(evt.target).html('Show Replies');
                var replyElem = jQuery(evt.target).parents('.annotationItem:first').find('.replies');
                replyElem.html('');
                return false;
            }
           
            // search
            this._refreshReplies(evt);
        } else if (action === 'deleteAnnotation') {
            if (confirm("Would you like to delete the annotation?")) {
                var annotator = this.annotator;
                var item = jQuery(evt.target).parents('.annotationItem:first');
                var id = parseInt(item.attr('annotationId'), 10);
                var store = annotator.plugins.Store;
                var annotations = store.annotations;
                var permissions = annotator.plugins.Permissions;
                var annotation;
                annotations.forEach(function(ann) {
                   if (ann.id === id)
                       annotation = ann;
                });
                var authorized = permissions.options.userAuthorize('delete', annotation, permissions.user);
                if (authorized)
                    annotator.deleteAnnotation(annotation);
            }
        } else if (action === 'editAnnotation') {
           
            var annotator = this.annotator;
            var item = jQuery(evt.target).parents('.annotationItem:first');
            var id = parseInt(item.attr('annotationId'), 10);
            var store = annotator.plugins.Store;
            var annotations = store.annotations;
            var permissions = annotator.plugins.Permissions;
            var annotation;
            annotations.forEach(function(ann) {
               if (ann.id === id)
                   annotation = ann;
            });
            var authorized = permissions.options.userAuthorize('update', annotation, permissions.user);
            if (authorized){
                // Get elements
                var wrapper = jQuery('.annotator-wrapper');
                // Calculate Editor position
                var positionLeft = this.findPosition(jQuery(evt.target).parent().find('.editAnnotation')[0]);
                var positionAnnotator = this.findPosition(wrapper[0]);
                var positionAdder = {};

                positionAdder.left = positionLeft.left - positionAnnotator.left;
                positionAdder.top = positionLeft.top + 20 - positionAnnotator.top;
                var cleanup, offset, update;
                var _this = this.annotator;
                offset = positionAdder;
                update = function() {
                  cleanup();
                  return _this.updateAnnotation(annotation);
                };
                cleanup = function() {
                  _this.unsubscribe('annotationEditorHidden', cleanup);
                  return _this.unsubscribe('annotationEditorSubmit', update);
                };
                this.annotator.subscribe('annotationEditorHidden', cleanup);
                this.annotator.subscribe('annotationEditorSubmit', update);
                this.annotator.viewer.hide();
                this.annotator.showEditor(annotation, offset);                
            }
        }
    };

    $.DashboardController.prototype.findPosition = function(el) {
        var box, docEl, body, clientLeft, scrollLeft, left, clientTop, scrollTop, top;

        if (el.getBoundingClientRect && el.parentNode) {
          box = el.getBoundingClientRect();
        }

        if (!box) {
          return {
            left: 0,
            top: 0
          };
        }

        docEl = document.documentElement;
        body = document.body;

        clientLeft = docEl.clientLeft || body.clientLeft || 0;
        scrollLeft = window.pageXOffset || body.scrollLeft;
        left = box.left + scrollLeft - clientLeft;

        clientTop = docEl.clientTop || body.clientTop || 0;
        scrollTop = window.pageYOffset || body.scrollTop;
        top = box.top + scrollTop - clientTop;

        return {
          left: left,
          top: top
        };
    };

    $.DashboardController.prototype._refreshReplies = function(evt) {
        var item = jQuery(evt.target).parents('.annotationItem:first');
        var anId = parseInt(item.attr('annotationId'), 10);
            
        var replyElem = jQuery(evt.target).parents('.annotationItem:first').find('.replies');
        var annotator = this.annotator;
        var loadFromSearchURI = annotator.plugins.Store.options.loadFromSearch.uri;
        var self = this;
        var action='search';
        var loadFromSearch={
            limit:-1,
            parentid:anId,
            media:"comment",
            uri:loadFromSearchURI,        
        };
        var onSuccess = function(data) {
            if (data === null) data = {};
            annotations = data.rows || [];
            var _i, _len;
            for (_i = 0, _len = annotations.length; _i < _len; _i++) {
                
                self._formatCatch(annotations[_i]);
            }
            replyElem.html(self.TEMPLATES.annotationReply({ 
                annotations: annotations
            }));
            var replyItems = jQuery('.replies .replyItem');
            if (typeof replyItems !== 'undefined' && replyItems.length > 0) {
                annotations.forEach(function(ann) {
                    replyItems.each(function(item) {
                        var id = parseInt(jQuery(replyItems[item]).attr('annotationid'), 10);
                        if (id === ann.id) {
                            var perm = self.annotator.plugins.Permissions;
                            if (!perm.options.userAuthorize('delete', ann, perm.user)) {
                                jQuery(replyItems[item]).find('.deleteReply').remove();
                            } else {
                                jQuery(replyItems[item]).data('annotation', ann);
                            }
                        }
                    });
                });
            }
        };
        var id, options, request, url;
        var store = this.annotator.plugins.Store;
        id = loadFromSearch && loadFromSearch.id;
        url = store._urlFor(action, id);
        options = store._apiRequestOptions(action, loadFromSearch, onSuccess);
        request = jQuery.ajax(url, options);
        request._id = id;
        request._action = action;
    };

}(AController));