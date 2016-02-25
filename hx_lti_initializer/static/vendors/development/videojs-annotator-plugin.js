// ----------------Utilities---------------- //
var _ref;
var __bind = function(fn, me) { 
    return function() { 
        return fn.apply(me, arguments); 
    }; 
};
var __hasProp = {}.hasOwnProperty;
var __extends = function(child, parent) { 
    for (var key in parent) { 
        if (__hasProp.call(parent, key)) 
            child[key] = parent[key]; 
    } 
    function ctor() { 
        this.constructor = child; 
    } 

    ctor.prototype = parent.prototype; 
    child.prototype = new ctor(); 
    child.__super__ = parent.prototype; 
    return child; 
};
var createDateFromISO8601 = function(string) {
  var d, date, offset, regexp, time, _ref;
  regexp = "([0-9]{4})(-([0-9]{2})(-([0-9]{2})" + "(T([0-9]{2}):([0-9]{2})(:([0-9]{2})(\\.([0-9]+))?)?" + "(Z|(([-+])([0-9]{2}):([0-9]{2})))?)?)?)?";
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
var Util = typeof Util != 'undefined' ? Util : {};
Util.mousePosition = function(e, offsetEl) {
  var offset, _ref1;
  if ((_ref1 = $(offsetEl).css('position')) !== 'absolute' && _ref1 !== 'fixed' && _ref1 !== 'relative') {
    offsetEl = $(offsetEl).offsetParent()[0];
  }
  offset = $(offsetEl).offset();
  return {
    top: e.pageY - offset.top,
    left: e.pageX - offset.left
  };
};




// ----------------Load videojs-Annotation Plugin---------------- //
(function () {
    // -- Load Annotation plugin in videojs
    function vjsAnnotation_(options){
        var player = this;
    
        // variables to know if it is ready
    
        player.annotations = new vjsAnnotation(player, options);
    
        // When the DOM, Range Slider and the video media is loaded
        function initialVideoFinished(event) {
            // -- wait for plugins -- //
            var wrapper = $('.annotator-wrapper').parent()[0];
            var annotator = $.data(wrapper, 'annotator');
            
            // wait for Annotator and the Share plugin
            if (typeof Annotator.Plugin["Share"] === 'function') {
                if (typeof annotator.isShareLoaded != 'undefined' && annotator.isShareLoaded) {
                    annotator.unsubscribe('shareloaded', initialVideoFinished);
                } else {
                    annotator.subscribe('shareloaded', initialVideoFinished);
                    return false;
                }
            }
        
            var plugin = player.annotations;
        
            // All components will be initialize after they have been loaded by videojs
            for (var index in plugin.components) {
                plugin.components[index].init_();
            }

            player.annotations.AnConBut.show();
            //player.annotations.BigNewAn.show();
        
            // set the position of the big buttom
            plugin.setposBigNew(plugin.options.posBigNew);
        
            if(!options.showDisplay) 
                plugin.hideDisplay();
            if(!options.showStatistics) 
                plugin.hideStatistics();
        
        
            // Get current instance of annotator 
            player.annotator = annotator;
            plugin.annotator = annotator;
        
            // get annotations
            var allannotations = annotator.plugins['Store'].annotations;
            plugin.refreshDisplay();
        
            // -- Listener to Range Slider Plugin
            player.rangeslider.rstb.on('mousedown', function(){plugin._onMouseDownRS(event)});
            // Open the autoPlay from the API
            if (player.autoPlayAPI) {
                var OnePlay = function () {
                    player.annotations.showAnnotation(player.autoPlayAPI);
                    $('html, body').animate({
                        scrollTop: $("#" + player.id_).offset().top},
                        'slow');
                };
                if (player.techName == 'Youtube')
                    setTimeout(OnePlay, 100); // fix the delay playing youtube
                else
                    OnePlay();
            }
        
            // set the number of Annotations to display
            plugin.refreshDesignPanel();
        
            // check full-screen change
            player.on('fullscreenchange', function() {
                if (player.isFullScreen) {
                    $(player.annotator.wrapper[0]).addClass('vjs-fullscreen');
                } else {
                    $(player.annotator.wrapper[0]).removeClass('vjs-fullscreen');
                }
                plugin.refreshDesignPanel();
            });
        
            // loaded plugin
            plugin.loaded = true;
        }
        player.one('loadedRangeSlider', initialVideoFinished); // Loaded RangeSlider
    
        //console.log("Loaded Annotation Plugin");
    }
    videojs.plugin('annotations', vjsAnnotation_);


    // -- Plugin
    function vjsAnnotation(player, options) {
        var player = player || this;
    
        this.player = player;
        
        this.components = {}; // holds any custom components we add to the player

        options = options || {}; // plugin options
        
        if(!options.hasOwnProperty('posBigNew')) 
            options.posBigNew = 'none'; // ul = up left || ur = up right || bl = below left || br = below right || c = center
        if(!options.hasOwnProperty('showDisplay')) 
            options.showDisplay = false; 
        if(!options.hasOwnProperty('showStatistics')) 
            options.showStatistics = false; 
        
        this.options = options;
    
        this.init();
    }

    // -- Methods
    vjsAnnotation.prototype = {
        /* Constructor */
        init: function() {
            var player = this.player || {};
            var controlBar = player.controlBar;
            var seekBar = player.controlBar.progressControl.seekBar;
                
            this.updatePrecision = 3;
            
            // Components and Quick Aliases
            //this.BigNewAn = this.components.BigNewAnnotation = player.BigNewAnnotation;
            this.AnConBut = this.components.AnContainerButtons = player.AnContainerButtons;
            this.ShowSt = this.components.ShowStatistics = this.AnConBut.ShowStatistics;
            this.NewAn = this.components.NewAnnotation = this.AnConBut.NewAnnotation;
            this.ShowAn =this.components.ShowAnnotations = this.AnConBut.ShowAnnotations;
            this.BackAnDisplay = this.components.BackAnDisplay = controlBar.BackAnDisplay; // Background of the panel
            this.AnDisplay = this.components.AnDisplay = controlBar.BackAnDisplay.AnDisplay; // Panel with all the annotations
            this.AnStat = this.components.AnStat = controlBar.BackAnDisplay.AnStat; // Panel with statistics of the number of annotations
            this.BackAnDisplayScroll = this.components.BackAnDisplayScroll = controlBar.BackAnDisplayScroll; // Back Panel with all the annotations
            this.backDSBar = this.components.BackAnDisplayScrollBar = this.BackAnDisplayScroll.BackAnDisplayScrollBar; // Scroll Bar
            this.backDSBarSel = this.components.ScrollBarSelector = this.backDSBar.ScrollBarSelector; // Scroll Bar Selector
            this.backDSTime = this.components.BackAnDisplayScrollTime = this.BackAnDisplayScroll.BackAnDisplayScrollTime; // Back Panel with time of the annotations in the scroll
            this.rsd = this.components.RangeSelectorDisplay = controlBar.BackAnDisplay.RangeSelectorDisplay; // Selection the time to display the annotations
            this.rsdl = this.components.RangeSelectorLeft = this.rsd.RangeSelectorLeft;
            this.rsdr = this.components.RangeSelectorRight = this.rsd.RangeSelectorRight;
            this.rsdb = this.components.RangeSelectorBar = this.rsd.RangeSelectorBar;
            this.rsdbl = this.components.RangeSelectorBarL = this.rsdb.RangeSelectorBarL;
            this.rsdbr = this.components.RangeSelectorBarR = this.rsdb.RangeSelectorBarR;
            this.rs = player.rangeslider;
            
            // local variables
            this.editing = false;
            
            var wrapper = $('.annotator-wrapper').parent()[0];
            var annotator = $.data(wrapper, 'annotator');
            var self = this;
            // Subscribe to Annotator changes
            annotator.subscribe("annotationsLoaded", function (annotations) {
                if(self.loaded)
                    self.refreshDisplay();
            });
            annotator.subscribe("annotationUpdated", function (annotation) {
               if(self.loaded)
                    self.refreshDisplay();
            });
            annotator.subscribe("annotationDeleted", function (annotation) {
                var annotations = annotator.plugins['Store'].annotations;
                var tot = typeof annotations !== 'undefined' ? annotations.length : 0;
                var attempts = 0; // max 100
                // This is to watch the annotations object, to see when is deleted the annotation
                var ischanged = function() {
                    var new_tot = annotator.plugins['Store'].annotations.length;
                    if (attempts < 100)
                        setTimeout(function(){
                            if (new_tot !== tot) {
                                if(self.loaded)
                                    self.refreshDisplay();
                            } else {
                                attempts++;
                                ischanged();
                            }
                        }, 100); // wait for the change in the annotations
                };
                ischanged();
            });
            this.AnConBut.hide();
           // this.BigNewAn.hide(); // Hide until the video is load
        },
        newan: function(start, end) {
            var player = this.player;
            var annotator = this.annotator;
            var sumPercent = 10; // percentage for the last mark
            var currentTime = player.currentTime();
            var lastTime = this._sumPercent(currentTime, sumPercent); 
            
            var start = typeof start !== 'undefined' ? start : currentTime;
            var end = typeof end !== 'undefined' ? end : lastTime;
                
            this._reset();
            
            // set position RS and pause the player
            player.showSlider();
            player.pause();
            
            player.setValueSlider(start, end);
            
            // This variable is to say the editor that we want create a VideoJS annotation
            annotator.editor.VideoJS = this.player.id_;
            
            annotator.adder.show();
            
            this._setOverRS(annotator.adder);

            // Open a new annotator dialog
            annotator.onAdderClick();
        },
        showDisplay: function() {
            this._reset();
            // show
            this.BackAnDisplay.removeClass('disable'); // show the Container
            this.BackAnDisplayScroll.removeClass('disable'); // show the scroll
            // active button
            this.ShowAn.addClass('active');
            this.options.showDisplay =true;
            console.log(this);
            jQuery(this.player).trigger('annotationsDisplayed');
        },
        hideDisplay: function() {
            // hide
            this.BackAnDisplay.addClass('disable'); // hide the Container
            this.BackAnDisplayScroll.addClass('disable'); // hide the scroll
            // no active button
            videojs.removeClass(this.ShowAn.el_, 'active');
            this.options.showDisplay =false;
        },
        showStatistics: function() {
            this._reset();
            // show
            this.BackAnDisplay.removeClass('disable'); // show the Container
            this.AnStat.removeClass('disable'); // show Statistics
            // mode (this mode will hide the annotations to show the statistics in the container)
            this.BackAnDisplay.addClass('statistics'); // mode statistics 
            // paint
            this.AnStat.paintCanvas(); // refresh canvas
            // active button
            this.ShowSt.addClass('active');
            this.options.showStatistics =true;
        },
        hideStatistics: function() {
            // hide
            this.BackAnDisplay.addClass('disable'); // hide the Container
            this.AnStat.addClass('disable'); // hide Statistics
            // remove mode statistics
            this.BackAnDisplay.removeClass('statistics');
            // no active button
            this.ShowSt.removeClass('active');
            this.options.showStatistics = false;
        },
        showAnnotation: function(annotation) {
            var isVideo = this._isVideoJS(annotation);
            if (isVideo) {
                var start = annotation.rangeTime.start;
                var end = annotation.rangeTime.end;
                var duration = this.player.duration();
                var isPoint = videojs.round(start, 3) == videojs.round(end, 3);
                
                this._reset();
            
                // show the range slider
                this.rs.show();
            
                // set the slider position
                this.rs.setValues(start, end);
            
                // lock the player        
                this.rs.lock();
                console.log(start);
                console.log(end);
                // play
                if (!isPoint)
                    this.rs.playBetween(start, end);
                    
                // fix small bar
                var width = Math.min(1, Math.max(0.005, (this.rs._percent(end - start)))) * 100;
                this.rs.bar.el_.style.width = width + '%';
                    
                // Add the annotation object to the bar 
                var bar = isPoint ? this.rs[((duration - start) / duration < 0.1) ? 'left' : 'right'].el_ : this.rs.bar.el_;
                var holder = $(this.rs.left.el_).parent()[0];
                $(holder).append('<span class="annotator-hl"></div>');
                $(bar).appendTo( $(holder).find('.annotator-hl'));
            
                var span = $(bar).parent()[0];
                $.data(span, 'annotation', annotation); // Set the object in the span
            
                // set the editor over the range slider
                this._setOverRS(this.annotator.editor.element);
                this.annotator.editor.checkOrientation();
            
                // hide the panel
                this.rs.hidePanel();
            }
        },
        hideAnnotation: function() {
            this.rs.hide();
            this.rs.showPanel();
            
            // remove the last single showed annotation
            var holder = $(this.rs.left.el_).parent()[0];
            var holderRight = $(this.rs.right.el_).parent()[0];
            if ($(holder).find('.annotator-hl').length > 0) {
                $($(holder).find('.annotator-hl')[0].children[0]).appendTo(holder);
                $(holder).find('.annotator-hl').remove();
            } else if ($(holderRight).find('.annotator-hl').length > 0) {
                $($(holderRight).find('.annotator-hl')[0].children[0]).appendTo(holderRight);
                $(holderRight).find('.annotator-hl').remove();
            }
        },
        editAnnotation: function(annotation, editor) {
            // This will be usefull when we are going to edit an annotation.
            if (this._isVideoJS(annotation)) {
                this.hideDisplay();
                var player = this.player;
                var editor = editor || this.annotator.editor;
                
                // show the slider and set in the position
                player.showSlider();
                player.unlockSlider();
                player.setValueSlider(annotation.rangeTime.start, annotation.rangeTime.end);
                
                // show the time panel
                player.showSliderPanel();
                
                // set the editor over the range slider
                this._setOverRS(editor.element);
                editor.checkOrientation();
                
                // set the VideoJS variable
                editor.VideoJS = player.id_;
            }
        },
        refreshDisplay: function() {
            var count = 0;
            var allannotations = this.annotator.plugins['Store'].annotations;
            
            // Sort by date the Array
            this._sortByDate(allannotations);
            
            // reset the panel
            $(this.AnDisplay.el_).find('span').remove(); // remove the last html items
            $(this.player.el_).find('.vjs-anpanel-annotation .annotation').remove(); // remove a deleted annotation without span wrapper
            
            for (var item in allannotations) {
                var an = allannotations[item];
                
                // check if the annotation is a video annotation
                if (this._isVideoJS(an)){
                    var div = document.createElement('div');
                    var span = document.createElement('span');
                    var start = this.rs._percent(an.rangeTime.start) * 100;
                    var end = this.rs._percent(an.rangeTime.end) * 100;
                    var width;
                    span.appendChild(div);
                    span.className = "annotator-hl";
                    width = Math.min(100, Math.max(0.2, end - start));
                    div.className = "annotation";
                    div.id = count;
                    div.style.top = count + "em";
                    div.style.left = start + '%';
                    div.style.width = width + '%';
                    div.start = an.rangeTime.start;
                    div.end = an.rangeTime.end;
                    this.AnDisplay.el_.appendChild(span);
                    
                    // detect point annotations
                    if (videojs.round(start, 0) == videojs.round(end, 0)) {
                        $(div).css('width', '');
                        $(div).addClass("point");
                    }
                    
                    // Set the object in the div
                    $.data(span, 'annotation', an);
                    // Add the highlights to the annotation
                    an.highlights = $(span);
                    
                    count++;
                }
            };
            var start = this.rs._seconds(parseFloat(this.rsdl.el_.style.left) / 100);
            var end = this.rs._seconds(parseFloat(this.rsdr.el_.style.left) / 100);
                
            this.showBetween(start, end, this.rsdl.include, this.rsdr.include);
        },
        showBetween: function (start, end, includeLeft, includeRight) {
            var duration = this.player.duration();
            var start = start || 0;
            var end = end || duration;
            var annotationsHTML = $.makeArray($(this.player.el_).find('.vjs-anpanel-annotation .annotator-hl'));
            var count = 0;
            var wrapper = $('.annotator-wrapper').parent()[0];
            var annotator = $.data(wrapper, 'annotator');
            for (var index in annotationsHTML) {
                var an = $.data(annotationsHTML[index], 'annotation');
                var expressionLeft = includeLeft ? (an.rangeTime.end >= start) : (an.rangeTime.start >= start);
                var expressionRight = includeRight ? (an.rangeTime.start <= end) : (an.rangeTime.end <= end);
                if (this._isVideoJS(an) && expressionLeft && expressionRight && typeof an.highlights[0] !== 'undefined') {
                    var annotationHTML = an.highlights[0].children[0];
                    annotationHTML.style.marginTop = (-1 * parseFloat(annotationHTML.style.top) + count) + 'em';
                    $(an.highlights[0]).show();
                    annotator.publish('annotationShown', an.id);
                    count++;
                } else if (this._isVideoJS(an) && typeof an.highlights[0] !== 'undefined') {
                    $(an.highlights[0]).hide();
                    an.highlights[0].children[0].style.marginTop = '';
                    annotator.publish('annotationHidden', an.id);
                }
            }
            // Set the times in the scroll time panel
            this.backDSTime.setTimes();
        },
        setposBigNew: function(pos) {
            /*var pos = pos || 'ul';
            var el = this.player.BigNewAnnotation.el_;
            videojs.removeClass(el, 'ul');
            videojs.removeClass(el, 'ur');
            videojs.removeClass(el, 'c');
            videojs.removeClass(el, 'bl');
            videojs.removeClass(el, 'br');
            videojs.addClass(el, pos);*/
        },
        pressedKey: function (key) {
            var player = this.player;
            var rs = this.player.rs;
            if (typeof key !== 'undefined' && key == 73) { // -- i key
                this._reset();
                
                // show slider
                this.rs.show();
                // hide other elements
                this.rs._reset();
                this.rs.setValue(0, player.currentTime());
                this.rs.right.el_.style.visibility = 'hidden';
                this.rs.tpr.el_.style.visibility = 'hidden';
                this.rs.ctpr.el_.style.visibility = 'hidden';
                this.rs.bar.el_.style.visibility = 'hidden';
                this.lastStartbyKey = player.currentTime();
            } else if (typeof key!='undefined' && key==79) { // -- o key
                if (this.rs.bar.el_.style.visibility == 'hidden') { // the last action was to type the i key
                    var start = this.lastStartbyKey != 'undefined' ? this.lastStartbyKey:0;
                    this.newan(start, player.currentTime());
                } else {
                    this.newan(player.currentTime(), player.currentTime());
                }
            }
        },
        refreshDesignPanel: function() {
            var player = this.player;
            var emtoPx = parseFloat($(this.backDSBar.el_).css('width'));
            var playerHeight = parseFloat($(player.el_).css('height'));
            var controlBarHeight = parseFloat($(player.controlBar.el_).css('height'));
            var newHeight = (playerHeight - controlBarHeight - 80) / emtoPx - 5;
            this.BackAnDisplay.el_.style.height = this.backDSBar.el_.style.height = (newHeight + 'em');
            this.BackAnDisplay.el_.style.top = this.backDSBar.el_.style.top = "-" + (newHeight + 3 + 'em');
            this.BackAnDisplayScroll.el_.children[0].style.top = "-" + (newHeight + 5 + 'em');
            this.backDSTime.el_.children[0].style.top = "-" + (newHeight + 5 + 'em');
        },
        _reset: function() {
            // Hide all the components
            this.hideDisplay();
            this.hideAnnotation();
            this.hideStatistics();
            this.player.annotator.adder.hide(); 
            this.player.annotator.editor.hide();
            this.player.annotator.viewer.hide();
            
            // make visible all the range slider element that maybe were hidden in pressedKey event
            this.rs.right.el_.style.visibility = '';
            this.rs.tpr.el_.style.visibility = '';
            this.rs.ctpr.el_.style.visibility = '';
            this.rs.bar.el_.style.visibility = '';
            
            // by default the range slider must be unlocked
            this.rs.unlock();
            
            // whether there is a playing selection
            this.rs.bar.suspendPlay(); 
            
            // refresh the design
            this.refreshDesignPanel();
        },
        _setOverRS: function(elem) {
            var annotator = this.player.annotator;
            var wrapper = $('.annotator-wrapper')[0];
            var positionLeft = videojs.findPosition(this.rs.left.el_);
            var positionRight = videojs.findPosition(this.rs.right.el_);
            var positionAnnotator = videojs.findPosition(wrapper);
            var positionAdder = {};
                
            elem[0].style.display = 'block'; // Show the adder
            
            if (this.player.isFullScreen) {
                positionAdder.top = positionLeft.top;
                positionAdder.left = positionLeft.left + (positionRight.left - positionLeft.left) / 2;
            } else {
                positionAdder.left = positionLeft.left + (positionRight.left - positionLeft.left) / 2 - positionAnnotator.left;
                positionAdder.top = positionLeft.top - positionAnnotator.top;
            }
            
            elem.css(positionAdder);
        },
        _onMouseDownRS: function(event) {
            event.preventDefault();
        
            if (!this.rs.options.locked) {
                videojs.on(document, "mousemove", videojs.bind(this, this._onMouseMoveRS));
                videojs.on(document, "mouseup", videojs.bind(this, this._onMouseUpRS));
            }
        },
        _onMouseMoveRS: function(event) {
            var player = this.player;
            var annotator = player.annotator;
            var rs = player.rangeslider;
            annotator.editor.element[0].style.display = 'none';
            rs.show();
            this._setOverRS(annotator.adder);
        },
        _onMouseUpRS: function(event) {
            videojs.off(document, "mousemove", this._onMouseMoveRS, false);
            videojs.off(document, "mouseup", this._onMouseUpRS, false);
            
            var player = this.player;
            var annotator = player.annotator;
            var rs = player.rangeslider;
            annotator.editor.element[0].style.display = 'block';
            
            this._setOverRS(annotator.editor.element);
        },
        _sumPercent: function(seconds, percent) {
            // the percentage is in %
            var duration = this.player.duration();
            var seconds = seconds || 0;
            var percent = percent || 10;
            percent = Math.min(100, Math.max(0, percent));
            
            if (isNaN(duration)) {
                return 0;
            }
            return Math.min(duration, Math.max(0, seconds + duration * percent / 100));
        },
        // Detect if we are creating or editing a video-js annotation
        _EditVideoAn: function () {
            var annotator = this.annotator;
            var isOpenVideojs = (typeof this.player != 'undefined');
            var VideoJS = annotator.editor.VideoJS;
            return (isOpenVideojs && typeof VideoJS!='undefined' && VideoJS!==-1);
        },
        // Detect if the annotation is a video-js annotation
        _isVideoJS: function (an) {
            var player = this.player;
            var rt = an.rangeTime;
            var isOpenVideojs = (typeof this.player !== 'undefined');
            var isVideo = (typeof an.media !== 'undefined' && (an.media === 'video' || an.media === 'audio'));
            var isContainer = (typeof an.target !== 'undefined' && an.target.container == player.id_ );
            var isNumber = (typeof rt !== 'undefined' && !isNaN(parseFloat(rt.start)) && isFinite(rt.start) && !isNaN(parseFloat(rt.end)) && isFinite(rt.end));
            var isSource = false;
            if (isContainer) {
                // Compare without extension
                var isYoutube = (isOpenVideojs && typeof this.player.techName !== 'undefined') ? (this.player.techName === 'Youtube') : false;
                var targetSrc = isYoutube ? an.target.src : an.target.src.substring(0, an.target.src.lastIndexOf("."));
                var playerSrc = isYoutube ? player.options_.sources[0].src : player.options_.sources[0].src.substring(0, player.options_.sources[0].src.lastIndexOf("."));
                isSource = (targetSrc === playerSrc);
            }
            return (isOpenVideojs && isVideo && isContainer && isSource && isNumber);
        },
        _sortByDate: function (annotations, type) {
            var type = type || 'asc'; // asc => The value [0] will be the most recent date
            annotations.sort(function(a, b) {
                a = new Date(typeof a.updated !== 'undefined' ? createDateFromISO8601(a.updated) : '');
                b = new Date(typeof b.updated !== 'undefined' ? createDateFromISO8601(b.updated) : '');
                if (type == 'asc')
                    return (b < a) ? -1 : ((b > a) ? 1 : 0);
                else
                    return (a < b) ? -1 : ((a > b) ? 1 : 0);
            });
        }
    };

    // ----------------CREATE new Components for video-js---------------- //

    // --Charge the new Component into videojs
    videojs.Player.prototype.options_.children.AnContainerButtons = {}; // Container with the css for the buttons
    videojs.ControlBar.prototype.options_.children.BackAnDisplay = {}; // Range Slider Time Bar
    videojs.ControlBar.prototype.options_.children.BackAnDisplayScroll = {}; // Range Slider Time Bar
   // videojs.options.children.BigNewAnnotation = {}; // Big Button New Annotation



    // -- Player--> BigNewAnnotation

    /**
     * Create a New Annotation with big Button
     * @param {videojs.Player|Object} player
     * @param {Object=} options
     * @constructor
     */
    // videojs.BigNewAnnotation = videojs.Button.extend({
    //     /** @constructor */
    //     init: function(player, options) {
    //         videojs.Button.call(this, player, options);
    //     }
    // });

    // videojs.BigNewAnnotation.prototype.init_ = function() {
    //     this.an = this.player_.annotations;
    //     // Hide Button if the user has selected readOnly in the Annotator options
    //     var opts = this.an.options.optionsAnnotator;
    //     if (typeof opts !== 'undefined' && typeof opts.readOnly !== 'undefined' && opts.readOnly)
    //         this.hide();
    // };

    // videojs.BigNewAnnotation.prototype.createEl = function() {
    //     return videojs.Button.prototype.createEl.call(this, 'div', {
    //         className: 'vjs-big-new-annotation vjs-menu-button vjs-control',
    //         innerHTML: '<div class="vjs-big-menu-button vjs-control">A</div>',
    //         title: 'New Annotation',
    //     });
    // };

    // videojs.BigNewAnnotation.prototype.onClick = function() {
    //     this.an.newan();
    // };

    // -- Player--> ControlBar--> AnContainerButtons

    /**
     * Container for the button CSS
     * @param {videojs.Player|Object} player
     * @param {Object=} options
     * @constructor
     */

    videojs.AnContainerButtons = videojs.Component.extend({
        /** @constructor */
        init: function(player, options) {
            videojs.Component.call(this, player, options);
        }
    });

    videojs.AnContainerButtons.prototype.init_ = function() {};


    videojs.AnContainerButtons.prototype.options_ = {
        children: {
            'ShowAnnotations': {},
            'NewAnnotation': {},
            'ShowStatistics': {},
        }
    };

    videojs.AnContainerButtons.prototype.createEl = function() {
        return videojs.Component.prototype.createEl.call(this, 'div', {
            className: 'vjs-container-button-annotation',
        });
    };

    // -- Player--> ControlBar--> AnContainerButtons--> ShowStatistics

    /**
     * Button for show/hide the chart with statistics of the annotation's number
     * @param {videojs.Player|Object} player
     * @param {Object=} options
     * @constructor
     */

    videojs.ShowStatistics = videojs.Button.extend({
        /** @constructor */
        init: function(player, options) {
            videojs.Button.call(this, player, options);
        }
    });

    videojs.ShowStatistics.prototype.init_ = function() {
        this.an = this.player_.annotations;
    };

    videojs.ShowStatistics.prototype.createEl = function() {
        return videojs.Button.prototype.createEl.call(this, 'div', {
            className: 'vjs-statistics-annotation vjs-control',
            title: 'Show the Statistics',
        });
    };

    videojs.ShowStatistics.prototype.onClick = function() {
        if (!this.an.options.showStatistics) this.an.showStatistics();
        else this.an.hideStatistics();
    };



    // -- Player--> ControlBar--> AnContainerButtons--> ShowAnnotations

    /**
     * Button for show/hide the annotation panel
     * @param {videojs.Player|Object} player
     * @param {Object=} options
     * @constructor
     */

    videojs.ShowAnnotations = videojs.Button.extend({
      /** @constructor */
      init: function(player, options) {
        videojs.Button.call(this, player, options);
      }
    });

    videojs.ShowAnnotations.prototype.init_ = function() {
        this.an = this.player_.annotations;
    };

    videojs.ShowAnnotations.prototype.createEl = function() {
        return videojs.Button.prototype.createEl.call(this, 'div', {
            className: 'vjs-showannotations-annotation vjs-control',
            title: 'Show Annotations',
        });
    };

    videojs.ShowAnnotations.prototype.onClick = function() {
        if (!this.an.options.showDisplay) this.an.showDisplay();
        else this.an.hideDisplay();
    };



    // -- Player--> ControlBar--> AnContainerButtons--> NewAnnotation

    /**
     * Create a New Annotation
     * @param {videojs.Player|Object} player
     * @param {Object=} options
     * @constructor
     */
    videojs.NewAnnotation = videojs.Button.extend({
        /** @constructor */
        init: function(player, options) {
            videojs.Button.call(this, player, options);
        }
    });

    videojs.NewAnnotation.prototype.init_ = function() {
        this.an = this.player_.annotations;
        // Hide Button if the user has selected readOnly in the Annotator options
        var opts = this.an.options.optionsAnnotator;
        if (typeof opts !== 'undefined' && typeof opts.readOnly !== 'undefined' && opts.readOnly)
            this.hide();
    };

    videojs.NewAnnotation.prototype.createEl = function() {
        return videojs.Button.prototype.createEl.call(this, 'div', {
            className: 'vjs-new-annotation vjs-control',
            title: 'New Annotation',
        });
    };

    videojs.NewAnnotation.prototype.onClick = function() {
        this.an.newan();
    };



    // -- Player--> ControlBar--> BackAnDisplay

    /**
     * The background annotations panel
     * @param {videojs.Player|Object} player
     * @param {Object=} options
     * @constructor
     */
    videojs.BackAnDisplay = videojs.Component.extend({
        /** @constructor */
        init: function(player, options) {
            videojs.Component.call(this, player, options);
        }
    });

    videojs.BackAnDisplay.prototype.init_ = function() {
        this.an = this.player_.annotations
            self = this;
        // Fix error resizing the display panel. The scroll always went up.
        $(this.el_).watch('font-size', function() {
            self.an.backDSBarSel.setPosition(self.an.BackAnDisplayScroll.currentValue, false);
        });

    };

    videojs.BackAnDisplay.prototype.options_ = {
        children: {
            'RangeSelectorDisplay': {},
            'AnDisplay': {},
            'AnStat': {},
        }
    };

    videojs.BackAnDisplay.prototype.createEl = function() {
        return videojs.Component.prototype.createEl.call(this, 'div', {
            className: 'vjs-back-anpanel-annotation',
        });
    };



    // -- Player--> ControlBar--> BackAnDisplay--> RangeSelectorDisplay

    /**
     * The selector to show the annotations in a time selection
     * @param {videojs.Player|Object} player
     * @param {Object=} options
     * @constructor
     */
     
    videojs.RangeSelectorDisplay = videojs.Component.extend({
        /** @constructor */
        init: function(player, options) {
        videojs.Component.call(this, player, options);
            this.on('mousedown', this.onMouseDown);
        }
    });

    videojs.RangeSelectorDisplay.prototype.init_ = function() {
        this.rs = this.player_.rangeslider;
        this.an = this.player_.annotations;
        var duration = this.an.player.duration();
        this.start = 0;
        this.end = duration;
        
        // set the selection area in the extreme position
        this.setPosition(0, 0, false);
        this.setPosition(1, this.rs._percent(duration), false);
    };

    videojs.RangeSelectorDisplay.prototype.options_ = {
        children: {
            'RangeSelectorLeft': {},
            'RangeSelectorRight': {},
            'RangeSelectorBar': {},
        }
    };

    videojs.RangeSelectorDisplay.prototype.createEl = function(){
        return videojs.Component.prototype.createEl.call(this, 'div', {
            className: 'vjs-rangeselector-anpanel-annotation',
        });
    };

    videojs.RangeSelectorDisplay.prototype.onMouseDown = function(event) {
        event.preventDefault();
        // videojs.blockTextSelection();
        
        videojs.on(document, "mousemove", videojs.bind(this, this.onMouseMove));
        videojs.on(document, "mouseup", videojs.bind(this, this.onMouseUp));
        
        videojs.removeClass(this.an.rsdb.el_, 'disable');
    };

    videojs.RangeSelectorDisplay.prototype.onMouseUp = function(event) {
        videojs.off(document, "mousemove", this.onMouseMove, false);
        videojs.off(document, "mouseup", this.onMouseUp, false);
        
        videojs.addClass(this.an.rsdb.el_, 'disable');
    };

    videojs.RangeSelectorDisplay.prototype.onMouseMove = function(event) {
        var left = this.calculateDistance(event);
        if (this.an.rsdl.pressed)
            this.setPosition(0, left);
        else if (this.an.rsdr.pressed)
            this.setPosition(1, left);
        
        // move the frame to the position of the arrow
        this.an.player.currentTime(this.rs._seconds(left));
    };

    videojs.RangeSelectorDisplay.prototype.calculateDistance = function(event) {
        var rstbX = this.getRSTBX();
        var rstbW = this.getRSTBWidth();
        var handleW = this.getWidth();

        // Adjusted X and Width, so handle doesn't go outside the bar
        rstbX = rstbX + (handleW / 2);
        rstbW = rstbW - handleW;

        // Percent that the click is through the adjusted area
        return Math.max(0, Math.min(1, (event.pageX - rstbX) / rstbW));
    };

    videojs.RangeSelectorDisplay.prototype.getRSTBWidth = function() {
        return this.el_.offsetWidth;
    };
    videojs.RangeSelectorDisplay.prototype.getRSTBX = function() {
        return videojs.findPosition(this.el_).left;
    };
    videojs.RangeSelectorDisplay.prototype.getWidth = function() {
        var arrow = $(this.an.rsdl.el_).find('.vjs-selector-arrow')[0];
        return arrow.offsetWidth; // does not matter left or right
    };

    videojs.RangeSelectorDisplay.prototype.setPosition = function(index, left, changeTime) {
        // index = 0 for left side, index = 1 for right side
        var index = index || 0;
        var changeTime = typeof changeTime !== 'undefined' ? changeTime : true;

        // Check for invalid position
        if(isNaN(left)) 
            return false;
        
        // Check index between 0 and 1
        if (!(index === 0 || index === 1))
            return false;
        // Alias
        var ObjLeft = this.an.rsdl.el_;
        var ObjRight = this.an.rsdr.el_;
        var Obj = this.an[index === 0 ? 'rsdl' : 'rsdr'].el_;
        
        // Check if left arrow is over the right arrow
        if ((index === 0 ? this.updateLeft(left) : this.updateRight(left))) {
            if (index === 1) { // right
                Obj.style.left = (left * 100) + '%';
                Obj.style.width = ((1 - left) * 100) + '%';
            } else { // left
                Obj.style.left = (left * 100) + '%';
                Obj.style.width = ((left) * 100) + '%';
            }
            
            this[index === 0 ? 'start' : 'end'] = this.rs._seconds(left);
        
            // Fix the problem  when you press the button and the two arrow are underhand
            // left.zIndex = 10 and right.zIndex=20. This is always less in this case:
            if (index === 0 && (left * 100) >= 90)
                $(ObjLeft).find('.vjs-selector-arrow')[0].style.zIndex = 25;
            else
                $(ObjLeft).find('.vjs-selector-arrow')[0].style.zIndex = 10;
            
            
            // -- Panel
            var rsdbl = this.an.rsdbl.el_,
                rsdbr = this.an.rsdbr.el_,
                distance = parseFloat(ObjRight.style.left) - parseFloat(ObjLeft.style.left);
            if (index === 0)
                rsdbl.children[0].innerHTML = videojs.formatTime(this.rs._seconds(left));
            else
                rsdbr.children[0].innerHTML = videojs.formatTime(this.rs._seconds(left));
            if (typeof distance !== 'undefined' && distance <= 12.5) {
                if (parseFloat(ObjLeft.style.left) < 7) {
                    rsdbl.style.top = (-1.5) + 'em';
                    rsdbl.style.left = 1 + 'em';
                } else {
                    rsdbl.style.left = (-2.5) + 'em';
                    rsdbl.style.top = '';
                }
                    
                if (parseFloat(ObjRight.style.left) > 93) {
                    rsdbr.style.top = (-1.5) + 'em';
                    rsdbr.style.right = 1 + 'em';
                } else {
                    rsdbr.style.right = (-2.5) + 'em';
                    rsdbr.style.top = '';
                }
            } else {
                rsdbl.style.left = 1 + 'em';
                rsdbr.style.right = 1 + 'em';
                rsdbl.style.top = '';
                rsdbr.style.top = '';
            }
            
            
            var start = this.rs._seconds(parseFloat(ObjLeft.style.left) / 100);
            var end = this.rs._seconds(parseFloat(ObjRight.style.left) / 100);
                
            if (changeTime)
                this.an.showBetween(start, end, this.an.rsdl.include, this.an.rsdr.include);
        }
        return true;
    };

    videojs.RangeSelectorDisplay.prototype.updateLeft = function(left) {
        var rightVal = this.an.rsdr.el_.style.left !== '' ? this.an.rsdr.el_.style.left : 100;
        var right = parseFloat(rightVal) / 100;
        var bar = this.an.rsdb.el_;
        
        var width = videojs.round((right - left), this.an.updatePrecision); // round necessary for not get 0.6e-7 for example that it's not able for the html css width
        if(left <= (right+0.00001)) {
                bar.style.left = (left * 100) + '%';
                bar.style.width = (width * 100) + '%';
                return true;
        }
        return false;
    };
            
    videojs.RangeSelectorDisplay.prototype.updateRight = function(right) {
        var leftVal = this.an.rsdl.el_.style.left !== '' ? this.an.rsdl.el_.style.left : 0;
        var left = parseFloat(leftVal) / 100;
        var bar = this.an.rsdb.el_;
            
        var width = videojs.round((right - left), this.an.updatePrecision); // round necessary for not get 0.6e-7 for example that it's not able for the html css width
        
        if((right+0.00001) >= left) {
            bar.style.width = (width * 100) + '%';
            bar.style.left = ((right  - width) * 100) + '%';
            return true;
        }
        return false;
    };        



    // -- Player--> ControlBar--> BackAnDisplay--> RangeSelectorDisplay--> RangeSelectorLeft

    /**
     * Left Time selector
     * @param {videojs.Player|Object} player
     * @param {Object=} options
     * @constructor
     */
    videojs.RangeSelectorLeft = videojs.Component.extend({
        /** @constructor */
        init: function(player, options) {
            videojs.Component.call(this, player, options);
            this.on('mousedown', this.onMouseDown);
            this.on('dblclick', this.ondblclick);
            this.pressed = false; // to know when is mousedown
            this.include = true; // to know when we want to include the boundary time in the selection or not
        }
    });

    videojs.RangeSelectorLeft.prototype.init_ = function() {
        this.rs = this.player_.rangeslider;
        this.an = this.player_.annotations;
        videojs.addClass(this.el_, 'include');
    };

    videojs.RangeSelectorLeft.prototype.createEl = function() {
        return videojs.Component.prototype.createEl.call(this, 'div', {
            className: 'vjs-leftselector-anpanel-annotation',
            innerHTML: '<div class="vjs-selector-arrow" title="Left Annotation Selector"></div><div class="vjs-leftselector-back"></div>'
        });
    };


    videojs.RangeSelectorLeft.prototype.onMouseDown = function(event) {
        event.preventDefault();
        
        this.pressed = true;
        videojs.on(document, "mouseup", videojs.bind(this, this.onMouseUp));
        videojs.addClass(this.el_, 'active');
        videojs.addClass(this.el_.parentNode, 'active');
    };

    videojs.RangeSelectorLeft.prototype.onMouseUp = function(event) {
        videojs.off(document, "mouseup", this.onMouseUp, false);
        videojs.removeClass(this.el_, 'active');
        videojs.removeClass(this.el_.parentNode, 'active');
        this.pressed = false;
    };

    videojs.RangeSelectorLeft.prototype.ondblclick = function(event) {
        if (this.include) {
            this.include = false;
            videojs.removeClass(this.el_, 'include');
        } else {
            this.include = true;
            videojs.addClass(this.el_, 'include');
        }
        var left = this.an.rsd.calculateDistance(event);
        this.an.rsd.setPosition(0, left);
    };



    // -- Player--> ControlBar--> BackAnDisplay--> RangeSelectorDisplay--> RangeSelectorRight

    /**
     * Right Time selector
     * @param {videojs.Player|Object} player
     * @param {Object=} options
     * @constructor
     */
    videojs.RangeSelectorRight = videojs.Component.extend({
        /** @constructor */
        init: function(player, options) {
            videojs.Component.call(this, player, options);
            this.on('mousedown', this.onMouseDown);
            this.on('dblclick', this.ondblclick);
            this.pressed = false; // to know when is mousedown
            this.include = true; // to know when we want to include the boundary time in the selection or not
        }
    });

    videojs.RangeSelectorRight.prototype.init_ = function() {
        this.rs = this.player_.rangeslider;
        this.an = this.player_.annotations;
        videojs.addClass(this.el_, 'include');
    };

    videojs.RangeSelectorRight.prototype.createEl = function() {
        return videojs.Component.prototype.createEl.call(this, 'div', {
            className: 'vjs-rightselector-anpanel-annotation',
            innerHTML: '<div class="vjs-selector-arrow" title="Right Annotation Selector"></div><div class="vjs-rightselector-back"></div>'
        });
    };

    videojs.RangeSelectorRight.prototype.onMouseDown = function(event) {
        event.preventDefault();
        
        this.pressed = true;
        videojs.on(document, "mouseup", videojs.bind(this, this.onMouseUp));
        videojs.addClass(this.el_, 'active');
        videojs.addClass(this.el_.parentNode, 'active');
    };

    videojs.RangeSelectorRight.prototype.onMouseUp = function(event) {
        videojs.off(document, "mouseup", this.onMouseUp, false);
        videojs.removeClass(this.el_, 'active');
        videojs.removeClass(this.el_.parentNode, 'active');
        this.pressed = false;
    };

    videojs.RangeSelectorRight.prototype.ondblclick = function(event) {
        if (this.include){
            this.include = false;
            videojs.removeClass(this.el_, 'include');
        }else{
            this.include = true;
            videojs.addClass(this.el_, 'include');
        }
        var left = this.an.rsd.calculateDistance(event);
        this.an.rsd.setPosition(1, left);
    };



    // -- Player--> ControlBar--> BackAnDisplay--> RangeSelectorDisplay--> RangeSelectorBar

    /**
     * Bar to display the selected Time
     * @param {videojs.Player|Object} player
     * @param {Object=} options
     * @constructor
     */
     
    videojs.RangeSelectorBar = videojs.Component.extend({
        /** @constructor */
        init: function(player, options) {
            videojs.Component.call(this, player, options);
        }
    });

    videojs.RangeSelectorBar.prototype.init_ = function() {
        videojs.addClass(this.el_, 'disable');
    };

    videojs.RangeSelectorBar.prototype.options_ = {
        children: {
            'RangeSelectorBarL': {},
            'RangeSelectorBarR': {},
        }
    };

    videojs.RangeSelectorBar.prototype.createEl = function() {
        return videojs.Component.prototype.createEl.call(this, 'div', {
            className: 'vjs-barselector-anpanel-annotation',
        });
    };



    // -- Player--> ControlBar--> BackAnDisplay--> RangeSelectorDisplay--> RangeSelectorBar--> RangeSelectorBarL

    /**
     * This is the left time panel for RangeSelectorBar
     * @param {videojs.Player|Object} player
     * @param {Object=} options
     * @constructor
     */
    videojs.RangeSelectorBarL = videojs.Component.extend({
      /** @constructor */
        init: function(player, options) {
            videojs.Component.call(this, player, options);
        }
    });

    videojs.RangeSelectorBarL.prototype.init_ = function() {};

    videojs.RangeSelectorBarL.prototype.createEl = function() {
        return videojs.Component.prototype.createEl.call(this, 'div', {
            className: 'vjs-barselector-left',
            innerHTML: '<span class="vjs-time-text">00:00</span>',
        });
    };



    // -- Player--> ControlBar--> BackAnDisplay--> RangeSelectorDisplay--> RangeSelectorBar--> RangeSelectorBarR
    /**
     * This is the right time panel for RangeSelectorBar
     * @param {videojs.Player|Object} player
     * @param {Object=} options
     * @constructor
     */
    videojs.RangeSelectorBarR = videojs.Component.extend({
      /** @constructor */
        init: function(player, options) {
            videojs.Component.call(this, player, options);
        }
    });

    videojs.RangeSelectorBarR.prototype.init_ = function() {};

    videojs.RangeSelectorBarR.prototype.createEl = function() {
        return videojs.Component.prototype.createEl.call(this, 'div', {
            className: 'vjs-barselector-right',
            innerHTML: '<span class="vjs-time-text">00:00</span>'
        });
    };



    // -- Player--> ControlBar--> BackAnDisplay--> AnDisplay

    /**
     * Show the annotations in a panel
     * @param {videojs.Player|Object} player
     * @param {Object=} options
     * @constructor
     */
     
    videojs.AnDisplay = videojs.Component.extend({
        /** @constructor */
        init: function(player, options) {
            videojs.Component.call(this, player, options);
            this.on('mousedown', this.onMouseDown);
            this.on('mouseover', this.onMouseOver);
        }
    });

    videojs.AnDisplay.prototype.init_ = function() {
        this.rs = this.player_.rangeslider;
        this.an = this.player_.annotations;
        this.transition = false;
    };

    videojs.AnDisplay.prototype.createEl = function() {
        return videojs.Component.prototype.createEl.call(this, 'div', {
            className: 'vjs-anpanel-annotation',
        });
    };

    videojs.AnDisplay.prototype.onMouseDown = function(event) {
        var elem = $(event.target).parents('.annotator-hl').andSelf();
        var _self = this;
        if (elem.hasClass("annotator-hl")) {
            videojs.on(document, "mouseup", videojs.bind(this, this.onMouseUp));
            // Clone the bar box to make the animation
            var boxup = document.createElement('div');
            var ElemTop = parseFloat(elem[1].style.top);
            var ElemMargin = parseFloat(elem[1].style.marginTop);
            var emtoPx = parseFloat($(elem[1]).css('height'));
            var isPoint = $(elem[1]).hasClass("point");
                
            boxup.className = isPoint ? "boxup-dashed-line point" : "boxup-dashed-line";
            boxup.style.left = elem[1].style.left;
            boxup.style.width = elem[1].style.width;
        
            boxup.style.top = (ElemTop + ElemMargin - this.el_.scrollTop / emtoPx) + 'em';
            elem[0].parentNode.parentNode.appendChild(boxup);
        }
    }

    videojs.AnDisplay.prototype.onMouseUp = function(event) {
        if (typeof this.lastelem === 'undefined')
            return false;
        var elem = this.lastelem;
        var _self = this;
        if (elem.hasClass("annotator-hl")) {
            var annotation = elem.map(function() {
                return $(this).data("annotation");
            })[0];
            var displayHeight = (-1) * parseFloat($(this.el_).parent()[0].style.top);
            var emtoPx = parseFloat($(elem[1]).css('height'));
            if (typeof $(elem).parent().parent().find('.boxup-dashed-line')[0] !== 'undefined') {
                $(elem).parent().parent().find('.boxup-dashed-line')[0].style.top = (displayHeight - 2) + 'em';
            }
            
            this.an.player.pause();
            this.transition = true;
            window.setTimeout(function () {
                _self.an.showAnnotation(annotation);
                _self.transition = false;
                _self.onCloseViewer();
            }, 900);
        }
        videojs.off(document, "mouseup", this.onMouseUp, false);
    };

    videojs.AnDisplay.prototype.onMouseOver = function(event) {
        if (!this.transition && !this.an.rsdl.pressed && !this.an.rsdr.pressed) {
            var annotator = this.an.annotator;
            var elem = $(event.target).parents('.annotator-hl').andSelf();
        
            // if there is a opened annotation then show the new annotation mouse over
            if (typeof annotator !== 'undefined' && annotator.viewer.isShown() && elem.hasClass("annotator-hl")) {
                // hide the last open viewer
                annotator.viewer.hide();
                // get the annotation over the mouse
                var annotations = elem.map(function() {
                    return $(this).data("annotation");
                });
                // show the annotation in the viewer
                annotator.showViewer($.makeArray(annotations), Util.mousePosition(event, annotator.wrapper[0]));
            }
        
            // create dashed line
            elem.addClass('active');
            if (typeof elem !== 'undefined' && $(elem[1]).hasClass('annotation')) {
                // create dashed line under the bar
                var dashed = document.createElement('div');
                var boxdown = document.createElement('div');
                var DisplayHeight = parseFloat(this.an.BackAnDisplay.el_.style.height);
                var ElemMarginTop = elem[1].style.marginTop !== '' ? parseFloat(elem[1].style.marginTop) : 0;
                var ElemTop = parseFloat(elem[1].style.top) + ElemMarginTop;
                var emtoPx = parseFloat($(elem[1]).css('height'));
                var isPoint = $(elem[1]).hasClass("point");

                dashed.className = isPoint ? 'dashed-line point' : 'dashed-line';
                boxdown.className = "box-dashed-line";
                dashed.style.left = boxdown.style.left = elem[1].style.left;
                dashed.style.width = boxdown.style.width = isPoint ? '0' : elem[1].style.width;
                dashed.style.top = ((ElemTop + 1) - this.el_.scrollTop / emtoPx) + 'em';
                dashed.style.height = ((DisplayHeight - ElemTop + 2) + this.el_.scrollTop / emtoPx) + 'em'; // get the absolute value of the top to put in the height
                boxdown.style.top = (DisplayHeight + 2) + 'em';
                elem[0].parentNode.parentNode.appendChild(dashed);
                elem[0].parentNode.parentNode.appendChild(boxdown);
                
                $(this.player).find('.vjs-play-progress').css('z-index', 2);
                $(this.player).find('.vjs-seek-handle').css('z-index', 2);
            }
        
            // store the last selected item
            if (elem.hasClass("annotator-hl"))
                this.lastelem = elem;
        }
    };

    videojs.AnDisplay.prototype.onCloseViewer = function() {
        if (!this.transition) {
            if (typeof this.lastelem !== 'undefined')
                this.lastelem.removeClass('active');
            // remove dashed line
            if (typeof this.lastelem !== 'undefined' && this.lastelem.hasClass("annotator-hl")) {
                $(this.lastelem).parent().parent().find('.dashed-line').remove();
                $(this.lastelem).parent().parent().find('.box-dashed-line').remove();
                $(this.lastelem).parent().parent().find('.boxup-dashed-line').remove();
                $(this.player).find('.vjs-play-progress').css('z-index', "");
                $(this.player).find('.vjs-seek-handle').css('z-index', "");
            }
        }
    };


    videojs.AnDisplay.prototype.countVisibles = function() {
        var AnArray = $.makeArray(this.el_.children);
        // Count visible annotations in Panel
        var count = 0;
        for (var index in AnArray) {
            var an = AnArray[index];
            if (an.style.display !== 'none') {
                count++;
            }
        }
        return count;
    };



    // -- Player--> ControlBar--> BackAnDisplay--> AnStat

    /**
     * Display with a chart with the statistics of the number of Annotations
     * @param {videojs.Player|Object} player
     * @param {Object=} options
     * @constructor
     */
     
    videojs.AnStat = videojs.Component.extend({
        /** @constructor */
        init: function(player, options) {
            videojs.Component.call(this, player, options);
            this.marginTop = 20;
            this.marginBottom = 0;
        }
    });

    videojs.AnStat.prototype.init_ = function() {
        this.rs = this.player_.rangeslider;
        this.an = this.player_.annotations;
        this.canvas = this.el_.children[0];
    };

    videojs.AnStat.prototype.createEl = function() {
        return videojs.Component.prototype.createEl.call(this, 'div', {
            className: 'vjs-anstat-annotation',
            innerHTML: '<canvas class="vjs-char-anstat-annotation">Your browser does not support the HTML5 canvas tag.</canvas>',
        });
    };

    videojs.AnStat.prototype.paintCanvas = function() {
        var ctx = this.canvas.getContext("2d");
        var points = this._getPoints();
        var w = this._getWeights(points);
        var maxEn = this._getMaxArray(points, 'entries');
        var TotAn = this.an.AnDisplay.el_.children.length;
        var duration = this.an.player.duration();

        // set the position of the canvas
        this.canvas.style.marginTop = Math.round(this.marginTop) + 'px';
        
        // Add the Max Concentration and Number of annotations
        if($(this.canvas).parent().find('.vjs-totan-anstat-annotation').length === 0) {
            $(this.canvas).parent().append('<div class="vjs-totan-anstat-annotation">');
            $(this.canvas).parent().append('<div class="vjs-maxcon-anstat-annotation">');
        }
        var textCanvas = $(this.canvas).parent().find('.vjs-totan-anstat-annotation')[0];
        textCanvas.innerHTML = TotAn + ' total annotations';
        var textCanvas = $(this.canvas).parent().find('.vjs-maxcon-anstat-annotation')[0];
        textCanvas.innerHTML = 'Max Annotations = ' + maxEn;
        
        // Added dashed line function to paint
        if (window.CanvasRenderingContext2D && CanvasRenderingContext2D.prototype.lineTo) {
            CanvasRenderingContext2D.prototype.dashedLine = function(x1, y1, x2, y2, dashLen) {
                if (dashLen === undefined) dashLen = 2;

                this.beginPath();
                this.moveTo(x1, y1);

                var dX = x2 - x1;
                var dY = y2 - y1;
                var dashes = Math.floor(Math.sqrt(dX * dX + dY * dY) / dashLen);
                var dashX = dX / dashes;
                var dashY = dY / dashes;

                var q = 0;
                while (q++ < dashes) {
                 x1 += dashX;
                 y1 += dashY;
                 this[q % 2 == 0 ? 'moveTo' : 'lineTo'](x1, y1);
                }
                this[q % 2 == 0 ? 'moveTo' : 'lineTo'](x2, y2);

                this.stroke();
                this.closePath();
            };
        };    
            
        
        // set the canvas size
        this.canvas.height = this.an.AnDisplay.el_.offsetHeight - (this.marginTop + this.marginBottom);
        this.canvas.width  = this.an.AnDisplay.el_.offsetWidth;
        
        ctx.beginPath();
        ctx.strokeStyle = "rgb(255, 163, 0)";
        var lastSe = 0;
        var lastEn = 0;
        ctx.moveTo(0, maxEn * w.Y); // Move pointer to 0, 0
        for (var index in points) {
            var p = points[index];
            var x1 = lastSe * w.X, y1 = (maxEn - lastEn) * w.Y; // Old Point
            var x2 = p.second * w.X, y2 = (maxEn - p.entries) * w.Y; // New Point
            // new line
            ctx.lineTo(x2, y1); // move horizontally to the new point
            ctx.moveTo(x2, y1); // Move pointer
            ctx.lineTo(x2, y2); // move vertically to the new point height
            ctx.moveTo(x2, y2); // Prepare pointer for a new instance
            // new rectangle under the curve
            ctx.fillStyle = "rgba(0, 0, 0, 0.5)";
            ctx.fillRect(x1, y1, (x2 - x1), (maxEn * w.Y - y1));
            
            // store the last point
            lastSe = p.second;
            lastEn = p.entries;
        }
        // set the graphic to the end of the video
        ctx.lineTo(lastSe * w.X, maxEn * w.Y); 
        ctx.moveTo(lastSe * w.X, maxEn * w.Y); 
        ctx.lineTo(duration * w.X, maxEn * w.Y);
        ctx.stroke();
        
        // dashed line down
        ctx.beginPath();
        ctx.dashedLine(0, maxEn * w.Y, duration * w.X, maxEn * w.Y, 8);
        ctx.stroke();
        // dashed line top
        ctx.beginPath();
        ctx.dashedLine(0, 0, duration * w.X, 0, 8);
        ctx.stroke();
    };

    videojs.AnStat.prototype._getWeights = function(points){
        var weight = {};
        var panel = $(this.an.AnDisplay.el_);
        var maxSe = this.an.player.duration();
        var maxEn = this._getMaxArray(points, 'entries');
        var panelW = parseFloat(panel.css('width'));
        var panelH = parseFloat(panel.css('height')) - (this.marginTop + this.marginBottom);
        weight.X = maxSe != 0 ? (panelW / maxSe) : 0;
        weight.Y = maxEn != 0 ? (panelH / maxEn) : 0;
        return weight;
    };

    videojs.AnStat.prototype._getMaxArray = function(points, variable) {
        var highest = 0;
        var tmp;
        for (var index in points) {
            tmp = points[index][variable];
            if (tmp > highest) highest = tmp;
        }
        return highest;
    };

    videojs.AnStat.prototype._getPoints = function() {
        var points = [];
        var allannotations = this.an.annotator.plugins.Store.annotations;
        for (var index in allannotations) {
            var an = allannotations[index];
            var start, end;
            if (this.an._isVideoJS(an)) {
                start = an.rangeTime.start;
                end = an.rangeTime.end;
                // start
                if (!this._isFound(points, start)) {
                    points.push({
                        second:an.rangeTime.start,
                        entries:this._getNumberAnnotations(start)
                    });
                    if (an.rangeTime.start == an.rangeTime.end){ // is a point
                        points.push({
                            second:an.rangeTime.end,
                            entries:this._getNumberAnnotations(end, true)
                        });
                    }
                }
                // end
                if (!this._isFound(points, end)) {
                    points.push({
                        second:an.rangeTime.end,
                        entries:this._getNumberAnnotations(end, true)
                    });
                }
                    
                found = false;
            }
        }
        points.sort(function(a, b) {
            return parseFloat(a.second) - parseFloat(b.second)
        });
        return points;
    };

    videojs.AnStat.prototype._isFound = function(array, elem) {
        var found = false;
        for (var indexA in array) {
            if(typeof array[indexA].second !== 'undefined' && array[indexA].second == elem)
                found = true;
        }
        return found;
    };

    videojs.AnStat.prototype._getNumberAnnotations = function(time, end) {
        var num = (typeof end !== 'undefined' && end) ? -1 : 0;
        var allannotations = this.an.annotator.plugins['Store'].annotations;
        for (var index in allannotations) {
            var an = allannotations[index];
            if (this.an._isVideoJS(an)) {
                if(an.rangeTime.start <= time && an.rangeTime.end >= time)
                    num++;
            }
        }
        return num;
    };

    // -- Player--> ControlBar--> BackAnDisplayScroll

    /**
     * The background annotations panel
     * @param {videojs.Player|Object} player
     * @param {Object=} options
     * @constructor
     */
     
    videojs.BackAnDisplayScroll = videojs.Component.extend({
          /** @constructor */
        init: function(player, options) {
            videojs.Component.call(this, player, options);
            this.on('mousedown', this.onMouseDown);
            this.UpValue = 0.1;
            this.currentValue = 0;
        }
    });

    videojs.BackAnDisplayScroll.prototype.init_ = function() {
        this.rs = this.player_.rangeslider;
        this.an = this.player_.annotations;
        this.mousedownID = -1;
        var self = this;
        var direction;
            
        // Firefox
        $(this.an.AnDisplay.el_).bind('DOMMouseScroll', function(e) {
            if (e.originalEvent.detail > 0)
                direction = self.UpValue;
            else 
                direction = -self.UpValue;
            self.an.backDSBarSel.setPosition(self.getPercentScroll() + direction);
            return false;
        });

        // IE, Opera, Safari
        $(this.an.AnDisplay.el_).bind('mousewheel', function(e) {
            if (e.originalEvent.wheelDelta < 0) 
                direction = self.UpValue;
            else 
                direction = -self.UpValue;
            self.an.backDSBarSel.setPosition(self.getPercentScroll() + direction);
            return false;
        });
    };

    videojs.BackAnDisplayScroll.prototype.options_ = {
        children: {
            'BackAnDisplayScrollBar': {},
            'BackAnDisplayScrollTime': {},
        }
    };

    videojs.BackAnDisplayScroll.prototype.createEl = function() {
      return videojs.Component.prototype.createEl.call(this, 'div', {
        className: 'vjs-scroll-anpanel-annotation',
        innerHTML: '<div class="vjs-up-scroll-annotation"></div><div class="vjs-down-scroll-annotation"></div>',
      });
    };

    videojs.BackAnDisplayScroll.prototype.onMouseDown = function(event) {
        var self = this;
        if (event.target.className === 'vjs-scrollbar-anpanel-annotation') {
            // change position with a click in the scrollbar
            this.an.backDSBarSel.onMouseMove(event);
            return false;
        } else if (event.target.className === 'vjs-scrollbar-selector') {
            // change position with scrollbar
            // this event is controlled by this.an.backDSBarSel
            return false;
        } else {
            // change position with arrows
            var direction = event.target.className=='vjs-down-scroll-annotation' ? this.UpValue : -this.UpValue;
            videojs.on(document, "mouseup", videojs.bind(this, this.onMouseUp));
            if(parseInt(this.mousedownID, 10) === -1) {  // Prevent multimple loops!
                this.mousedownID = setInterval(function () {
                    var pos = Math.max(0, Math.min(1, self.getPercentScroll() + direction));
                    self.an.backDSBarSel.setPosition(pos);
                }, 100);
            }
        }
    };

    videojs.BackAnDisplayScroll.prototype.onMouseUp = function(event) {
        videojs.off(document, "mouseup", this.onMouseUp, false);
        var self = this;
        if(parseInt(this.mousedownID, 10) != -1) { // Only stop if exists
            clearInterval(this.mousedownID);
            self.mousedownID = -1;
        }
    };

    videojs.BackAnDisplayScroll.prototype.getPercentScroll = function() {
        var scroll = this.an.AnDisplay.el_;
        var maxscroll = scroll.scrollHeight - scroll.offsetHeight;
        var currentValue = scroll.scrollTop;
        return Math.max(0, Math.min(1, maxscroll !== 0 ? (currentValue / maxscroll) : 0));
    };

    videojs.BackAnDisplayScroll.prototype.setPercentScroll = function(percent) {
        var scroll = this.an.AnDisplay.el_;
        var maxscroll = scroll.scrollHeight-scroll.offsetHeight;
        percent = Math.max(0, Math.min(1, percent ? percent : 0));
        scroll.scrollTop = Math.round(maxscroll * percent);
    };



    // -- Player--> ControlBar--> BackAnDisplayScroll--> BackAnDisplayScrollBar

    /**
     * The Scroll bar for the display
     * @param {videojs.Player|Object} player
     * @param {Object=} options
     * @constructor
     */
     
    videojs.BackAnDisplayScrollBar = videojs.Component.extend({
          /** @constructor */
        init: function(player, options) {
            videojs.Component.call(this, player, options);
        }
    });

    videojs.BackAnDisplayScrollBar.prototype.init_ = function() {};

    videojs.BackAnDisplayScrollBar.prototype.options_ = {
        children: {
            'ScrollBarSelector': {},
        }
    };

    videojs.BackAnDisplayScrollBar.prototype.createEl = function() {
      return videojs.Component.prototype.createEl.call(this, 'div', {
        className: 'vjs-scrollbar-anpanel-annotation',
      });
    };



    // -- Player--> ControlBar--> BackAnDisplayScroll--> BackAnDisplayScrollBar--> ScrollBarSelector

    /**
     * The Scroll bar for the display
     * @param {videojs.Player|Object} player
     * @param {Object=} options
     * @constructor
     */
     
    videojs.ScrollBarSelector = videojs.Component.extend({
          /** @constructor */
        init: function(player, options) {
            videojs.Component.call(this, player, options);
            this.on('mousedown', this.onMouseDown);
        }
    });

    videojs.ScrollBarSelector.prototype.init_ = function() {
        this.rs = this.player_.rangeslider;
        this.an = this.player_.annotations;
        videojs.addClass(this.an.backDSBar.el_, 'disable');
    };


    videojs.ScrollBarSelector.prototype.createEl = function() {
        return videojs.Component.prototype.createEl.call(this, 'div', {
            className: 'vjs-scrollbar-selector',
        });
    };

    videojs.ScrollBarSelector.prototype.onMouseDown = function(event) {
        event.preventDefault();
        videojs.on(document, "mousemove", videojs.bind(this, this.onMouseMove));
        videojs.on(document, "mouseup", videojs.bind(this, this.onMouseUp));
    }

    videojs.ScrollBarSelector.prototype.onMouseUp = function(event) {
        videojs.off(document, "mousemove", this.onMouseMove, false);
        videojs.off(document, "mouseup", this.onMouseUp, false);
    };

    videojs.ScrollBarSelector.prototype.onMouseMove = function(event) {
        var top = this.calculateDistance(event);
        top = this.parseMaxPercent(top); // set the max value fixing the height of the handle
        this.setPosition(top);
    }

    videojs.ScrollBarSelector.prototype.calculateDistance = function(event) {
        var scrollY = this.getscrollY();
        var scrollH = this.getscrollHeight();
        var handleH = this.getHeight();
        
        // Adjusted X and Width, so handle doesn't go outside the bar
        scrollY = scrollY + (handleH);
        scrollH = scrollH - (handleH);
        // Adjusted X and Width, so handle doesn't go outside the bar
        // Percent that the click is through the adjusted area
        return Math.max(0, Math.min(1, (event.pageY - scrollY) / scrollH));
    };

    videojs.ScrollBarSelector.prototype.getscrollHeight = function() {
        return this.el_.parentNode.offsetHeight;
    };
    videojs.ScrollBarSelector.prototype.getscrollY = function() {
        return videojs.findPosition(this.el_.parentNode).top;
    };
    videojs.ScrollBarSelector.prototype.getHeight = function() {
        return this.el_.offsetHeight;
    };
    videojs.ScrollBarSelector.prototype.parseMaxHeight = function(top) {
        var scrollH = this.getscrollHeight();
        var handleH = this.getHeight();
        var percent = handleH / scrollH;
        return Math.max(0, Math.min(1 - percent, top));
    };

    videojs.ScrollBarSelector.prototype.parseMaxPercent = function(top) {
        var scrollH = this.getscrollHeight();
        var handleH = this.getHeight();
        var percent = handleH / scrollH;
        var newTop = top;
        if (top >= (1 - percent))
            newTop = 1;
        return newTop;
    };

    videojs.ScrollBarSelector.prototype.setPosition = function(top, showBar) {
        var showBar = typeof showBar !== 'undefined' ? showBar : true;
        
        // Check for invalid position
        if (isNaN(top)) 
            return false;
        
        // Check if there is enough annotations to scroll
        if (!this.isScrollable())
            return false;
            
        // Show the Scrollbar
        if (showBar) {
            videojs.removeClass(this.an.backDSBar.el_, 'disable')
        }
        
        // Alias
        var Obj = this.el_;
        var scroll = this.an.BackAnDisplayScroll;
        var scrollTime = this.an.backDSTime;
        
        Obj.style.top = (this.parseMaxHeight(top) * 100) + '%';
        scroll.setPercentScroll(top);
        
        // Set the times in the scroll time panel
        scrollTime.setTimes();
        
        // Hide the Scrollbar in 1 sec
        if(showBar) {
            var _self = this;
            if (typeof this.Timeout !== 'undefined')
                clearTimeout(this.Timeout);
            this.Timeout = window.setTimeout(function () {
                videojs.addClass(_self.an.backDSBar.el_, 'disable');
            }, 1000);
        }
        
        // set current position
        this.an.BackAnDisplayScroll.currentValue = top;
        return true;
    }

    videojs.ScrollBarSelector.prototype.isScrollable = function() {
        var scroll = this.an.AnDisplay.el_;
        var emtoPx = parseFloat($(scroll).find('.annotation').css('height'));
        var minTop = parseInt(scroll.offsetHeight/emtoPx);
        
        // Count visible annotations in Panel
        var count = this.an.AnDisplay.countVisibles();
        return (count > minTop);
    }



    // -- Player--> ControlBar--> BackAnDisplayScroll--> BackAnDisplayScrollTime

    videojs.BackAnDisplayScrollTime = videojs.Component.extend({
          /** @constructor */
        init: function(player, options) {
            videojs.Component.call(this, player, options);
        }
    });

    videojs.BackAnDisplayScrollTime.prototype.init_ = function() {
        this.rs = this.player_.rangeslider;
        this.an = this.player_.annotations;
    };

    videojs.BackAnDisplayScrollTime.prototype.createEl = function() {
      return videojs.Component.prototype.createEl.call(this, 'div', {
        className: 'vjs-scrolltime-anpanel-annotation',
        innerHTML: '<div class="vjs-up-scrolltime-annotation"><span class="vjs-time-text"></span></div><div class="vjs-down-scrolltime-annotation"><span class="vjs-time-text"></span></div>',
      });
    };

    videojs.BackAnDisplayScrollTime.prototype.setTimes = function() {
        var AnPos = this.getAnnotationPosition();
        var AnEl = this.getElements(AnPos);
        var AnTimes = this.getTimes(AnEl);
        if (AnTimes.top != 'Invalid Date') {
            $(this.el_).find('.vjs-up-scrolltime-annotation')[0].style.visibility = '';
            $(this.el_).find('.vjs-up-scrolltime-annotation span')[0].innerHTML = AnTimes.top;
        } else {
            $(this.el_).find('.vjs-up-scrolltime-annotation')[0].style.visibility = 'hidden';
        }
        if (AnTimes.bottom != 'Invalid Date') {
            $(this.el_).find('.vjs-down-scrolltime-annotation')[0].style.visibility = '';
            $(this.el_).find('.vjs-down-scrolltime-annotation span')[0].innerHTML = AnTimes.bottom;
        } else {
            $(this.el_).find('.vjs-down-scrolltime-annotation')[0].style.visibility = 'hidden';
        }
    };

    videojs.BackAnDisplayScrollTime.prototype.getAnnotationPosition = function() {
        var backDSBarSel = this.an.backDSBarSel;
        var percent = backDSBarSel.parseMaxPercent(parseFloat(backDSBarSel.el_.style.top) / 100);
        var scroll = this.an.AnDisplay.el_;
        var maxTop = scroll.scrollHeight;
        var minTop = scroll.offsetHeight;
        var maxBottom = maxTop - minTop;
        var minBottom = 0;
        var pos = {};
        
        percent = percent || 0;
        pos.top = Math.max(minTop, Math.min(maxTop, maxBottom * percent + scroll.offsetHeight));
        pos.bottom = Math.max(minBottom, Math.min(maxBottom, maxBottom * percent));
        return pos;
    };

    videojs.BackAnDisplayScrollTime.prototype.getElements = function(AnPos) {
        var AnPos = AnPos || {};
        var scroll = this.an.AnDisplay.el_;
        var emtoPx = parseFloat($(scroll).find('.annotation').css('height'));
        var maxTop = parseInt(scroll.scrollHeight / emtoPx);
        var minTop = parseInt(scroll.offsetHeight / emtoPx);
        var maxBottom = (maxTop - minTop);
        var minBottom = 0;
        var AnEl = {};
        AnEl.top = Math.max(minTop, Math.min(maxTop, parseInt(AnPos.top / emtoPx)));
        AnEl.bottom = Math.max(minBottom, Math.min(maxBottom, parseInt(AnPos.bottom / emtoPx)));
        return AnEl;
    };

    videojs.BackAnDisplayScrollTime.prototype.getTimes = function(AnEl) {
        var AnEl = AnEl || {};
        var AnTimes = {};
        var TopEl, BottomEl, AnTop, AnBottom;
        var AnArray = $.makeArray(this.an.AnDisplay.el_.children);
        AnEl.top = AnEl.top || 0;
        AnEl.bottom = AnEl.bottom || 0;
        
        // Get HTML Elements
        var count = 0;
        var lastEl;
        for (var index in AnArray) {
            var an = AnArray[index];
            if (an.style.display !== 'none') {
                if (count == AnEl.bottom) {
                    TopEl = an;
                } else if (count == AnEl.top) {
                    BottomEl = an;
                }
                lastEl = an;
                count++;
            }
        }
        if (typeof BottomEl === 'undefined')
            BottomEl = lastEl;
            
        // Annotation Element
        AnTop = typeof TopEl !== 'undefined' ? $.data(TopEl, 'annotation') : undefined;
        AnBottom = typeof BottomEl !== 'undefined' ? $.data(BottomEl, 'annotation') : undefined;
        // Update of the element
        AnTimes.top = (typeof AnTop !== 'undefined' && typeof AnTop.updated !== 'undefined') ? AnTop.updated : '';
        AnTimes.bottom = (typeof AnBottom !=='undefined' && typeof AnBottom.updated !== 'undefined') ? AnBottom.updated : '';
        // Format
        AnTimes.top = new Date(AnTimes.top !== '' ? createDateFromISO8601(AnTimes.top) : '');
        AnTimes.bottom = new Date(AnTimes.bottom != '' ? createDateFromISO8601(AnTimes.bottom) : '');
        return AnTimes;
    };
}) ();
