/*
Doug: Thursday, 2 May 2013 at 15:45
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
Deluge.ux.LocalBFFTab = Ext.extend(Ext.ux.tree.TreeGrid, {
	
	// set defaults for UI settings
	title: _('LocalBFF'),

  rootVisible: false,

  columns: [
    {
      header: _('File'),
      width: 300,
      dataIndex: 'filename'
    },
    {
      header: _('Potential Matches'),
      width: 150,
      dataIndex: 'matches'
    }
  ],

  initComponent: function() {
    Deluge.ux.LocalBFFTab.superclass.initComponent.call(this);
    this.setRootNode(new Ext.tree.TreeNode({text: 'Files'}) );
  },

  update: function(torrentId) {
    function add(torrentId, parentNode) {
      parentNode.appendChild(new Ext.tree.TreeNode({
        filename: torrentId
      }));
    }

    if(this.torrentId != torrentId)
    {
      this.torrentId = torrentId;
      // {'a/payload/file': 4}
      var potentialMatches = deluge.client.localbff.find_potential_matches(torrentId);
      
      console.log(potentialMatches); 
      var root = this.getRootNode();
      add(torrentId, root);
      root.firstChild.expand();
    }
  },

  //Update file match information
  updateMatchInfo: function(torrentId) {
    function add(torrentId, parentNode) {
      parentNode.appendChild(new Ext.tree.TreeNode({
        filename: torrentId
        })
      );
    }

    var root = this.getRootNode();
    add(torrentId, root);
    root.firstChild.expand();
  },

  //Clear tab of all existing information
  clear: function() {
    
    var root = this.getRootNode();
    
    //check if root node has any children
    if(!root.hasChildNodes()) return;

    //If root has children, erase them
    root.cascade( 
      function(node) {
        var parentNode = node.parentNode;
        if(!parentNode) return;
        if(!parentNode.ownerTree) return;
        parentNode.removeChild(node);
      }
    );
  }
 
});

//////////////////////////////////////////
//					//
//	MAX'S DOMAIN START		//
//					//
//////////////////////////////////////////

// specify Deluge.ux namespace
Ext.ns('Deluge.ux');

// define LocalBFFDirectoryWindowBase model
Deluge.ux.LocalBFFDirectoryWindowBase = Ext.extend(Ext.Window, {
	
	// set defaults for window base settings
	layout: 'fit',
	width: 400,
	height: 130,
	closeAction: 'hide',

	// initialize function
	initComponent: function() {

		// call superclass's initialize function
		Deluge.ux.LocalBFFDirectoryWindowBase.superclass.initComponent.call(this);

		// add Cancel button to window base
		this.addButton(_('Cancel'), this.onCancelClick, this);

		// add form elements to window base
		this.form = this.add({
			xtype: 'form',
			baseCls: 'x-plain',
			bodyStyle: 'padding: 5px',
			items: [{
				xtype: 'textfield',
				fieldLabel: _('Directory'),
				name: 'dir_name',
				width: 270
			}]
		});
	},

	// called when user clicks window's Cancel button
	onCancelClick: function() {

		// closes window
		this.hide();
	}
});

// define Edit Directory dialog
Deluge.ux.EditLocalBFFDirectoryWindow = Ext.extend(Deluge.ux.LocalBFFDirectoryWindowBase, {

	// set defaults for dialog settings
	title: _('Edit Directory'),

	// initialize function
	initComponent: function() {

		// call superclass's initialize function
		Deluge.ux.EditLocalBFFDirectoryWindow.superclass.initComponent.call(this);

		// add Save button to dialog
		this.addButton(_('Save'), this.onSaveClick, this);

		// add directoryedit event to dialog
		this.addEvents({
			'directoryedit': true
		});
	},

	// called when Edit Dialog is displayed
	show: function(directory) {

		// call superclass's show function
		Deluge.ux.EditLocalBFFDirectoryWindow.superclass.show.call(this);

		// set dialog's directory object to selected directory
		this.directory = directory;

		// populate form fields with directory information
		this.form.getForm().setValues({
			dir_name: directory.get('directory')
		});
	},

	// called when user clicks dialog's Save button
	onSaveClick: function() {

		// retrieve values from forms in dialog
		var values = this.form.getForm().getFieldValues();

		// calls the python core method to update directory in plugin's config
		deluge.client.localbff.save_command(this.command.id, values.dir_name {
			success: function() {
				this.fireEvent('directoryedit', this, values.dir_name);
			},
			scope: this
		});

		// close dialog
		this.hide();
	}

});

// define Add Directory dialog
Deluge.ux.AddLocalBFFDirectoryWindow = Ext.extend(Deluge.ux.LocalBFFDirectoryWindowBase, {

	// set defaults for dialog settings
	title: _('Add Directory'),

	// initialize function
	initComponent: function() {

		// call superclass's initialize function
		Deluge.ux.AddLocalBFFDirectoryWindow.superclass.initComponent.call(this);

		// add Add button to dialog
		this.addButton(_('Add'), this.onAddClick, this);

		// add directoryadd event to dialog
		this.addEvents({
			'directoryadd': true
		});
	},

	// called whenever the user clicks the dialog's Add button
	onAddClick: function() {

		// retrieve values from forms in dialog
		var values = this.form.getForm().getFieldValues();

		// calls the python core method to add directory to plugin's config
		deluge.client.localbff.add_directory(values.dir_name, {
			success: function() {
				this.fireEvent('directoryadd', this, values.dir_name);
			},
			scope: this
		});

		// close dialog
		this.hide();
	}

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

		// set onPreferencesShow function to trigger on show event
      		deluge.preferences.on('show', this.onPreferencesShow, this);
	},

	// called when preferences page for plugin is displayed
	onPreferencesShow: function() {
	
		// update directory list in preferences UI
		this.updateDirectories();
	},

	// called when user selects an item from directory list in preferences UI
	onSelectionChange: function(dv, selections) {

		// enable/disable the edit/remove buttons if item from directory list is/is not selected
		if (selections.length) {
			this.panel.getBottomToolbar().items.get(1).enable();
			this.panel.getBottomToolbar().items.get(3).enable();
		} else {
			this.panel.getBottomToolbar().items.get(1).disable();
			this.panel.getBottomToolbar().items.get(3).disable();
		}
	}

	// called when user clicks list view's Add button
	onAddClick: function() {

		// if Add Directory dialog is not currently active, create new dialog
		if (!this.addWin) {
			this.addWin = new Deluge.ux.AddLocalBFFDirectoryWindow();
			this.addWin.on('directoryadd', function() {
				this.updateDirectories();
			}, this);
		}

		// display new dialog
		this.addWin.show();
	},

	// called when user adds a directory to the plugin's config
	onDirectoryAdded: function(win, dir) {

		// adds directory into directory list in preferences UI
		var record = new this.list.getStore().recordType({
			directory: dir
		});
	},

	// called when user clicks list view's Edit button
	onEditClick: function() {

		// if Edit Directory dialog is not currently active, create new dialog
		if (!this.editWin) {
			this.editWin = new Deluge.ux.EditLocalBFFDirectoryWindow();
			this.editWin.on('directoryedit', function() {
				this.updateCommands();
			}, this);
		}

		// display new dialog, populated with the selected directory information
		this.editWin.show(this.list.getSelectedRecords()[0]);
	},

	// called when user clicks list view's Remove button
	onRemoveClick: function() {

		// get selected directory from preferences UI
		var record = this.list.getSelectedRecords()[0];

		// call the python core method to remove directory from plugin's config
		deluge.client.localbff.remove_directory(record.id, {
			success: function() {
				this.updateDirectories();
			},
			scope: this
		});
	},

	// fetches directories from plugin's config and reloads table in preferences UI
	updateDirectories: function() {

		// calls the python core method to get directories from plugin's config
	    	deluge.client.localbff.get_directories({
			success: function(directories) {
				this.list.getStore().loadData(directories);
			},
			scope: this
		});
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
	name: 'LocalBFF',

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
      			text: _('Relink and seed')
    		});
	}
});

//////////////////////////////////////////
//					//
//	MAX'S DOMAIN END		//
//					//
//////////////////////////////////////////


/*
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
      			      deluge.client.localbff.relink(id)
      			    });
      			},
      			scope: this
    		});
	}
});
*/
// register LocalBFF plugin with Deluge
Deluge.registerPlugin('LocalBFF', Deluge.plugins.LocalBFFPlugin);
