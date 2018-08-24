/**
 * Helper functions that can be/are reused in other Hx projects.
 */


/**
 * Publishes events to trigger subscribers to perform something
 *
 * @param      {string}  eventName   The event name
 * @param      {string}  instanceID  The instance id
 * @param      {list}  list        The list
 */
function hxPublish(eventName, instanceID, list) {
    jQuery.publish(eventName + '.' + instanceID, list);
}

/**
 * Subscribes to events triggered above and performs a callback
 *
 * @param      {string}  eventName   The event name
 * @param      {string}  instanceID  The instance id
 * @param      {function}  callBack    The callback
 */
function hxSubscribe(eventName, instanceID, callback) {
    jQuery.subscribe(eventName + '.' + instanceID, callback);
}

/**
 * Gets the current top/left position for an event (in particular your mouse pointer)
 *
 * @param      {Object}  event   The event
 * @return     {Object}  { description_of_the_return_value }
 */
function mouseFixedPosition(event) {
    var body = window.document.body;
    var offset = {top: 0, left: 0};

    if ($(body).css('position') !== "static") {
        offset = $(body).offset();
    }

    var top = event.pageY - offset.top;
    var left = event.pageX - offset.left;
    // in case user is selecting via keyboard, this sets the adder to top-left corner
    if (event.type.indexOf("mouse") === -1 && event.type.indexOf('key') > -1) {
        var boundingBox = window.getSelection().getRangeAt(0).getBoundingClientRect();
        top = boundingBox.top - offset.top + boundingBox.height;
        left = boundingBox.left - offset.left + boundingBox.width;
    }
    return {
        top: top,
        left: left
    };
}

function trim(s) {
    if (typeof String.prototype.trim === 'function') {
        return String.prototype.trim.call(s);
    } else {
        return s.replace(/^[\s\xA0]+|[\s\xA0]+$/g, '');
    }
}

function watchForChange(selector, callback) {
    var observer = new MutationObserver(callback);
    observer.observe(jQuery(selector)[0], {
        'subtree': true,
        'childList': true
    });
    return observer;
}

function getQuoteFromHighlights(ranges) {
    var text = [];
    var exactText = [];
    for (var i = 0, len = ranges.length; i < len; i++) {
        text = [];
        var r = ranges[i];
        text.push(trim(r.text()));

        var exact = text.join(' / ').replace(/[\n\r]/g, '<br>') ;
        exactText.push(exact);
    }
    return {
        'exact': exactText,
        'exactNoHtml': text
    };
}

function exists(obj) {
    return typeof(obj) !== 'undefined';
}

function pauseEvent(e){
    if(e.stopPropagation) e.stopPropagation();
    if(e.preventDefault) e.preventDefault();
    e.cancelBubble=true;
    e.returnValue=false;
    return false;
}