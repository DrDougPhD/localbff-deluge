#
# core.py
#
# Copyright (C) 2009 Doug McGeehan <doug.mcgeehan@mst.edu>
#
# Basic plugin template created by:
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
# Copyright (C) 2009 Damien Churchill <damoxc@gmail.com>
#
# Deluge is free software.
#
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 3 of the License, or (at your option)
# any later version.
#
# deluge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with deluge.    If not, write to:
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA  02110-1301, USA.
#
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.
#

from deluge.log import LOG as log
from deluge.plugins.pluginbase import CorePluginBase
import deluge.component as component
import deluge.configmanager
from deluge.core.rpcserver import export
from localbff.LocalBitTorrentFileFinder import LocalBitTorrentFileFinder 
from localbff.ContentDirectoryCache import getAllFilesInContentDirectories

DEFAULT_PREFS = {
    "test":"NiNiNi"
}

class Core(CorePluginBase):
    def enable(self):
        self.config = deluge.configmanager.ConfigManager("localbff.conf", DEFAULT_PREFS)
        #self.cache = getAllFilesInContentDirectories(self.config['contentDirectories'])

    def disable(self):
        pass

    def update(self):
        pass

    @export
    def set_config(self, config):
        """Sets the config dictionary"""
        for key in config.keys():
            self.config[key] = config[key]
        self.config.save()

    @export
    def get_config(self):
        """Returns the config dictionary"""
        return self.config.config

    @export
    def update_cache(self, content_directories):
        #self.cache = getAllFilesInContentDirectories(content_directories)
        pass


    @export
    def add_new_metafile(self, torrent_id):
        # Determine if potential matches exist.
        #  If no potential matches exist, proceed with the default action.
        pass


    @export
    def find_potential_matches(self, torrent_id):
        # Grab the torrent from the torrent manager

        # Get the filenames and file sizes of each payload file

        # Iterate through these files, and query the cache for potential
        #  matches.

        # Return the number of potential matches for each payload file.
        return {'a/payload/file/': 4}


    @export
    def relink(self, torrent_id):
        """Relink this torrent ID to a positive match if one exists"""
        # 1. Find the potential matches for this file.
        #     If no matches are found, perform the default action.

        # 2. Build the LocalBitTorrentFileFinder object.

        # 3. Query for the positive match for each potential match.
        #      If there is a match, reconnect the metafile.
        #      Otherwise, do nothing.

        # 4. If at least one positive match is not found, perform default
        #     default action.
        import datetime
        core = component.get("Core")
        current_torrent = core.torrentmanager.torrents[torrent_id]

        with open("/home/evil/localbff_core_relink", "a") as f:
          f.write("Time: {0}\n".format(datetime.datetime.now()))
          f.write("torrent_id: {0}\n".format(torrent_id))
          print("torrent_id: {0}".format(torrent_id))

          f.write("filename := {0}".format(current_torrent.filename))
          print("filename := {0}".format(current_torrent.filename))

          f.write("get_files() := {0}".format(current_torrent.get_files()))
          print("get_files() := {0}".format(current_torrent.get_files()))
          current_torrent.write_torrentfile()

          import os
          metafile_dir = os.path.join(
            deluge.configmanager.get_config_dir(),
            "state"
          )
          metafile_path = os.path.join(
            metafile_dir,
            "{0}.torrent".format(torrent_id)
          )
          if os.path.isfile(metafile_path):
            f.write('Torrent file written to {0}'.format(metafile_path))
            print("Torrent file written to {0}".format(metafile_path))
          else:
            f.write("Something went wrong with writing metafile out")
            print("Something went wrong with writing metafile out")

          f.write("Torrent info: {0}".format(current_torrent.torrent_info))
          print("Torrent info: {0}".format(current_torrent.torrent_info))
          f.write("{0}".format(dir(current_torrent.torrent_info)))
          print("{0}".format(dir(current_torrent.torrent_info)))
        return 42

