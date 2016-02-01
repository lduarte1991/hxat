//videojs-download-plugin
// by Luis Duarte 2016
vjs.DownloadMenuButton = vjs.MenuButton.extend({
	init: function(player, options) {
		vjs.MenuButton.call(this, player, options);
	};
});

vjs.DownloadMenuButton.prototype.createEl = function(){
	var el = vjs.Component.prototype.createEl.call(this, 'div', {
		className: 'vjs-download-control',
		innerHTML: '<div class="vjs-control-content"><span class="vjs-control-text">Download Video/Transcript</span></div>',
	});

	return el;
};

vjs.DownloadMenuButton.prototype.createMenu = function (){
	var menu = new vjsMenu(this.player());
	var downloads = this.player().options()['downloadItems'];

	if (downloads) {
		if (downloads['video']) {
			menu.addChild(
				new vjs.DownloadMenuItem(this.player(), {'downloadItem': 'Download Video', 'source': downloads['video']});
			);
		};
		if (downloads['transcript']) {
			menu.addchild(
				new vjs.DownloadMenuItem(this.player(), {'downloadItem': 'Download Transcript', 'source': downloads['video']});
			);
		};
	};

	return menu;
};

vjs.DownloadMenuItem = vjs.MenuItem.extend({
	contentElType: 'button',
	init: function(player, options) {
		var label = this.label = options['downloadItem'];
		var src = this.src = options['source'];

		options['label'] = label;
		vjs.MenuItem.call(this, player, options);
	}
});

vjs.DownloadMenuItem = vjs.MenuItem.prototype.onClick = function() {
	vjs.MenuItem.prototype.onClick.call(this);
	window.open(this.src);
};