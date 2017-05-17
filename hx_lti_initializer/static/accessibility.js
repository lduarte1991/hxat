//accessibility.js

(function($) {
	$.Accessibility = function(options) {
		this.initOptions = options;
		this.init();
		return this;
	};

	$.Accessibility.prototype.init = function() {
		var self = this;
		jQuery.each(this.initOptions['triggerClicks'], function(index, value) {
			self.keyPressOn('body', value, {
				'13': function(){
					jQuery(event.target).trigger('click');
				}, 
				'32': function() {
					jQuery(event.target).trigger('click');
				}
			})
		})
	};

	// if you need something that works in the document/window without a specific element
	$.Accessibility.prototype.globalKeyPress = function(codesAndFuncs) {
		var self = this;
		jQuery(document).ready(function() {
			jQuery(this).on('keypress', function(event) {
				var key = event.keyCode ? event.keyCode : event.which;
				jQuery.each(codesAndFuncs, function(keyCode, value) {
					if (key == self.keyCodeValue(keyCode)) {
						value();
					}
				});
				return false;
			});
		});
	};

	// if you need a listener when focused on a specific element
	$.Accessibility.prototype.keyPressOn = function(parent, child, codesAndFuncs) {
		var self = this;
		jQuery(parent).on('keypress', child, function(event) {
			var key = event.keyCode ? event.keyCode : event.which;
			jQuery.each(codesAndFuncs, function(keyCode, value) {
				if (key == self.keyCodeValue(keyCode)) {
					value();
				}
			});
			return false;
		});
	};

	// translates keyCodeValue ... will add more as more are needed
	$.Accessibility.prototype.keyCodeValue = function(keyCode) {
		switch(keyCode.toUpperCase()) {
			case 'SPACE':
			case 'SPACEBAR':
			case 'SPACE BAR':
				return 32;
				break;
			case 'ENTER':
			case 'ENT':
				return 13;
				break;
			default:
				return parseInt(keyCode, 10);
		}
	};

}(AController))