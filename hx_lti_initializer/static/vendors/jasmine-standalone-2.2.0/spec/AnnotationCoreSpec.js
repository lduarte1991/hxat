describe("Annotation Core Test Parameters", function(){
	
	beforeEach(function(){
		jQuery('body').append('<div class="container">Test</div>');
		this.options = {
			commonInfo: {
				mediaType: "text", // {{ media_type }}
				context_id: "Summer/BlueMonkey", // {{ context_id }}
				collection_id: "1", // {{ collection_id }}
				object_id: "1", // {{ collection_id }}
			},
			annotationCoreOptions: {
				annotationElement: jQuery(".container"),
				initOptions: {},
			},
		}
    	AController(this.options);
	});

	afterEach(function(){
		jQuery('.container').remove();
	});

	it("receives the correct mediaType", function(){
		expect(AController.annotationCore.initOptions.mediaType).toEqual("text");
	});

	it("receives the correct context_id", function(){
		expect(AController.annotationCore.initOptions.context_id).toEqual("Summer/BlueMonkey");
	});

	it("receives the correct collection_id", function(){
		expect(AController.annotationCore.initOptions.collection_id).toEqual("1");
	});

	it("receives the correct object_id", function(){
		expect(AController.annotationCore.initOptions.object_id).toEqual("1");
	});

	it("receives the correct element", function(){
		expect(AController.annotationCore.element).toEqual(jQuery(".container"));
	});

});

describe("Annotation Core Test Initialization", function(){
	
	beforeEach(function(){
		jQuery('body').append('<div class="container">Test</div>');
		this.options = {
			commonInfo: {},
			annotationCoreOptions: {
				annotationElement: jQuery(".container"),
				initOptions: {},
			},
		}
	});

	afterEach(function(){
		jQuery('.container').remove();
	});

	it("calls init", function(){
		spyOn(AController.AnnotationCore.prototype, "init");
		AController(this.options);
		expect(AController.annotationCore.init).toHaveBeenCalled();
	});

	it("calls setUpCommonAttributes", function(){
		spyOn(AController.AnnotationCore.prototype, "setUpCommonAttributes");
		AController(this.options);
		expect(AController.annotationCore.setUpCommonAttributes).toHaveBeenCalled();
	});

	it("checks if annotation_tool was created with text mediaType", function(){
		this.options.commonInfo.mediaType = "text"
		AController(this.options);
		expect(AController.annotationCore.annotation_tool).not.toBeUndefined();
	});

	it("annotation_tool should be nonexistent if unknown mediaType is passed in", function(){
		this.options.commonInfo.mediaType = "unknown"
		AController(this.options);
		expect(AController.annotationCore.annotation_tool).toBeUndefined();
	});

});

describe("Annotation Core Test Store Defaults", function() {
	beforeEach(function(){
		jQuery('body').append('<div class="container">Test</div>');
		this.options = {
			commonInfo: {
				mediaType: "text", // {{ media_type }}
				context_id: "Summer/BlueMonkey", // {{ context_id }}
				collection_id: "1", // {{ collection_id }}
				object_id: "1", // {{ collection_id }}
			},
			annotationCoreOptions: {
				annotationElement: jQuery(".container"),
				initOptions: {},
			},
		}
    	AController(this.options);
	});

	afterEach(function(){
		jQuery('.container').remove();
	});

	it("contains uri in the annotation data", function(){
		expect(AController.annotationCore.initOptions.store.annotationData.uri).not.toBeUndefined();
		expect(AController.annotationCore.initOptions.store.annotationData.uri).toEqual("1");
		expect(AController.annotationCore.initOptions.store.annotationData.uri).not.toEqual("2");
	});

	it("contains context_id in the annotation data", function(){
		expect(AController.annotationCore.initOptions.store.annotationData.context_id).not.toBeUndefined();
		expect(AController.annotationCore.initOptions.store.annotationData.context_id).toEqual("Summer/BlueMonkey");
		expect(AController.annotationCore.initOptions.store.annotationData.context_id).not.toEqual("FakeMonkey");
	});

	it("contains collection_id in the annotation data", function(){
		expect(AController.annotationCore.initOptions.store.annotationData.collection_id).not.toBeUndefined();
		expect(AController.annotationCore.initOptions.store.annotationData.collection_id).toEqual("1");
		expect(AController.annotationCore.initOptions.store.annotationData.collection_id).not.toEqual("2");
	});

	it("contains correct info in the loadFromSearch attribute", function(){
		expect(AController.annotationCore.initOptions.store.loadFromSearch.uri).not.toBeUndefined();
		expect(AController.annotationCore.initOptions.store.loadFromSearch.uri).toEqual("1");
		expect(AController.annotationCore.initOptions.store.loadFromSearch.uri).not.toEqual("2");
		expect(AController.annotationCore.initOptions.store.loadFromSearch.limit).not.toBeUndefined();
		expect(AController.annotationCore.initOptions.store.loadFromSearch.limit).toEqual(10000);
		expect(AController.annotationCore.initOptions.store.loadFromSearch.limit).not.toEqual(5000);
	});
});