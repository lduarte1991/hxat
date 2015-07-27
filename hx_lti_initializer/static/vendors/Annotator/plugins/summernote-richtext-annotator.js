Annotator.Plugin.SummernoteRichText = function(element, options) {
	
	// extends the Plugin class from Annotator
	Annotator.Plugin.apply(this, arguments);

	this.field = null;
	this.options = {
		height: 100,
		focus: true,
		width: 400,
	};

	return this;
};

Annotator.Plugin.SummernoteRichText.prototype = new Annotator.Plugin();

Annotator.Plugin.SummernoteRichText.prototype.pluginInit = function() {
	if (!Annotator.supported()){
		return;
	}
	var self = Annotator._instances[0].plugins.SummernoteRichText;
	self.field = self.annotator.editor.addField({
		type: 'input',
		load: self.updateEditor,
		submit: self.submitEditor,
	});

	self.viewer = self.annotator.viewer.addField({
		load: this.updateViewer,
	});

	self.annotator.subscribe("annotationEditorShown", function() {
		$('#annotator-field-0').summernote(self.options);
		self.checkOrientation();
	});

	self.annotator.subscribe("annotationEditorHidden", function() {
		$('#annotator-field-0').destroy();
		$('.fullscreen').toggleClass('fullscreen');
	});
};

Annotator.Plugin.SummernoteRichText.prototype.checkOrientation = function() {
      var current, offset, viewport, widget, window;
      this.annotator.editor.element.removeClass('annotator-invert-x').removeClass('annotator-invert-y');
      window = $(Annotator.Util.getGlobal());
      widget = this.annotator.editor.element.children(":first");
      offset = widget.offset();
      viewport = {
        top: window.scrollTop(),
        right: window.width() + window.scrollLeft()
      };
      current = {
        top: offset.top,
        right: offset.left + widget.width()
      };
      if ((current.top - viewport.top) < 0) {
        this.annotator.editor.element.addClass('annotator-invert-y');
      }
      if ((current.right - viewport.right) > 0) {
        this.annotator.editor.element.addClass('annotator-invert-x');
      }
      return this;
}

Annotator.Plugin.SummernoteRichText.prototype.updateEditor = function(field, annotation) {
	var text = typeof annotation.text != 'undefined' ? annotation.text : '';
	$('#annotator-field-0').code(text);
	$(field).remove();
};

Annotator.Plugin.SummernoteRichText.prototype.updateViewer = function(field, annotation) {
	var textDiv = $(field.parentNode).find('div:first-of-type')[0];
    textDiv.innerHTML = annotation.text;
    $(field).remove();
};

Annotator.Plugin.SummernoteRichText.prototype.submitEditor = function(field, annotation) {
	var text = $('#annotator-field-0').code();
	if (annotation.text !== text) {
        annotation.text = text;
	}
};
