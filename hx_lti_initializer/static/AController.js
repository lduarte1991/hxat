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
	AController.main = new AController.AnnotationMain(options);
	AController.targetObjectController = new AController.TargetObjectController(options.targetObjectOptions);
	//AController.annotationServer = new AController.AnnotationServer(options.annotationServerOptions);
	AController.annotationCore = new AController.AnnotationCore(options.annotationCoreOptions, options.commonInfo);
	AController.dashboardObjectController = new AController.DashboardController(options.dashboardControllerOptions, options.commonInfo);
}