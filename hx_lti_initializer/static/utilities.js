//utilities.js

/*
 *  jQuery.ajaxSetup
 *  Makes sure that the csrf cookie is set properly on all your ajax requests
 *
 */

jQuery.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (settings.type == 'POST' || settings.type == 'PUT' || settings.type == 'DELETE') {
            function getCookie(name) {
                var cookieValue = null;
                if (document.cookie && document.cookie != '') {
                    var cookies = document.cookie.split(';');
                    for (var i = 0; i < cookies.length; i++) {
                        var cookie = jQuery.trim(cookies[i]);
                        // Does this cookie string begin with the name we want?
                        if (cookie.substring(0, name.length + 1) == (name + '=')) {
                            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                            break;
                        }
                    }
                }
                return cookieValue;
            }
            if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
                // Only send the token to relative URLs i.e. locally.
                xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken') || window.csrf_token_backup);
            }
        }
    }
});

/*
 *  Utils
 *  Contains items that might be useful elsewhere. In this case it contains a way to
 *  listen and create messages between the iFrame and the origin page. It will also
 *  send items via the logThatThing.
 *
 */

(function($) {
    $.Utils = function(origin) {
        this.init();
        this.mainOrigin = origin;
        this.logSource = undefined;
        this.logOrigin = undefined;
        return this;
    };

    // Makes sure that window listens for the iFrame message
    $.Utils.prototype.init = function() {
        window.addEventListener('message', this.receiveMessage.bind(this), false);
        jQuery.subscribe('logThatThing', this.logViaEvent.bind(this));
    };

    // the only thing that matters is to retain the source and origin once it has received
    $.Utils.prototype.receiveMessage = function(event) {
        if (event.data !== undefined) {
            if (event.data == "hide thread") {
                jQuery('.new-thread').remove();
            }
        }
        console.log(event);
        if (event.origin !== this.mainOrigin) {
            return;
        }
        this.logSource = event.source;
        this.logOrigin = event.origin;
        console.log(event);
    };

    // if we are in an iFrame, it sends the events via postMessage
    // if we are in edX it calls the Logger function
    // otherwise it just prints it to the console. 
    $.Utils.prototype.logThatThing = function(action, thing, source, object) {
        if (this.logSource && this.logSource.postMessage) {
            // this checks to see if the current codebase is in an iframe with the logger in the parent
            this.logSource.postMessage({
                'event': "log",
                'event-source': source,
                'event-object': object,
                'action': action,
                'object': JSON.stringify(thing)
            }, this.logOrigin);
        } else if(window.Logger !== undefined) {
            // this checks to see if its in the same page as the logger
            Logger.log(source + '.' + object + '.' + action, JSON.stringify(thing));
        } else {
            // for debug
            console.log("Could not find logger.");
            console.log("Here's what I would have logged: " + source + '.' + object + '.' + action);
            console.log(JSON.stringify(thing));
        }
    };

    // calls the logThat thing from the pub/sub rather than through deep diving
    $.Utils.prototype.logViaEvent = function(_, action, thing, source, object) {
        this.logThatThing(action, thing, source, object);
    };

}(AController));