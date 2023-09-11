/*
 * Assignment Form Editor
 *
 */

function AssignmentEditor() {
    this.templateList = [
        'add_tag_template',
        'add_source_row',
        'add_form_row',
        'popup_window',
    ]
    this.static_url = "/static/templates";
    this.source_list = jQuery('.source-materials');
    this.main_page = jQuery('.main-page');
    this.annotation_settings_page = jQuery('.annotation-settings-page');
    this.database_settings_page = jQuery('.database-settings-page');
    this.TEMPLATES = {};
    this.totalForms = jQuery('.source-item');
    
    this.init();
}

AssignmentEditor.setupWysiwyg = function(selector, options) {
    var $textarea = $(selector);
    options = jQuery.extend({
       focus: false,
       onChange: function(contents, $editable) {
           $textarea.val( contents );
           $textarea.change();
       }
    }, options || {});

    $textarea.summernote(options);
};

AssignmentEditor.prototype = {
    constructor: AssignmentEditor,
    init: function() {
        this.load_templates();
        this.set_up_page_changing();
        this.set_up_source_expanding();
        this.set_up_global_buttons();
        this.set_up_tagging_functionality();
        this.set_up_ordering_functionality();
    },
    load_templates: function(){

        // goes through ALL the templates in the list
        var self = this;
        jQuery.each(this.templateList, function(index, value) {
            self.load_template(value);
        });
    },
    load_template: function(template_name) {

        // allows you to set up a template given the name
        // all should exist in a static/templates folder
        var self = this;
        var options = {
            url: this.static_url + "/" + template_name + ".html",
            success: function(data) {
                self.TEMPLATES[template_name] = _.template(data);
            },
            async: true,
        };
        jQuery.ajax(options);
    },
    set_up_page_changing: function() {
        var self = this;
        // allows you to go back and forth between the annotation settings
        // and the main page without saving
        jQuery('#annotation-settings-button').click(function(event) {
            self.main_page.hide();
            self.annotation_settings_page.show();
        });
        jQuery('#annotation-settings-cancel-button').click(function(event) {
            self.main_page.show();
            self.annotation_settings_page.hide();
        });

        // allows you to go back and forth between the database settings
        // and the main page without saving.
        jQuery('#database-settings-button').click(function(event) {
            self.main_page.hide();
            self.database_settings_page.show();
        });
        jQuery('#database-settings-cancel-button').click(function(event) {
            self.main_page.show();
            self.database_settings_page.hide();
        });
    },
    set_up_source_expanding: function() {
        var self = this;
        // toggles source tailed view from clicking on the row with the name
        var expand_from_first_row = function(event) {
            event.preventDefault ? event.preventDefault() : (event.returnValue = false);
            var source_item = jQuery(this.parentElement);
            var source_item_arrow = source_item.find('.fa-lg');
            var to_list = source_item.find('.source-detail');

            if (source_item.hasClass('open')) {
                source_item_arrow.addClass('fa-caret-right');
                source_item_arrow.removeClass('fa-caret-down');
                to_list.hide();
                source_item.removeClass('open');
            } else {
                source_item_arrow.addClass('fa-caret-down');
                source_item_arrow.removeClass('fa-caret-right');
                to_list.show();
                source_item.addClass('open');
            }
        };

        this.source_list.on('click', '.source-item .first-row', expand_from_first_row);
        this.keyPressOn('.source-materials', '.source-item .first-row', {
            'SPACE': expand_from_first_row,
            'ENTER': expand_from_first_row
        });

        // toggles the advanced settings of each source
        this.source_list.on("click", '.show-settings', function(event) {
            event.preventDefault ? event.preventDefault() : (event.returnValue = false);
            var settings_link = jQuery(this);
            var source_item = settings_link.closest('.source-item'); 
            var advanced_list = source_item.find('.advanced-settings');

            if (source_item.hasClass('open') && settings_link.hasClass('open')) {
                settings_link.html(settings_link.html().replace('Hide', 'Show'));
                settings_link.removeClass('open');
                advanced_list.hide();
            } else if (source_item.hasClass('open')){
                settings_link.html(settings_link.html().replace('Show', 'Hide'));
                settings_link.addClass('open');
                advanced_list.show();
            }
        });

        // sets up remove button to delete row in list
        this.source_list.on('click', '.remove', function(event){
            var $this = jQuery(this);
            var source_item = $this.closest('.source-item');
            var object_pk = source_item.attr('data-id');
            var object_title = source_item.find('.source-title').html();
            var assignment_title = jQuery('#assignment-name-input').val();
            var url = "/lti_init/launch_lti/targetobject/" + object_pk + "/delete/";

            var context = {
                "popup_title": 'Delete this assignment',
                "popup_content": '<p>Are you sure you want to remove the annotation source: <em>&quot;'+ object_title +'&quot;</em> from the assignment: <em>&quot;' + assignment_title + '&quot</em></p><p>This action will only remove the source object from this individual assignment, and will not affect any other assignments or courses where it is used.</p>',
                "popup_confirm": '<div id="delete-popup-confirm" type="submit" role="button">Remove source</div>',
            };
            
            jQuery('body').append(self.TEMPLATES['popup_window'](context));

            jQuery('#delete-popup-confirm').click(function() {
                var source_id = source_item.data('id');
                console.log('input[value="'+source_id+'"]');
                console.log(jQuery('input[data-id='+source_id+']').prop('checked', true));
                console.log(source_id);
                source_item.remove();
                jQuery('.delete-popup-overlay').remove();
            });
        });
    },
    set_up_global_buttons: function() {
        var body = jQuery('body');
        var self = this;

        body.on('click', '#delete-popup-cancel', function() {
            jQuery('.delete-popup-overlay').remove();
        });

        setTimeout(function(){
            if (window.navigator.platform === "Win32") {
                jQuery('.bootstrap-select.form-control').addClass('win');
            }
            if (window.navigator.userAgent.toLowerCase().indexOf('firefox') > -1) {
                jQuery('.bootstrap-select.form-control').addClass('firefox');
            }
        }, 500);

        body.click(function() {
            if (jQuery('.color-selection.open').length > 0) {
                jQuery('.color-selection.open .custom-tag-color-menu').hide();
                jQuery('.color-selection.open').removeClass('open');
            }
        });
        jQuery('#id_assignmenttargets_set-TOTAL_FORMS').attr('value', jQuery('.source-item').length);
        jQuery('.visible-tabs-collection input').change(function() {
            var inst_tab = jQuery('#instructor-tab-visible').prop('checked');
            var student_tab = jQuery('#student-tab-visible').prop('checked');
            var public_tab = jQuery('#public-tab-visible').prop('checked');

            if (inst_tab) {
                if (student_tab) {
                    if (public_tab) {
                        jQuery('#visible-tabs-explanation').html("<p>Second-most used option. Allow students to discuss with instructor guidance. <br>Example use case: Allow students to view each other's annotations, filter their own annotations, and view their instructor's annotations.</p>");
                    } else {
                        jQuery('#visible-tabs-explanation').html("<p>Option to guide users through assignment.<br>Example use case: Allows users to make their own annotations and view instructor annotations but they will not be able to see other users' annotations.</p>");
                    }
                } else {
                    if (public_tab) {
                        jQuery('#visible-tabs-explanation').html("<p style='color: red;'>Not recommended for regular use. Read Only.<br>Example use case: This would allow users to view instructor and students' annotations but not be able to filter their own. Probably helpful when opening up an old version of a course/tool.</p>");
                    } else {
                        jQuery('#visible-tabs-explanation').html("<p>Instructor only.<br>Example use case: Instructors have something they would like to guide learners through without them adding their own annotations.</p>");
                    }
                }
            } else {
                if (student_tab) {
                    if (public_tab) {
                        jQuery('#visible-tabs-explanation').html("<p>This is the default option: annotations without instructor guidance.<br>Example use case: Allow students to view each other's annotations and filter their own without the instructor adding their own annotations to guide them through the source.</p>");
                    } else {
                        jQuery('#visible-tabs-explanation').html("<p>Private Notes. <br>Example use case: Allow users to make their own annotations on a source for personal reasons without instructor guidence or having other people view their own.</p>");
                    }
                } else {
                    if (public_tab) {
                        jQuery('#visible-tabs-explanation').html("<p style='color: red;'>Not recommended for regular use. <br>Example use case: Since this shuts off 'My Notes', students will not be able to make annotations but only view a collection of learner annotations. They will not be able to filter and see only instructor annotations.</p>");
                    } else {
                        jQuery('#visible-tabs-explanation').html("<p>Zen mode. <br>Example use case: Usually only helpful for images since it basically turns on Mirador without an annotation mode, but may extended to the other media types. Turns off all annotations and leaves just the source materials.</p>");
                    }
                }
            }
            jQuery('#visible-tabs-explanation').prepend('<p><strong>Note:</strong> These checkboxes will be the default for all instances of this assignment. Custom parameters can overwrite these options.</p>')
        });

        this.source_list.on('click', '#add-source-button', function(event){
            var $this = jQuery(this);        
            var html='<div class="delete-popup-overlay"><div class="add-source-popup-background"><h3>Add Source to Assignment</h3>\
            <select class="hx-textfield form-control popup" id="assignment_object_choices">\
            '+ jQuery('.object_options').html() +'\
            </select>\
            <label for="assignment-css">Assignment CSS:</label>\
            <input class="hx-textfield form-control popup" id="assignment-css" type="text">\
            <div class="other_options"></div>\
            <div style="display:none;"><input type="checkbox" id="hide_dash"><label for="hide_dash">Hide dashboard on load</label></div>\
            <div id="add-source-popup-confirm" class="popup" type="submit" role="button">Add Source</div><div id="delete-popup-cancel">Cancel</div></form></div></div>';

            jQuery('body').append(html);
            jQuery('#assignment_object_choices').selectpicker({
                liveSearch: true,
            });
            setTimeout(function(){
                if (window.navigator.platform === "Win32") {
                    jQuery('.bootstrap-select.form-control').addClass('win');
                }
                if (window.navigator.userAgent.toLowerCase().indexOf('firefox') > -1) {
                    jQuery('.bootstrap-select.form-control').addClass('firefox');
                }
            }, 500);
            jQuery('#assignment_object_choices').change(function(event) {
                var media = jQuery(this).find('option:selected').data('type');
                if (media == "ig" && jQuery('#viewtype').length == 0) {
                    jQuery('.other_options').append('<label for="viewtype">View type:</label>\
                        <select class="hx-textfield form-control popup" id="viewtype">\
                            <option value="ImageView" selected>Single Image View</option>\
                            <option value="ThumbnailsView">Thumbnails View</option>\
                            <option value="ScrollView">Scroll View</option>\
                            <option value="BookView">Book View</option>\
                        </select>\
                        <label for="assignment-open-to-page">Open to page (Canvas ID):</label>\
                        <input class="hx-textfield form-control popup" id="assignment-open-to-page" type="text">');
                    jQuery('#viewtype').selectpicker();
                } else if (media !== "ig") {
                    jQuery('.other_options').html('');
                }
            });

            jQuery('#assignment_object_choices').trigger('change');
            
            jQuery('#delete-popup-cancel').click(function() {
                jQuery('.delete-popup-overlay').remove();
            });
            jQuery('#add-source-popup-confirm').click(function() {
                var title = jQuery('.add-source-popup-background .dropdown-toggle[data-id^="assignment_object_choices"]').text();
                var id_selected = jQuery('.add-source-popup-background #assignment_object_choices').val();
                var option_selected = jQuery('.add-source-popup-background option[value="'+id_selected+'"]');
                self.add_source_row({
                    "id": id_selected,
                    "target_title": title,
                    "target_author": option_selected.data('author'),
                    "target_created": option_selected.data('date'),
                    "target_type": option_selected.data('type')
                });
                jQuery('.delete-popup-overlay').remove();
            });
        });

        jQuery('.bootstrap-select').on('click', function(e) {
            console.log(jQuery(this).find('button'));
            jQuery(this).find('button').dropdown('toggle');
        });

    },
    set_up_tagging_functionality: function() {
        var self = this;
        var tag_list_holder = jQuery('.tag-list-holder');
        jQuery('#enable-tags').change(function(event) {
            if (jQuery(this).prop('checked')) {
                if (jQuery('.tag-list-holder .trow').length == 1) {
                    jQuery('#add-tags-button').show();
                } else {
                    jQuery('.tag-list-holder').show();
                }
            } else {
                jQuery('#add-tags-button').hide();
                jQuery('.tag-list-holder').hide();
            }
        });

        jQuery('#add-tags-button').click(function(event) {
            jQuery(this).hide();
            tag_list_holder.show();
            self.add_tag();
        });

        tag_list_holder.on('click', '.remove-tag', function(event) {
            event.preventDefault ? event.preventDefault() : (event.returnValue = false);
            jQuery(this).closest('.trow').remove();
            if (jQuery('.tag-list-holder .trow').length == 1) {
                tag_list_holder.hide();
                jQuery('#add-tags-button').show();
            }
        });

        tag_list_holder.on('click', '.add-another-tag', self.add_tag);

        tag_list_holder.on('click', '.color-selection .custom-tag-color-chosen', function(event) {
            event.preventDefault ? event.preventDefault() : (event.returnValue = false);
            event.stopPropagation();

            var resultcolor = jQuery(this);
            var toggle = resultcolor.parent();

            if (toggle.hasClass('open')) {
                toggle.removeClass('open');
                toggle.find('.custom-tag-color-menu').hide();
            } else {
                toggle.addClass('open');
                toggle.find('.custom-tag-color-menu').show();
            }
        });

        tag_list_holder.on('click', '.color-selection', function(event) {
            event.stopPropagation();
        });

        tag_list_holder.on('click', '.dropdown-inner li', function(event) {
            event.stopPropagation();
            var choice = jQuery(this);

            var chosenColor = choice.find('.custom-tag-color').css('background-color');
            var selector = choice.closest('.color-selection');

            if (choice.text().trim() === "Custom") {
                choice.html('<div class="custom-tag-color" role="button" style="background-color:rgba(255, 255, 255, 0.3);"></div><input type="text" id="custom-color">');
            } else if(choice.text().trim() !== "") {
                selector.find('.custom-tag-color-chosen').first().css('background-color', chosenColor);
                selector.find('.custom-tag-color-menu').hide();
                selector.removeClass('open');
            }
        });

        jQuery('.tag-list-holder').on('keyup', '#custom-color', function(event) {
            if (event.keyCode == 13) {
                var chosenColor = jQuery(event.currentTarget).parent().find('.custom-tag-color').css('background-color');
                var selector = jQuery(event.currentTarget).closest('.color-selection');
                selector.find('.custom-tag-color-chosen').first().css('background-color', chosenColor);
                selector.find('.custom-tag-color-menu').hide();
                selector.removeClass('open');
            }
            var input = event.currentTarget.value;
            var result = self.getColorValues(input);
            var color = "rgba(" + result.red + ',' + result.green + ',' + result.blue + ',' + result.alpha + ')'; 
            jQuery(event.currentTarget).parent().find('.custom-tag-color').css('background-color', color);

        });
    },
    add_tag: function(event) {
        var self = window.assignment_editor;
        console.log(self);
        if (event) {
            event.preventDefault ? event.preventDefault() : (event.returnValue = false);
        }
        
        var count = jQuery('.tag-list-holder .trow').length;
        jQuery('.tag-list-holder').append(self.TEMPLATES['add_tag_template']({"count": count}));
    },
    add_source_row: function(context) {
        var $materials = jQuery('.source-materials');
        var $totalForms = jQuery('#id_assignmenttargets_set-TOTAL_FORMS');
        var $reorderButton = jQuery('#reorder-list-button');
        var count = parseInt($totalForms.attr('value'), 10);
        var is_ordering = $reorderButton.text() === "Invert order";
        var aTarget = 100000+count;
        var html = '';
        var form_context = {};
        
        context.count = count;
        context.order_value = count + 1;
        context.aTarget = aTarget;
        context.should_show_order = is_ordering;
        html = this.TEMPLATES.add_source_row(context);

        if ($materials.find('.source-item').length > 0) {
            $materials.find('.source-item:last').after(html);
        } else {
            $materials.find('.add-source-collection').before(html);
        }

        $totalForms.attr('value', count + 1);
        if(!$reorderButton.is(':visible')) {
            $reorderButton.show();
        }
        
        if (jQuery('.object_options option[value='+context.id+']').length === 0) {
            jQuery('.object_options').append('<option value="'+context.id+'" data-type="'+context.target_type+'" data-author="'+context.target_author+'" data-date="'+String(new Date())+'">'+context.target_title.replace(/&"'<>/, '')+'</option>');
        }
        
        form_context = jQuery.extend({}, context);
        form_context.choices = jQuery('.object_options').clone();
        form_context.choices.find('option[value='+context.id+']').attr('selected', 'selected');
        form_context.choices = form_context.choices.html();

        if (jQuery('#id_assignmenttargets_set-' + count + '-order').length === 0) {
            jQuery('form').append(this.TEMPLATES.add_form_row(form_context));
        } else if(jQuery('#id_assignmenttargets_set-' + count + '-id').length === 0) {
            jQuery('#id_assignmenttargets_set-' + count + '-order').after('<input class="hidden" id="id_assignmenttargets_set-'+count+'-id" name="assignmenttargets_set-'+count+'-id" value='+aTarget+'>');
        }

        jQuery('#mirador-view-type-' + count).selectpicker();
        jQuery('#mirador-view-type-' + count).selectpicker('val', jQuery('#viewtype').val());
        jQuery('#assignment-css-' + count).val(jQuery('#assignment-css').val());
        jQuery('#canvas-id-' + count).val(jQuery('#assignment-open-to-page').val());
        jQuery('#dashboard_hidden-' + count).prop("checked", jQuery("#hide_dash").prop("checked"));

        AssignmentEditor.setupWysiwyg('#instructions-'+count);
    },
    getColorValues: function(color) {
        var values = { red:null, green:null, blue:null, alpha:null };
        if( typeof color == 'string' ){
            /* hex */
            if( color.indexOf('#') === 0 ){
                color = color.substr(1)
                if( color.length == 3 ){
                    values = {
                        red:   parseInt( color[0]+color[0], 16 ),
                        green: parseInt( color[1]+color[1], 16 ),
                        blue:  parseInt( color[2]+color[2], 16 ),
                        alpha: .3
                    }
                }
                else if (color.length == 6) {
                    values = {
                        red:   parseInt( color.substr(0,2), 16 ),
                        green: parseInt( color.substr(2,2), 16 ),
                        blue:  parseInt( color.substr(4,2), 16 ),
                        alpha: .3
                    }
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
    },
    set_up_ordering_functionality: function() {
        var self = this;

        this.source_list.on('click', '.ordernum', function(event) {
            event.stopPropagation();
        });

        this.source_list.on('click', '#reorder-list-button', function(event) {
            var $this = jQuery(this);
            if ($this.html() === "Reorder list") {
                jQuery('.ordernum').show();
                jQuery(this).html("Invert order");
            } else {
                var before1 = jQuery('.source-materials h4').get();
                var before2 = jQuery('.source-materials #reorder-list-button').get();
                var list = jQuery('.source-item').get().reverse();
                var after = jQuery('.source-materials .add-source-collection').get();

                self.source_list.empty();
                self.source_list.append(before1, before2);
                jQuery.each(list, function(index, value) {
                    self.source_list.append(value);
                });
                self.source_list.append(after);
            }
            self.reorderList();
        });

        this.source_list.on('change', '.ordernum', function(event) {
            jQuery(this).parent().find('.order-change-button:not(:visible)').show();
        });

        this.source_list.on('click', '.order-change-button', function(event) {
            event.stopPropagation();
            event.preventDefault ? event.preventDefault() : (event.returnValue = false);
            var $this = jQuery(this);
            var new_order = $this.parent().find('.ordernum').val();
            var source_involved = $this.closest('.source-item');
            if (new_order <= 1) {
                //user wants to put it first
                source_involved.detach();
                source_involved.insertBefore('.source-item:first');


            } else if(new_order >= jQuery('.source-item').length) {
                //user wants to put it last
                source_involved.detach();
                source_involved.insertAfter('.source-item:last');

            } else {
                //add before whatever number they put in. 
                source_involved.detach();
                source_involved.insertBefore('.source-item:eq(' + (new_order - 1) + ')');
            }
            self.reorderList();
            $this.hide();
        });
    },
    reorderList: function() {
        var list = jQuery('.source-item');
        jQuery.each(list, function(index, value) {
            jQuery(value).attr('data-order', index+1);
            jQuery(value).find('.ordernum').val(index+1);
        });
    },
    rgb2hex: function (rgb){
        rgb = rgb.match(/^rgba?[\s+]?\([\s+]?(\d+)[\s+]?,[\s+]?(\d+)[\s+]?,[\s+]?(\d+)[\s+]?/i);
        return (rgb && rgb.length === 4) ? "#" +
          ("0" + parseInt(rgb[1],10).toString(16)).slice(-2) +
          ("0" + parseInt(rgb[2],10).toString(16)).slice(-2) +
          ("0" + parseInt(rgb[3],10).toString(16)).slice(-2) : '';
    },
    save_form: function() {
        if (!this.empty_check()) {
            return;
        }
        this.error_check();

        jQuery.each(jQuery('.source-item'), function(index, element) {
            var aTarget = jQuery(element).attr('data-aTarget');
            var mediaType = jQuery(element).attr('data-media');
            var order = jQuery(element).attr('data-order');
            var source_id = jQuery(element).attr('data-id');
            var form_id = jQuery('input[name$=-id][value='+aTarget+']').attr('id').replace('-id','-');
            
            // saves object chosen
            jQuery('#' + form_id + 'target_object').find('option[value="' + source_id + '"]').attr('selected', true);

            // saves instructions
            jQuery('#' + form_id + 'target_instructions').html(jQuery(element).find('.instructions').val());

            // saves assignment css
            jQuery('#' + form_id + 'target_external_css').attr('value', jQuery(element).find('.assignment-css').val());

            // saves whether dashboard defaults to hidden
            var dashboard_hidden = jQuery(element).find('.dashboard-hidden').is(":checked") ? "true" : "false";
            var viewtype = "";
            var canvas_id = "";
            var transcript_hidden = "";
            var transcript_download = "";
            var video_download = "";
            if (mediaType === "ig") {
                viewtype = jQuery(element).find('.mirador-view-type').val();
                canvas_id = jQuery(element).find('.canvas-id').val();
            } else if (mediaType === "vd") {
                transcript_hidden = jQuery(element).find('.transcript-hidden').is(":checked") ? "true": "false";
                transcript_download = jQuery(element).find('.transcript-download').is(":checked") ? "true": "false";
                video_download = jQuery(element).find('.video-download').is(":checked") ? "true": "false";
            }

            var options = viewtype + "," + canvas_id + "," + dashboard_hidden + ',' + transcript_hidden + ',' + transcript_download + ',' + video_download;
            options = options.replace(/undefined/g, "");

            jQuery('#' + form_id + 'target_external_options').html(options);
            jQuery('#' + form_id + 'order').attr('value', order);
            jQuery('.erase#' + form_id + 'id').remove();
        });
        var course = jQuery('#assignment-name-input').data('course-id');
        jQuery('#id_course').val(course);
        jQuery('#id_assignment_name').val(jQuery('#assignment-name-input').val());
        jQuery('#id_common_inst_name').val(jQuery('#common_inst_name').val().trim());
        jQuery("#id_is_published").attr("checked", jQuery("#assignment-published").is(":checked") ? true : false);
        jQuery('#id_use_hxighlighter').attr("checked", true)
        jQuery('form').submit();
    },
    save_annotation_settings: function() {
        var self = this;
        if (this.empty_check()) {
            jQuery('#pagination-limit').css('border', '1px solid lightgray');
            this.annotation_settings_page.find('.error').remove();
            this.main_page.show();
            this.annotation_settings_page.hide();

            // start moving items to the form since they hit "save"
            jQuery('#id_include_mynotes_tab').prop('checked', jQuery('#student-tab-visible').prop('checked'));
            jQuery('#id_include_instructor_tab').prop('checked', jQuery('#instructor-tab-visible').prop('checked'));
            jQuery('#id_include_public_tab').prop('checked', jQuery('#public-tab-visible').prop('checked'));
            jQuery('#id_default_tab').val(jQuery('#default-tab').val());
            jQuery('#id_pagination_limit').val(jQuery('#pagination-limit').val());
            jQuery('#id_allow_highlights').prop('checked', jQuery('#enable-tags').prop('checked'));

            var tag_string = "";
            jQuery.each(jQuery('.trow:not(.theader)'), function(index, element) {
                if (tag_string !== "") {
                    tag_string += ",";
                }
                tag_string += jQuery(element).find('.custom-tag-name').val();
                tag_string += ':' + self.rgb2hex(jQuery(element).find('.custom-tag-color-chosen').css('background-color'));
            })
            jQuery('#id_highlights_options').val(tag_string);
        }
    },
    empty_check: function(){
        console.log('Checking to make sure nothing was left blank that should not have been left blank.');

        var noErrors = true;
        // list of fields that should not be left blank
        var list_of_fields = [
            "#assignment-name-input",
            "#pagination-limit",
        ];
        jQuery.each(list_of_fields, function(index, field) {
            var field_to_check = jQuery(field);
            if (field_to_check.val() == '' || field_to_check.val() == undefined) {
                field_to_check.css('border', '4px solid red');
                field_to_check.after('<p class="error" style="color: red; margin-left: 25px; margin-top: -10px;">Do not leave this field blank.</p>');
                noErrors = false;
            }
        });
        return noErrors;
    },
    error_check: function(){
        console.log('Checking to see if there are any errors in the form');  
    },

    keyPressOn: function(parent, child, codesAndFuncs) {
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
    },

    keyCodeValue: function(keyCode) {
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
    }
};

jQuery(document).ready(function() {
    window.assignment_editor = window.assignment_editor || new AssignmentEditor();
});
