/***
 * AnnotatorCore.js
 *
 * This file will contain the functions needed to access and use
 * whatever library is currently the norm for annotations.
 * As of Spring 2015, the norm is to use annotator.js
 * This is the page that should change if/when that tool changes.
 ***/

(function($) {
	$.AnnotationCore = function(options, commonInfo) {
		// HTMLElement that contains what should be annotated
		this.element = options.annotationElement;

		// contains any other options needed to initialize the tool
		this.initOptions = jQuery.extend({}, options.initOptions, commonInfo);

		// initializes tool
		this.init(this.initOptions.mediaType);

		return this;
	};

	/* init
	 * The following function initializes the annotation core library
	 * it should change depending on what the library we are using is.
	 * Currently we are using annotator.js and thus the following
	 * initializes and depends on those libraries being present.
	 */
	$.AnnotationCore.prototype.init = function(mediaType){
		// use this space to mold initOptions into whatever shape you need it to be
		annotatorOptions = this.initOptions;
		
		// sets up the store for the common settings for the tool, specifically Annotation Database
		this.setUpCommonAttributes();

		this.annotation_tool = jQuery(this.element).annotator(annotatorOptions).data('annotator');
		this.setUpPlugins();

		if(mediaType == "image") {
			//- OpenSeaDragon
		    this.viewer = OpenSeadragon(annotatorOptions.optionsOpenSeadragon);
		    console.log(this.viewer);
		    //- OpenSeaDragon Plugins
		    this.viewer.annotation(annotatorOptions.optionsOSDA);
		    
		    // Set annotator.editor.OpenSeaDragon by default
		    this.annotation_tool.editor.OpenSeaDragon=-1;

		    this.annotation_tool.osda = this;

			function reloadEditor(){
		        tinymce.EditorManager.execCommand('mceRemoveEditor',true, "annotator-field-0");
		        tinymce.EditorManager.execCommand('mceAddEditor',true, "annotator-field-0");
		        
		        // if person hits into/out of fullscreen before closing the editor should close itself
		        // ideally we would want to keep it open and reposition, this would make a great TODO in the future
		        Annotator._instances[0].editor.hide();
		    }

		    var self = this;
		    document.addEventListener("fullscreenchange", function () {
		        reloadEditor();
		    }, false);
		 
		    document.addEventListener("mozfullscreenchange", function () {
		        reloadEditor();
		    }, false);
		 
		    document.addEventListener("webkitfullscreenchange", function () {
		        reloadEditor();
		    }, false);
		 
		    document.addEventListener("msfullscreenchange", function () {
		        reloadEditor();
		    }, false);

		    // for some reason the above doesn't work when person hits ESC to exit full screen...
		    jQuery(document).keyup(function(e) {
		        // esc key reloads editor as well
		        if (e.keyCode == 27) { 
		            reloadEditor();
		        }   
		    });
		} else if (mediaType == "video") {
			// Video-JS
		    /*    
		        mplayers -> Array with the html of all the video-js
		        mplayer -> Array with all the video-js that will be in the plugin
		    */
		    var mplayers = this.element.find('div .video-js').toArray();
		    var mplayer = this.mplayer = {};
		    for (var index in mplayers) {
		        var id = mplayers[index].id;
		        var mplayer_ = videojs(mplayers[index], annotatorOptions.optionsVideoJS);
		        // solve a problem with firefox. In Firefox the src() function is loaded before charge the optionsVideoJS, and the techOrder are not loaded
		        if (vjs.IS_FIREFOX && typeof annotatorOptions.optionsVideoJS.techOrder !== 'undefined'){
		            mplayer_.options_.techOrder = annotatorOptions.optionsVideoJS.techOrder;
		            mplayer_.src(mplayer_.options_['sources']);
		        }
		        this.mplayer[id] = mplayer_;
		    }
		    
		    
		    // Video-JS
		    this.annotation_tool.an = {}; // annotations video-js plugin to annotator
		    for (var index in this.mplayer) {
		        // to be their own options is necessary to extend deeply the options with all the childrens
		        this.mplayer[index].rangeslider(jQuery.extend(true, {}, annotatorOptions.optionsRS));
		        this.mplayer[index].annotations(jQuery.extend(true, {}, annotatorOptions.optionsOVA));
		        this.annotation_tool.an[index]=this.mplayer[index].annotations;
		    }

		    // Local function to setup the keyboard listener
		    var focusedPlayer = this.focusedPlayer = ''; // variable to know the focused player
		    var lastfocusPlayer = this.lastfocusPlayer = ''; 
		    
		    function onKeyUp(e) {
		        // skip the text areas
		        if (e.target.nodeName.toLowerCase() !== 'textarea')
		            mplayer[focusedPlayer].annotations.pressedKey(e.which);
		    };
		    
		    (this._setupKeyboard = function() {
		        jQuery(document).mousedown(function(e) {
		            focusedPlayer = '';
		            
		            // Detects if a player was click
		            for (var index in mplayer) {
		                if (jQuery(mplayer[index].el_).find(e.target).length)
		                    focusedPlayer = mplayer[index].id_;
		            }
		            
		            // Enter if we change the focus between player or go out of the player
		            if (lastfocusPlayer !== focusedPlayer) {
		                jQuery(document).off("keyup", onKeyUp); // Remove the last listener
		                // set the key listener
		                if (focusedPlayer !== '')
		                    jQuery(document).on("keyup", onKeyUp);
		            }
		            
		            lastfocusPlayer = focusedPlayer;
		        });
		        
		    }) (this);
		    this.annotation_tool.mplayer = this.mplayer;
    		this.annotation_tool.editor.VideoJS = -1;
		}
	};

	/* setUpCommonAttributes
	 * Init some plugins or options that are common between text, video, and image.
	 */
	$.AnnotationCore.prototype.setUpCommonAttributes = function(){
		annotatorOptions = this.initOptions

		// checks to make sure whether the store attribute exists
		if (typeof annotatorOptions.store === "undefined"){
			annotatorOptions.store = {};
		}

		// as with above, the store needs to be set up a specific way
		var store = annotatorOptions.store;
	    if (typeof store.annotationData === 'undefined'){
	        store.annotationData = {};
	    }

	    // new mechanic, the following three options contains all the information you would
	    // need to know to determine where the annotation belongs, object_id is the id of the
	    // target source, it can exist in multiple assignments and multiple courses. context_id
	    // refers to the course it belongs to and collection_id is the assignment the object belongs to
	    if (typeof store.annotationData.uri === 'undefined'){
	    	//once CATCH can handle context_id and collection_id, we can store just the object_id as the URI
	        //store.annotationData.uri = annotatorOptions.object_id;
	        var tempUri = "" + annotatorOptions.object_id + ":" + annotatorOptions.context_id + ":" + annotatorOptions.collection_id;

	    }
	    if (typeof store.annotationData.context_id === 'undefined'){
	        store.annotationData.context_id = annotatorOptions.context_id;
	    }
	    if (typeof store.annotationData.collection_id === 'undefined'){
	        store.annotationData.collection_id = annotatorOptions.collection_id;
	    }

	    // the following are options for the first retrieval of information from the Annotation Database
	    if (typeof store.loadFromSearch === 'undefined'){
	        store.loadFromSearch = {};
	    }
	    if (typeof store.loadFromSearch.uri === 'undefined'){
	        store.loadFromSearch.uri = store.annotationData.uri;
	    }
	    if (typeof store.loadFromSearch.limit === 'undefined'){
	        store.loadFromSearch.limit = 10000;
	    }
	};

	$.AnnotationCore.prototype.setUpPlugins = function() {
	    for (plugin in this.initOptions.plugins){
	    	pluginName = this.initOptions.plugins[plugin];
	    	options = {};
	    	if (pluginName === "Store") {
	    		var tempUri = "" + this.initOptions.object_id + "_" + this.initOptions.context_id + "_" + this.initOptions.collection_id;
		    	options = {
		    		// The endpoint of the store on your server.
	                prefix: "http://54.148.223.225:8080/catch/annotator",
	                annotationData: {
	                    uri: tempUri,
	                    citation: "fake source",
	                    media: this.initOptions.mediaType,
	                },
	                urls: {
	                    // These are the default URLs.
	                    create:  '/create',
	                    read:    '/read/:id',
	                    update:  '/update/:id',
	                    destroy: '/delete/:id',
	                    search:  '/search'
	                },
	                loadFromSearch:{
	                    uri: tempUri,
	                    media: this.initOptions.mediaType,
	                }
		    	};
		    	
		    } else if (pluginName === 'Auth') {
		    	options = {
		    		token: this.initOptions.token,
		    	};
		    } else if (pluginName === 'Permissions') {
		    	options = {
	                user: {
	                    id: this.initOptions.user_id,
	                    name: this.initOptions.username,
	                },
	                permissions: {
	                        'read':   [],
	                        'update': [this.initOptions.user_id,],
	                        'delete': [this.initOptions.user_id,],
	                        'admin':  [this.initOptions.user_id,]
	                },
	                showViewPermissionsCheckbox: false,
	                showEditPermissionsCheckbox: false,
	                userString: function (user) {
	                    if (user && user.name)
	                        return user.name;
	                    return user;
	                },
	                userId: function (user) {
	                    if (user && user.id)
	                        return user.id;
	                    return user;
	                },
	                userAuthorize: function(action, annotation, user) {
	                    var token, tokens, _i, _len;
	                    if (annotation.permissions) {
	                      tokens = annotation.permissions[action] || [];
	                      if (tokens.length === 0) {
	                        return true;
	                      }
	                      for (item in tokens) {
	                        token = tokens[item];
	                        if (this.userId(user) === token) {
	                          return true;
	                        }
	                      }
	                      return false;
	                    } else if (annotation.user) {
	                      if (user) {
	                        return this.userId(user) === this.userId(annotation.user);
	                      } else {
	                        return false;
	                      }
	                    }
	                    return true;
	                  },
			    } 
			} else if(pluginName === "RichText") {
		    	options = {
		    		tinymce:{
		                selector: "li.annotator-item textarea",
		                plugins: "media image codemirror",
		                menubar: false,
		                toolbar_items_size: 'small',
		                extended_valid_elements : "iframe[src|frameborder|style|scrolling|class|width|height|name|align|id]",
		                toolbar: "insertfile undo redo | styleselect | bold italic | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent | image rubric | code ",
        				auto_focus: "annotator-field-0",
        			}
        		}
		    } else if (pluginName === "HighlightTags") {
		    	options = {
		            tag: "test1:red,test2:blue",
		    	}
		    } else if (pluginName === "Grouping") {
		    	options = {
		    		optionsOVA: {
			    		posBigNew: 'none', 
			    		default_tab: 'Public',
			    		annotation_tool: this.annotation_tool,
			    	}
		    	}
		    } else if (pluginName === "Touch") {
		    	options = {
		    		force: false,
		    	}
		    }
		    this.annotation_tool.addPlugin(pluginName, options);
	    }
	};

	$.AnnotationCore.prototype.getAnnotationTool = function() {
		return this.annotation_tool;
	};

}(AController));
