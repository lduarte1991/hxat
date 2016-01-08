/***
 * AnnotationMain.js
 *
 * This file should be the main controller for syncing processes
 * between Core, Dahsboard, and Target objects. 
 ***/

(function($) {
	$.AnnotationMain = function(options_param) {
		if (window.AController.main) {
			return window.AController.main;
		};
		this.initOptions = jQuery.extend({}, options_param);
		this.tags = this.setUpHighlightTags();
		return this;
	};

	/* initForText
	 * 
	 */
	$.AnnotationMain.prototype.initForText = function(){

	};

	/* initForText
	 * 
	 */
	$.AnnotationMain.prototype.initForVideo = function(){

	};

	$.AnnotationMain.prototype.getRGB = function(item) {
	    function getColorValues( color ){
		    var values = { red:null, green:null, blue:null, alpha:null };
		    if( typeof color == 'string' ){
		        /* hex */
		        if( color.indexOf('#') === 0 ){
		            color = color.substr(1)
		            if( color.length == 3 )
		                values = {
		                    red:   parseInt( color[0]+color[0], 16 ),
		                    green: parseInt( color[1]+color[1], 16 ),
		                    blue:  parseInt( color[2]+color[2], 16 ),
		                    alpha: .3
		                }
		            else
		                values = {
		                    red:   parseInt( color.substr(0,2), 16 ),
		                    green: parseInt( color.substr(2,2), 16 ),
		                    blue:  parseInt( color.substr(4,2), 16 ),
		                    alpha: .3
		                }
		        /* rgb */
		        }else if( color.indexOf('rgb(') === 0 ){
		            var pars = color.indexOf(',');
		            values = {
		                red:   parseInt(color.substr(4,pars)),
		                green: parseInt(color.substr(pars+1,color.indexOf(',',pars))),
		                blue:  parseInt(color.substr(color.indexOf(',',pars+1)+1,color.indexOf(')'))),
		                alpha: .3
		            }
		        /* rgba */
		        }else if( color.indexOf('rgba(') === 0 ){
		            var pars = color.indexOf(','),
		                repars = color.indexOf(',',pars+1);
		            values = {
		                red:   parseInt(color.substr(5,pars)),
		                green: parseInt(color.substr(pars+1,repars)),
		                blue:  parseInt(color.substr(color.indexOf(',',pars+1)+1,color.indexOf(',',repars))),
		                alpha: parseFloat(color.substr(color.indexOf(',',repars+1)+1,color.indexOf(')')))
		            }
		        /* verbous */
		        }else{
		            var stdCol = { acqua:'#0ff',   teal:'#008080',   blue:'#00f',      navy:'#000080',
		                           yellow:'#ff0',  olive:'#808000',  lime:'#0f0',      green:'#008000',
		                           fuchsia:'#f0f', purple:'#800080', red:'#f00',       maroon:'#800000',
		                           white:'#fff',   gray:'#808080',   silver:'#c0c0c0', black:'#000' };
		            if( stdCol[color]!==undefined )
		                values = getColorValues(stdCol[color]);
		        }
		    }
		    return values;
		}
	    return getColorValues(item);
	};

	$.AnnotationMain.prototype.setUpHighlightTags = function(){
		var self = window.AController.main || this;
		console.log(self);
		var tagOptions = self.initOptions.annotationMainOptions.highlightTags_options;
		if (typeof tagOptions !== 'undefined') {
			var fin = {};
			var prelim = tagOptions.split(',');

			prelim.forEach(function(item) {
				var temp = item.split(':');
				fin[temp[0]] = self.getRGB(temp[1]);
			});

			return fin;
		};
		return {};
	};

	$.AnnotationMain.prototype.colorizeAnnotation = function(annotation) {
		var self = this;
		if (typeof annotation["@type"] !== "undefined") {
			var colorTag = undefined
			annotation.resource.forEach(function(item){
				if (item["@type"] == "oa:Tag") {
					if (typeof self.tags[item["chars"]] !== "undefined") {
						colorTag = item["chars"];
					}
				}
			});

			if (typeof window.AController.targetObjectController !== "undefined" && typeof colorTag !== "undefined") {
				window.AController.targetObjectController.colorizeAnnotation(annotation["@id"], self.tags[colorTag]);

			};

		} else if (typeof annotation.tags !== "undefined" && annotation.tags.length > 0) {
			var colorTag = undefined;
			annotation.tags.forEach(function (tag) {
				if (typeof self.tags[tag] !== "undefined") {
					colorTag = tag;
				};
			});
			console.log(window.AController.targetObjectController);
			if (typeof window.AController.targetObjectController !== "undefined" && typeof colorTag !== "undefined") {
				window.AController.targetObjectController.colorizeAnnotation(annotation, self.tags[colorTag]);
			};
		};
	};

	$.AnnotationMain.prototype.colorizeAnnotations = function(annotations) {
		var self = this;
		annotations.forEach(function(annotation) {
			self.colorizeAnnotation(annotation);
		});
	};

	$.AnnotationMain.prototype.colorizeViewer = function() {
		window.AController.targetObjectController.colorizeViewer();
	}

}(AController));
