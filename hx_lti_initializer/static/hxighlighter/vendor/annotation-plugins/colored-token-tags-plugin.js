/**
 *  Colored Token Tags Plugin
 *  
 *  Should be generic, but its main purpose is to be used in tandem with annotations.
 *
 */

(function($){

    /**
     * @constructor
     * @params {Object} options - specific options for this plugin
     */
    $.ColoredTokenTags = function(options, instanceID) {
        this.options = jQuery.extend({}, options);
        this.init();
        this.instanceID = instanceID;
        return this;
    };

    /**
     * Initializes instance
     */
    $.ColoredTokenTags.prototype.init = function() {
        if (typeof jQuery(window).tokenInput !== "function") {
            hxLogging("You must include tokeninput.js and token-input.css on this page in order to use this plugin", "error");
        }
        var self = this;
        var tags = self.options.tags.split(',');
        self.colorDict = {};
        if (self.options.hasColors) {
            jQuery.each(tags, function(_, tag) {
                var splitTag = tag.split(':');
                self.colorDict[splitTag[0]] = self.colorSetUp(splitTag[1]);
            });

            // From https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object/keys
            if (!Object.keys) {
                Object.keys = (function() {
                'use strict';
                var hasOwnProperty = Object.prototype.hasOwnProperty,
                    hasDontEnumBug = !({ toString: null }).propertyIsEnumerable('toString'),
                    dontEnums = [
                        'toString',
                        'toLocaleString',
                        'valueOf',
                        'hasOwnProperty',
                        'isPrototypeOf',
                        'propertyIsEnumerable',
                        'constructor'
                    ],
                    dontEnumsLength = dontEnums.length;

                return function(obj) {
                    if (typeof obj !== 'function' && (typeof obj !== 'object' || obj === null)) {
                    throw new TypeError('Object.keys called on non-object');
                    }

                    var result = [], prop, i;

                    for (prop in obj) {
                    if (hasOwnProperty.call(obj, prop)) {
                        result.push(prop);
                    }
                    }

                    if (hasDontEnumBug) {
                    for (i = 0; i < dontEnumsLength; i++) {
                        if (hasOwnProperty.call(obj, dontEnums[i])) {
                        result.push(dontEnums[i]);
                        }
                    }
                    }
                    return result;
                };
                }());
            }
            tags = Object.keys(self.colorDict);
        }

        self.options.tags = self.convertTagsToTokenObjects(tags);
    };

    /**
     * 
     * @param element {HTMLElement} - where the annotation will be added
     * @param selector {String} - selector to find input it is replacing
     */
    $.ColoredTokenTags.prototype.addTokenTagField = function(element, selector) {
        element.find(selector).append('<input type="text" id="in-' + this.instanceID + '" class="token-tag-field"></div>');
        this.field = element.find('.token-tag-field');
        this.field.tokenInput(this.options.tags);
    };

    $.ColoredTokenTags.prototype.convertTagsToTokenObjects = function(arr) {
        var finalList = [];
        jQuery.each(arr, function(_, tag) {
            finalList.push({
                'id': tag,
                'name': tag
            });
        })
        return finalList;
    };

    $.ColoredTokenTags.prototype.returnValue = function() {
        return this.field.tokenInput('get').map(function(val){ return val['name'] });
    };

    $.ColoredTokenTags.prototype.destroy = function(element, selector) {
        this.field.remove();
    };

    $.ColoredTokenTags.prototype.addTagToField = function(tag) {
        if (typeof this.field !== "undefined") {
            this.field.tokenInput('add', {
                'id': tag,
                'name': tag
            });
        }
    };

    // Annotation specific functions

    $.ColoredTokenTags.prototype.annotationListeners = function() {
        var self = this;

        hxSubscribe('editorToBeHidden', self.instanceID, function(){
            self.destroy();
            self.obs.disconnect();
        }.bind(this));
    };

    $.ColoredTokenTags.prototype.saving = function(annotation) {
        try {
            var annotationTags = this.returnValue();

            if (typeof this.options.validator === "function") {
                annotationText = this.options.validator(annotationTags);
            }
     
            annotation['tags'] = annotationTags;
        } catch(e) {
            console.log('plugin was never started');
        }
        return annotation;
    };

    $.ColoredTokenTags.prototype.editorShown = function(annotation, editor) {
        var self = this;
        self.addTokenTagField(editor, '.plugin-area');
        if (annotation.tags) {
            jQuery.each(annotation.tags, function(_, tag) {
                self.addTagToField(tag)
            });
        } else if (annotation.schema_version && annotation.schema_version === "catch_v2") {
            var tags = returnWATags(annotation);
            hxLogging(tags);
            jQuery.each(tags, function(_, tag) {
                self.addTagToField(tag)
            });
        }
        jQuery('.token-input-input-token input').attr('placeholder', 'Add a tag...');

        jQuery.each(jQuery(editor).find('.token-input-token p'), function(_, tagElement) {
            var elemObj = jQuery(tagElement);
            var color = self.colorDict[elemObj.text().trim()] || '#FFFFFF';
            elemObj.parent().css({
                'background': color,
                'color': 'black'
            });
        });
        self.obs = watchForChange('.token-input-list', function(event) {
            jQuery.each(jQuery(event[0].target).find('.token-input-token p'), function(_, tagElement) {
                var elemObj = jQuery(tagElement);
                var color = self.colorDict[elemObj.text().trim()] || '#FFFFFF';
                elemObj.parent().css({
                    'background': color,
                    'color': 'black'
                });
            });
        });
    };

    $.ColoredTokenTags.prototype.viewerShown = function(annotations, viewer) {
        var self = this;
        jQuery.each(viewer.find('.annotation-tag'), function(_, tagElement) {
            var elemObj = jQuery(tagElement);
            var color = self.colorDict[elemObj.html().trim()] || '#FFFFFF';
            elemObj.css({
                'background': color,
                'color': 'black'
            });
        });
    };

    $.ColoredTokenTags.prototype.annotationDrawn = function(annotation) {
        var self= this;
        if (!exists(annotation.tags) || annotation.tags.length == 0) {
            return;
        }
        jQuery.each(annotation._local['highlights'], function(_, high) {
            var elemObj = jQuery(high);
            var lastTag = annotation.tags[annotation.tags.length-1];
            var color = self.colorDict[lastTag] || 'rgba(255,255,0,0.3)';
            elemObj.css({
                'background': color,
            });
        });
    };

    $.ColoredTokenTags.prototype.colorSetUp = function(color1) {
        var values = { red:null, green:null, blue:null, alpha:null };
        var color = color1;
        var stdCol = { acqua:'#0ff',   teal:'#008080',   blue:'#00f',      navy:'#000080',
                       yellow:'#ff0',  olive:'#808000',  lime:'#0f0',      green:'#008000',
                       fuchsia:'#f0f', purple:'#800080', red:'#f00',       maroon:'#800000',
                       white:'#fff',   gray:'#808080',   silver:'#c0c0c0', black:'#000' };
        if( stdCol[color1]!==undefined ) {
            color = stdCol[color1];
        }
        if( typeof color == 'string' ){
            /* hex */
            if( color.indexOf('#') === 0 ){
                color = color.substr(1)
                if( color.length == 3 )
                    values = {
                        red:   parseInt( color[0]+color[0], 16 ),
                        green: parseInt( color[1]+color[1], 16 ),
                        blue:  parseInt( color[2]+color[2], 16 ),
                        alpha: 0.3
                    };
                else
                    values = {
                        red:   parseInt( color.substr(0,2), 16 ),
                        green: parseInt( color.substr(2,2), 16 ),
                        blue:  parseInt( color.substr(4,2), 16 ),
                        alpha: 0.3
                    };
            /* rgb */
            }else if( color.indexOf('rgb(') === 0 ){
                var pars = color.indexOf(',');
                values = {
                    red:   parseInt(color.substr(4,pars)),
                    green: parseInt(color.substr(pars+1,color.indexOf(',',pars))),
                    blue:  parseInt(color.substr(color.indexOf(',',pars+1)+1,color.indexOf(')'))),
                    alpha: 0.3
                };
            /* rgba */
            }else if( color.indexOf('rgba(') === 0 ){
                var pars = color.indexOf(',');
                var repars = color.indexOf(',',pars+1);
                values = {
                    red:   parseInt(color.substr(5,pars)),
                    green: parseInt(color.substr(pars+1,repars)),
                    blue:  parseInt(color.substr(color.indexOf(',',pars+1)+1,color.indexOf(',',repars))),
                    alpha: parseFloat(color.substr(color.indexOf(',',repars+1)+1,color.indexOf(')')))
                };
            /* verbous */
            }
        }
        return 'rgba(' + values.red + ',' + values.green + ',' + values.blue + ',' + values.alpha + ')';
    };

}(window));