/* AController.js
 *
 * This initializes the main Annotation Controller and all its parts on the page.
 * It calls upon the 4 parts of the tool:
 *     1) Target Object - to be annotated
 *     2) Annotation Core Library - doing the annotating
 *     3) Annotation Server - storing the annotation
 *     4) Dashboard Object - displays annotations
 */

window.AController = window.AController || function(aControllerOptions) {
	AController.main = new AController.AnnotationMain(aControllerOptions);
	AController.targetObjectController = new AController.TargetObjectController(aControllerOptions.targetObjectOptions);
	//AController.annotationServer = new AController.AnnotationServer(aControllerOptions.annotationServerOptions);
	AController.annotationCore = new AController.AnnotationCore(aControllerOptions.annotationCoreOptions, aControllerOptions.commonInfo);
	//AController.dashboardObjectController = new AController.DashboardController(aControllerOptions.dashboardObjectOptions);
}