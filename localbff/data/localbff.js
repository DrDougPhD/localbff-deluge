/*
Doug: Tuesday, 28 April 2013 at 16:41
Script: localbff.js
    The client-side javascript code for the LocalBFF plugin.

Copyright:
    (C) Doug McGeehan 2009 <doug.mcgeehan@mst.edu>
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3, or (at your option)
    any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, write to:
        The Free Software Foundation, Inc.,
        51 Franklin Street, Fifth Floor
        Boston, MA  02110-1301, USA.

    In addition, as a special exception, the copyright holders give
    permission to link the code of portions of this program with the OpenSSL
    library.
    You must obey the GNU General Public License in all respects for all of
    the code used other than OpenSSL. If you modify file(s) with this
    exception, you may extend this exception to your version of the file(s),
    but you are not obligated to do so. If you do not wish to do so, delete
    this exception statement from your version. If you delete this exception
    statement from all source files in the program, then also delete it here.
*/

// define spacer element for UI forms
Ext.ux.form.Spacer = Ext.extend(Ext.BoxComponent, {
  	height: 10,
  	autoEl: 'div'
});
Ext.reg('spacer', Ext.ux.form.Spacer);

// specify Deluge ux namespace
Ext.ns('Deluge.ux');

// define plugin details tab
Deluge.ux.LocalBFFTab = Ext.extend(Ext.Panel, {
	
	// set defaults for UI settings
	title: _('LocalBFF'),

  columns: [{ header: _('Filename'), width: 300, dataIndex: 'filename'}],

	constructor: function() {
		Deluge.ux.LocalBFFTab.superclass.constructor.call(this);

    this.progressBar = this.add({
      xtype: 'progress',
      cls: 'x-deluge-status-progressbar'
    });
	},

  update: function(torrentId) {
    console.log(torrentId);
  }

  //onRender: function(ct, position) {
    //Deluge.details.LocalBFFTab.superclass.onRender.call(this, ct, position);
  //}
});

// specify Deluge preferences namespace
Ext.ns('Deluge.ux.preferences');

// define plugin page
Deluge.ux.preferences.LocalBFFPage = Ext.extend(Ext.Panel, {
	
	// set defaults for UI settings
	border: false,
	title: _('LocalBFF'),
	layout: 'fit',

	// initialize function
	initComponent: function() {
	
		// call superclass's initialize function
		Deluge.ux.preferences.LocalBFFPage.superclass.initComponent.call(this);

		// define list view for directory list
		this.list = new Ext.list.ListView({
			store: new Ext.data.SimpleStore({
				fields: [
					{name: 'directory', mapping: 1}
				],
				id: 0
			}),
			columns: [{
				width: 1,
				header: _('File Directories'),
				sortable: true,
				dataIndex: 'directory'
			}],
			autoHeight: true,
			singleSelect: true,
			autoExpandColumn: 'directory'
		});		

		// add form to Preferences UI to contain plugin's UI elements
		this.form = this.add({
			xtype: 'form',
			layout: 'fit',
			border: false,
			hideBorders: true,
			autoHeight: true
		});

		// add list view to Preferences UI
		this.panel = this.form.add({
			border: true,
			height: 200,
			items: [this.list],
			bbar: {
				items: [{
					text: _('Add'),
					iconCls: 'icon-add',
					handler: this.onAddClick,
					scope: this
				}, {
					text: _('Edit'),
					iconCls: 'icon-edit',
					handler: this.onEditClick,
					scope: this,
					disabled: true
				}, '->', {
					text: _('Remove'),
					iconCls: 'icon-remove',
					handler: this.onRemoveClick,
					scope: this,
					disabled: true
				}]
			},
			
		});

		// add spacer element to the form
		this.form.add({xtype: 'spacer'});

		// add the Force Update Cache button to the form
		this.forceUpdateButton = this.form.add({
			xtype: 'button',
			text: _('Force Update Cache'),
			listeners: {
				'click': {
					fn: this.onForceUpdate,
					scope: this
				}			
			}
		});

		// add spacer element to the form
		this.form.add({xtype: 'spacer'});

		// add the description of the Force Update Cache button to the form
		this.form.add({
			xtype: 'box',
			autoEl: {
				cn: '<p>This button forces the plugin cache to clear and re-initialize.</p><br>'
			}
		});		

		// add the Default Action combo box to the form
		this.defaultActionComboBox = this.form.add({
			xtype: 'combo',
			fieldLabel: _('Default Action'),
			name: 'defaultaction',
			mode: 'local',
			width: 200,
			store: new Ext.data.ArrayStore({
				fields: ['id', 'text'],
				data: [
					[0, _('Download Payload')],
					[1, _('Delete Payload')],
					[2, _('Pause Download')]
				]
			}),
			editable: false,
			triggerAction: 'all',
			valueField: 'id',
			displayField: 'text'
		});
		this.defaultActionComboBox.on('select', this.onDefaultActionSelect, this);

		// add the description of the Default Action combo box to the form
		this.form.add({
			xtype: 'box',
			autoEl: {
				cn: '<p>This is the default action the plugin will take upon ' +
				    'finding a potential match for a newly added torrent.</p><br>'
			}
		});

		// set updateConfig function to trigger on show event
      		deluge.preferences.on('show', this.updateConfig, this);
	},

	// called when user clicks list view's Add button
	onAddClick: function() {
	},

	// called when user clicks list view's Edit button
	onEditClick: function() {
	},

	// called when user clicks list view's Remove button
	onRemoveClick: function() {
	},

	// called when user clicks the Force Update Cache button
	onForceUpdate: function() {
	},

	// called when user selects the Default Action for the plugin
	onDefaultActionSelect: function() {
	},

	// called on Preferences page render
	onRender: function(ct, position) {

		// call superclass's onRender function
		Deluge.ux.preferences.LocalBFFPage.superclass.onRender.call(this, ct, position);

		// initialize form layout
		this.form.layout = new Ext.layout.FormLayout();

		// set form layout container
		this.form.layout.setContainer(this);

		// execute layout
		this.form.doLayout();
	},

	// called on Apply button click
	onApply: function() {

	},

	// called after Preferences page render
	afterRender: function() {
		
		// call superclass's afterRender function
		Deluge.ux.preferences.LocalBFFPage.superclass.afterRender.call(this);
	},

  	// called when configuration needs to be updated
  	updateConfig: function() {

  	}
});

// initialize LocalBFF plugin
Deluge.plugins.LocalBFFPlugin = Ext.extend(Deluge.Plugin, {
	
	// set defaults for plugin settings
	name: 'NewLocalBFF',

	// called on plugin disable
	onDisable: function() {
	    	deluge.preferences.removePage(this.prefsPage);
	},

	// called on plugin enable
	onEnable: function() {
    		
		//alert("LocalBFF enabled!");
		this.prefsPage = deluge.preferences.addPage(new Deluge.ux.preferences.LocalBFFPage());
		deluge.details.add(new Deluge.ux.LocalBFFTab());

    		//Add Relink and Seed button context menu
    		this.torrentMenu = new Ext.menu.Menu();

    		this.tmSep = deluge.menus.torrent.add({xtype:'menuseparator'});

    		this.tm = deluge.menus.torrent.add({
      			text: _('Relink and seed'),
      			label: 'Reconnect torrrent to payload if it exists',
      			handler: function(item, e) {
      			    var selected_torrent_ids = deluge.torrents.getSelectedIds();
      			    
      			    // Iterate over each selected torrent, and fire off a relink
      			    //  operation for the selected torrent.
      			    Ext.each(selected_torrent_ids, function(id, i) {
      			      console.log("Torrent ID: " + id);
      			      deluge.client.localbff.relink(292)
      			    });
      			},
      			scope: this
    		});
	}
});

// register LocalBFF plugin with Deluge
Deluge.registerPlugin('NewLocalBFF', Deluge.plugins.LocalBFFPlugin);
