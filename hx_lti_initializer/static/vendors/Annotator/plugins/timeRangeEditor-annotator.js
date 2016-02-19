Annotator.Plugin.TimeRangeEditor = function(element, options) {
	
	// extends the Plugin class from Annotator
	Annotator.Plugin.apply(this, arguments);

	this.field = null;

	return this;
};

Annotator.Plugin.TimeRangeEditor.prototype = new Annotator.Plugin();

Annotator.Plugin.TimeRangeEditor.prototype.pluginInit = function() {
	if (!Annotator.supported()){
		return;
	}
	var self = Annotator._instances[0].plugins.TimeRangeEditor;
	self.field = self.annotator.editor.addField({
		type: 'input',
		load: self.updateEditor,
	});

	jQuery(self.field).html("<div class='timeRangeEditor' style='padding-left: 10px;padding-right:10px;'>Start: <input type='number' id='start' style='min-width: 30%!important;width: 30%!important;display:inline-block!important;'></input>seconds.<button role='button' style='padding:3px;margin-left:35px;margin-bottom:-30px;width:130px' id='preview' class='btn btn-default' aria-label='Select to preview range selected.'>Preview Video</button><br>End:&nbsp;&nbsp;&nbsp;<input type='number' id='end' style='min-width: 30%!important;width: 30%!important;display:inline-block!important;'></input>seconds.</div>");

};

Annotator.Plugin.TimeRangeEditor.prototype.updateEditor = function(field, annotation) {
	var times = AController.targetObjectController.vid.rangeslider.getValues();
	var startElement = jQuery(field).find('#start');
	var endElement = jQuery(field).find('#end');
	startElement.val(Math.floor(times.start));
	endElement.val(Math.floor(times.end));
	
	startElement.on('change', function(e){
		AController.targetObjectController.vid.rangeslider.setValue(0, startElement.val());
	});

	endElement.on('change', function(e){
		AController.targetObjectController.vid.rangeslider.setValue(1, endElement.val());
	});
	var self = Annotator._instances[0]
	console.log(self.editor);
	jQuery('#preview').click(function(e) {
		e.preventDefault();
		AController.targetObjectController.vid.player().playBetween(startElement.val(), endElement.val());
		
		if (jQuery('#transcript').is(":hidden")){
			var translate_editor = (jQuery(window).height() - (jQuery('#viewer').height() + 50)) * -1;
        	AController.annotationCore.annotation_tool.editor.element.css('transform', 'translateY('+translate_editor+'px)');
        	jQuery("#transcript").show();
	        jQuery('#viewer').css('height', '80%');
		}
		
	});

};
