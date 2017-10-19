/* AController.js
 *
 * This initializes the main Annotation Controller and all its parts on the page.
 * It calls upon the 4 parts of the tool:
 *     1) Target Object - to be annotated
 *     2) Annotation Core Library - doing the annotating
 *     3) Annotation Server - storing the annotation
 *     4) Dashboard Object - displays annotations
 */

window.AController = window.AController || function(options) {
	AController.accessibility = new AController.Accessibility({
		'triggerClicks': ['.clicking_allowed']
	});
	if (typeof options.targetObjectOptions !== "undefined") {
		AController.targetObjectController = new AController.TargetObjectController(options.targetObjectOptions, options.commonInfo);
	}
	//AController.annotationServer = new AController.AnnotationServer(options.annotationServerOptions);
	if (typeof options.annotationCoreOptions !== "undefined") {
		AController.annotationCore = new AController.AnnotationCore(options.annotationCoreOptions, options.commonInfo);
	}
	if (typeof options.dashboardControllerOptions !== "undefined") {
		AController.dashboardView = AController.DashboardView;
		AController.dashboardObjectController = new AController.DashboardController(options.dashboardControllerOptions, options.commonInfo, AController.dashboardView);
	}
	AController.main = new AController.AnnotationMain(options);
	var logger_url = options.commonInfo.logger_url || "";
	AController.utils = new AController.Utils(logger_url);
};
