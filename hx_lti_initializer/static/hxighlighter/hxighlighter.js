/**
 * Hxighlighter is the superclass that will contain all instances of the tool.
 * It will allow users to set up targets to annotate and then ways to annotate
 */

window.Hxighlighter = window.Hxighlighter || function(options) {

    // if no current instances, set up the dictionary
    if (!exists(Hxighlighter._instances)) {
        Hxighlighter._instances = {};
    }

    // create a unique id for this instance
    var inst_id = options.inst_id;
    if (!exists(inst_id)) {
        if (exists(options.commonInfo.context_id) ||
            exists(options.commonInfo.collection_id)||
            exists(options.commonInfo.object_id)) {
                inst_id = Hxighlighter.getUniqueId();
        } else {
            inst_id = options.commonInfo.context_id + ':' + options.commonInfo.collection_id + ':' + options.commonInfo.object_id
        }
    }

    // save the new instance by its id
    Hxighlighter._instances[inst_id] = {
        'id': inst_id
    };

    if (exists(options.targetOptions)) {
        var tOptions = jQuery.extend({}, options.targetOptions, options.commonInfo);
        Hxighlighter._instances[inst_id].targetController = new Hxighlighter.Target(tOptions, inst_id);
    }

    if (exists(options.coreOptions)) {
        var cOptions = jQuery.extend({}, options.coreOptions, options.commonInfo);
        Hxighlighter._instances[inst_id].core = new Hxighlighter.Core(cOptions, inst_id);
    }
};

/**
 * Gets the unique identifier.
 * https://stackoverflow.com/questions/105034/create-guid-uuid-in-javascript
 * @return     {string} { Unique identifier }
 */
Hxighlighter.getUniqueId = function() {
    function s4() {
        return Math.floor((1 + Math.random()) * 0x10000)
          .toString(16)
          .substring(1);
      }
      return s4() + s4() + '-' + s4() + '-' + s4() + '-' + s4() + '-' + s4() + s4() + s4();
};