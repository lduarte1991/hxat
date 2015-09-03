/* 
 HighlightTags Annotator Plugin v1.0 (https://github.com/lduarte1991/tags-annotator)
 Copyright (C) 2014 Luis F Duarte
 License: https://github.com/lduarte1991/tags-annotator/blob/master/LICENSE.rst
 
 This program is free software; you can redistribute it and/or
 modify it under the terms of the GNU General Public License
 as published by the Free Software Foundation; either version 2
 of the License, or (at your option) any later version.
 
 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.
  
 You should have received a copy of the GNU General Public License
 along with this program; if not, write to the Free Software
 Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
*/

Annotator.Plugin.HighlightTags = function(element, options) {
	
	// extends the Plugin class from Annotator
	Annotator.Plugin.apply(this, arguments);

	this.field = null;
	//this.prototype.input = null;
	this.colors = null;
	//this.prototype.isFirstTime = true;
	return this;
};

// Set the plugin prototype. This gives us all of the Annotator.Plugin methods.
Annotator.Plugin.HighlightTags.prototype = new Annotator.Plugin();
Annotator.Plugin.HighlightTags.prototype.tokensavailable = [];

Annotator.Plugin.HighlightTags.prototype.pluginInit = function() {
	// Check that Annotator is working
	if (!Annotator.supported()) {
		return;
	}

	// adds the field for them to enter tags in the editor
	var self = Annotator._instances[0].plugins.HighlightTags;
	self.field = self.annotator.editor.addField({
		type: 'input',
		label: 'Add tags...',
		load: self.updateField,
		submit: self.pluginSubmit,
	});

	$(self.field).html("<div><input placeholder =\"Add tags...\" type=\"text\" id=\"tag-input\" name=\"tags\" /></div>");

	// predetermined instructor tags are stored
	var tags = self.options.tag.split(",");

	// tags are given the structure that the dropdown/token function requires
    tags.forEach(function(tagnames) {
        lonename = tagnames.split(":");
        self.tokensavailable.push({'id': lonename[0], 'name': lonename[0]});
    });

	// now that #tag-input is in place, add the tokens to autocomplete
    $('#tag-input').tokenInput(self.tokensavailable);

    self.colors = self.getHighlightTags();

    var newview = self.annotator.viewer.addField({
        load: self.updateViewer,
    });
    // all of these need time for the annotations database to respond
    this.annotator.subscribe('annotationsLoaded', function(){setTimeout(function(){self.colorize()}, 1000)});
    self.annotator.subscribe('annotationUpdated', function(){setTimeout(function(){self.colorize()}, 1000)});
    self.annotator.subscribe('flaggedAnnotation', self.updateViewer);
    self.annotator.subscribe('annotationCreated', function(){setTimeout(function(){self.colorize()}, 1000)});
    self.annotator.subscribe('externalCallToHighlightTags', function(){setTimeout(function(){self.externalCall()}, 1000)});
    self.annotator.subscribe('colorEditorTags', self.colorizeEditorTags);
};

Annotator.Plugin.HighlightTags.prototype.getHighlightTags = function(){
	var self = Annotator._instances[0].plugins.HighlightTags;

    if (typeof self.options.tag != 'undefined') {
        var final = {};
        var prelim = self.options.tag.split(",");
        prelim.forEach(function(item){
            var temp = item.split(":");
            final[temp[0]] = self.getRGB(temp[1]);
        });
        return final;
    }
    return {};
};

Annotator.Plugin.HighlightTags.prototype.getRGB = function(item){
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
	            if( stdCol[color]!=undefined )
	                values = getColorValues(stdCol[color]);
	        }
	    }
	    return values;
	}
    return getColorValues(item);
};

Annotator.Plugin.HighlightTags.prototype.colorize = function() {
	var self = Annotator._instances[0].plugins.HighlightTags;
	var annotations = Array.prototype.slice.call($(".annotator-hl"));
	for (annNum = 0; annNum < annotations.length; ++annNum) {
	    var anns = $.data(annotations[annNum],"annotation");
	    if (typeof anns.tags !== "undefined" && anns.tags.length == 0) {
	        
	        // image annotations should not change the background of the highlight
	        // only the border so as not to block the image behind it.
	        if (anns.media !== "image") {
	            $(annotations[annNum]).css("background-color", "");
	        } else {
	            $(annotations[annNum]).css("border", "2px solid rgb(255, 255, 255)");
	            $(annotations[annNum]).css("outline", "2px solid rgb(0, 0, 0)");
	        }
	    }

	    if (typeof anns.tags !== "undefined" && self.colors !== {}) {
	        
	        for (var index = 0; index < anns.tags.length; ++index) {
	            if (anns.tags[index].indexOf("flagged-") == -1) {
	                if (typeof self.colors[anns.tags[index]] !== "undefined") {
	                    var finalcolor = self.colors[anns.tags[index]];
	                    // if it's a text change the background
	                    if (anns.media !== "image") {
	                        $(annotations[annNum]).css(
	                            "background", 
	                            // last value, 0.3 is the standard highlight opacity for annotator
	                            "rgba(" + finalcolor.red + ", " + finalcolor.green + ", " + finalcolor.blue + ", 0.3)"
	                        );
	                    } 
	                    // if it's an image change the dark border/outline leave the white one as is
	                    else {
	                        $(annotations[annNum]).css(
	                            "outline",
	                            "2px solid rgb(" + finalcolor.red + ", " + finalcolor.green + ", " + finalcolor.blue + ")"
	                        );
	                    }
	                } else {
	                    // if the last tag was not predetermined by instrutor background should go back to default
	                    if (anns.media !== "image") {
	                        $(annotations[annNum]).css(
	                            "background", 
	                            // returns the value to the inherited value without the above
	                            ""
	                        );
	                    }
	                }
	            }
	        }
	        
	    } else {
	        // if there are no tags or predefined colors, keep the background at default
	        if (anns.media !== "image") {
	           $(annotations[annNum]).css("background","");
	        }
	    }
	}
	self.annotator.publish('colorizeCompleted');
};

// this function adds the appropriate color to the tag divs for each annotation
Annotator.Plugin.HighlightTags.prototype.colorizeEditorTags = function() {
    var self = Annotator._instances[0].plugins.HighlightTags;;
    $.each($('.annotator-editor .token-input-token'), function(key, tagdiv) {
        // default colors are black for text and the original powder blue (already default)
        var rgbColor = "";
        var textColor = "color:#000;";
        var par = $(tagdiv).find("p");

        // if the tag has a predetermined color attached to it, 
        // then it changes the background and turns text white
        if (typeof self.colors[par.html()] !== "undefined") {
            var finalcolor = self.colors[par.html()];
            rgbColor = "background-color:rgba(" + finalcolor.red + ", " + finalcolor.green + ", " + finalcolor.blue + ", 0.5);";
            textColor = "color:#fff;";
        }

        // note that to change the text color you must change it in the paragraph tag, not the div
        $(tagdiv).attr('style', rgbColor);
        par.attr('style', textColor);
    });    
};

Annotator.Plugin.HighlightTags.prototype.updateField = function(field, annotation) {
	var self = Annotator._instances[0].plugins.HighlightTags;

    $('#tag-input').tokenInput('clear');
    $('#token-input-tag-input').attr('placeholder', 'Add tags...');

    // loops through the tags already in the annotation and "add" them to this annotation
    if (typeof annotation.tags !== "undefined") {
        for (tagnum = 0; tagnum < annotation.tags.length; tagnum++) {
            var n = annotation.tags[tagnum];
            if (typeof self.annotator.plugins["HighlightTags"] !== 'undefined') {
                // if there are flags, we must ignore them
                if (annotation.tags[tagnum].indexOf("flagged-") === -1 && annotation.tags[tagnum] !== "") {
                    $('#tag-input').tokenInput('add',{'id':n,'name':n});
                }
            } else {
                $('#tag-input').tokenInput('add', {'id': n, 'name': n});
            }
        }
    }
    self.colorizeEditorTags();
};

Annotator.Plugin.HighlightTags.prototype.updateViewer = function(field, annotation) {
	var self = Annotator._instances[0].plugins.HighlightTags;
	if (typeof annotation.tags !== "undefined") {
		if (annotation.tags.length === 0 || annotation.tags[0] === "") {
			$(field).remove();
			return;
		}

		// otherwise we prepare to loop through them
        var nonFlagTags = true;
        var tokenList = "<ul class=\"token-input-list\">";

        for (tagnum = 0; tagnum < annotation.tags.length; ++tagnum){
            if (typeof self.annotator.plugins["Flagging"] !== 'undefined') {
                // once again we ingore flags
                if (annotation.tags[tagnum].indexOf("flagged-") === -1) {
                    
                    // once again, defaults are black for text and powder blue default from token function
                    var rgbColor = "";
                    var textColor = "#000";

                    // if there is a color associated with the tag, it will change the background
                    // and change the text to white
                    if (typeof self.colors[annotation.tags[tagnum]] !== "undefined") {
                        var finalcolor = self.colors[annotation.tags[tagnum]];
                        rgbColor = "style=\"background-color:rgba(" + finalcolor.red + ", " + finalcolor.green + ", " + finalcolor.blue + ", 0.5);\"";
                        textColor = "#fff";
                    }

                    // note: to change text color you need to do it in the paragrph tag not the div
                    tokenList += "<li class=\"token-input-token\"" + rgbColor + "><p style=\"color: " + textColor + ";\">"+ annotation.tags[tagnum]+"</p></span></li>";
                    nonFlagTags = false;
                }
            } else {
                tokenList += "<li class=\"token-input-token\"><p>"+ annotation.tags[tagnum]+"</p></span></li>";
                nonFlagTags = false;
            }
        }

        // close off list from above
        tokenList += "</ul>";
        $(field).append(tokenList);

        // the field for tags is removed also if all the tags ended up being flags
        if (nonFlagTags) {
        	$(field.remove());
        }
	} else {
		$(field).remove();
	}
};

// The following function is run when a person hits submit.
Annotator.Plugin.HighlightTags.prototype.pluginSubmit = function(field, annotation) {
    arr = $(field).find('input[name=tags]').val().split(',');
    console.log(arr.indexOf("") !== -1);
    console.log(arr.length === 1);
    if (arr.indexOf("") !== -1 && arr.length === 1) {
    	annotation.tags = [];
    } else {
    	annotation.tags = arr;
    }
    console.log(annotation.tags);
};

// The following will call the colorize function during an external call and then return
// an event signaling completion.
Annotator.Plugin.HighlightTags.prototype.externalCall = function() {
	var self = Annotator._instances[0].plugins.HighlightTags;
    self.colorize();
    self.annotator.publish('finishedExternalCallToHighlightTags');
};