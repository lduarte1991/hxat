from django.contrib.staticfiles.storage import ManifestStaticFilesStorage
from collections import OrderedDict
import logging

logger = logging.getLogger(__name__)

class MixedManifestStaticFilesStorage(ManifestStaticFilesStorage):
    '''
    This subclasses ManifestStaticFilesStorage to make it possible for the static asset manifest
    to have a "mix" of files that have been hashed, and files that have not.

    Example:

    {
        "paths": {
            "AController.js": "AController.73751240244b.js",
            "admin/css/base.css": "admin/css/base.css"
        }
    }

    The problem this solves is when vendor CSS contains url() references to images or other static assets that were
    not included in the build/distribution, and causes the post processor to fail. An example is mirador-combined.css,
    which includes jqueryui as part of the distribution, but refers to image assets that were not included with mirador.
    This issue causes the ManifestStaticFilesStorage post processor to fail.
    '''
    def post_process(self, paths, dry_run=False, **options):
        hashed_files = OrderedDict()

        # We can be reasonably confident that JS files can be hashed without any problem because we're not trying to
        # change references inside the files themselves. This is not the case with CSS.
        paths_to_process, paths_to_skip = dict(), dict()
        for path in paths:
            if path.endswith(".js"):
                paths_to_process[path] = paths[path]
            else:
                paths_to_skip[path] = paths[path]

        result = []

        # Skip the hashing process on these paths, so the filename won't change to point to a hashed filename
        for path in paths_to_skip:
            processed = False
            hashed_files[path] = path
            result.append((path, path, processed))

        # Run the hashing process on the paths we want to process
        all_post_processed = super(ManifestStaticFilesStorage, self).post_process(paths_to_process, dry_run, **options)
        for post_processed in all_post_processed:
            result.append(post_processed)

        self.hashed_files.update(hashed_files)
        self.save_manifest()

        return result
