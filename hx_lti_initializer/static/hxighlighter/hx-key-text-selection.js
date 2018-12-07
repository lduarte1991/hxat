/* 
 * Selector Component
 * Should do the following:
 *      1) Given an HTML element, save content, turn it into a textarea
 *      2) Test delimiters and change/notify if necessary
 *      3) Allow only arrow keys and delimiter element to be used
 *      4) Once a selection has been identified, pass back range
 *      5) If selection is then unmade, pass back undefined
 */

var HxKeyboardTextSelection = function(inst) {
    this.delimiter_list = ['*', '+', '|'];
    this.keyMaps = {
        'BACKSPACE': 8,
        'TAB': 9,
        'ENTER': 13,
        'SHIFT': 16,
        'CTRL': 17,
        'ALT': 18,
        'ESC': 27,
        'SPACE': 32,
        'LEFT': 37,
        'UP': 38,
        'RIGHT': 39,
        'DOWN': 40,
        'DELETE': 46,
        'MULTIPLY': 106,
        'ADD': 107,
        'PIPE': 220,
        '*': 56,
        '+': 187,
        'HOME': 36,
        'END': 35
    }
    this.instance_id = inst;
};

HxKeyboardTextSelection.prototype.init = function(element) {
    this.element = element;
    this.delimiter = this.checkDelimiter(element);
    console.log(this.delimiter);
    if (!this.delimiter) {
        console.log('Error in delimiter...no suitable delimiter found!');
    }
    this.start = undefined;
};

HxKeyboardTextSelection.prototype.checkDelimiter = function(element) {
    var textSearch = jQuery(element).text();
    for (var i = 0; i < this.delimiter_list.length; i++) {
        var testDelimiter = this.delimiter_list[i];
        console.log(textSearch, testDelimiter);
        if (textSearch.indexOf(testDelimiter) == -1) {
            return testDelimiter;
        }
    }
    return undefined;
};

HxKeyboardTextSelection.prototype.turnSelectionModeOn = function() {
    jQuery(this.element).attr('contenteditable', 'true');
    jQuery(this.element).attr('role', 'textbox');
    jQuery(this.element).attr('tabindex', "0");
    jQuery(this.element).attr('aria-multiline', 'true');
    jQuery(this.element).attr('accesskey', 't');
    jQuery(this.element).on('keydown', jQuery.proxy(this.filterKeys, this));
    jQuery(this.element).on('keyup', jQuery.proxy(this.setSelection, this));
};

HxKeyboardTextSelection.prototype.turnSelectionModeOff = function() {
    jQuery(this.element).off('keydown');
    jQuery(this.element).off('keyup');
    jQuery(this.element).attr('contenteditable', 'false');
    jQuery(this.element).attr('role', '');
    jQuery(this.element).attr('tabindex', '');
    jQuery(this.element).attr('aria-multiline', 'false');
    jQuery(this.element).attr('outline', '0px');
};

/* Credit to Rich Caloggero
 * https://github.com/RichCaloggero/annotator/blob/master/annotator.html
 */
HxKeyboardTextSelection.prototype.filterKeys = function(keyPressed) {
    var self = this;
    const key = keyPressed.key;
    switch (key) {
        case self.delimiter:
        case "ArrowUp":
        case "ArrowDown":
        case "ArrowLeft":
        case "ArrowRight":
        case "Home":
        case "End":
        case "Tab":
            return true;
        case "Backspace":
            if (self.verifyBackspace()) {
                self.start = undefined;
                return true;
            }
        default: keyPressed.preventDefault();
            return false;
        } // switch
};

HxKeyboardTextSelection.prototype.setSelection = function(keyPressed) {
    var self = this;
    const key = keyPressed.key;
    console.log(this, self.delimiter);
    switch (key) {
        case self.delimiter:
            if (!(self.start)) {
                self.start = self.copySelection(getSelection());
                console.log("Found initial");
            } else {
                console.log("Found final");
                self.processSelection(self.start, self.copySelection(getSelection()));
            }
    }
};

HxKeyboardTextSelection.prototype.copySelection = function(selection) {
    const sel = {
        anchorNode: selection.anchorNode,
        anchorOffset: selection.anchorOffset,
        focusNode: selection.focusNode,
        focusOffset: selection.focusOffset
    };
    return sel;
};

HxKeyboardTextSelection.prototype.processSelection = function(start, end) {
    const s = getSelection();
    const r = this.removeMarkers(start, end);
    this.start = undefined;

    // publish selection made
    console.log(this.instance_id);
    hxPublish('keyboardSelectionMade', this.instance_id, [r]);
}

HxKeyboardTextSelection.prototype.removeMarkers = function(start, end) {
    const _start = start.anchorNode;
    const _startOffset = start.anchorOffset - 1;
    const _end = end.anchorNode;
    const _endOffset = end.anchorOffset -1;

    const t2 = this.removeCharacter(_end.textContent, _endOffset);
    _end.textContent = t2;
    const t1 = this.removeCharacter(_start.textContent, _startOffset);
    _start.textContent = t1;

    const r = new Range();
    r.setStart(_start, _startOffset);
    r.setEnd(_end, _endOffset - 1);
    return r;
};

HxKeyboardTextSelection.prototype.removeCharacter = function(s, offset) {
    if (offset === 0) {
        s = s.slice(1);
    } else if (offset === s.length-1) {
        s = s.slice(0, -1);
    } else {
        s = s.slice(0, offset) + s.slice(offset+1);
    }
    return s;
};

HxKeyboardTextSelection.prototype.verifyBackspace = function() {
    const s = getSelection();
    const r = new Range();
    var startOffset = s.anchorOffset;
    if (startOffset > 0) {
        startOffset -= 1;
    }
    r.setStart(s.anchorNode, startOffset);
    r.setEnd(s.anchorNode, startOffset + 1);

    return r.toString() == this.delimiter;
};