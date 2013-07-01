#
# core.py
#
# Copyright (C) 2013 Doug McGeehan <doug.mcgeehan@mst.edu>
# Copyright (C) 2013 Maximilian Schroeder
# Copyright (C) 2013 Hiren Patel
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
import os
__version__ = "LocalBFF: 29 June 2013 22:22pm"
print(__version__)
print(os.path.abspath(__file__))
from deluge.log import LOG as log
from deluge.plugins.pluginbase import CorePluginBase
import deluge.component as component
import deluge.configmanager
from deluge.core.rpcserver import export
from common import getAllFilesInContentDirectories
import time

DEFAULT_PREFS = {
    "contentDirectories": [],
    "defaultAction": 0,
    "minAge": 5,  # When deluged begins execution, it will enable this plugin
                  #  and immediately being re-adding all metafiles, which
                  #  will run through this script over and over again. If all
                  #  of your metafiles are re-added, rechecked, re-searched,
                  #  etc... that can lead to a bad time and a lot of wasted
                  #  computations.
                  #  To combat this, only files that have been added within
                  #  the minAge of seconds will be run through the 
                  #  add_new_metafile function below. That way, only files
                  #  that are NEWLY added will be run through, and not files
                  #  that were previously added some time ago.
}

# Default Actions are as follows:
#   0 => Download Missing Payload, Seed the Rest
#   1 => Delete BitTorrent
#   2 => Pause Download

class Core(CorePluginBase):
    def enable(self):
        self.config = deluge.configmanager.ConfigManager("localbff.conf", DEFAULT_PREFS)
        self.cache = getAllFilesInContentDirectories(self.config['contentDirectories'])
        component.get("EventManager").register_event_handler(
            "TorrentAddedEvent",
            self.add_new_metafile
        )


    def disable(self):
        component.get("EventManager").deregister_event_handler(
            "TorrentAddedEvent",
            self.add_new_metafile
        )


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
    def add_directory(self, directory):
        """Adds a new Content Directory to the configuration"""
        print("core.add_directory('{0}')".format(directory))
        if not directory in self.config['contentDirectories']:
          self.config['contentDirectories'].append(directory)

          # Load the files in the new content directory into the cache
          self.cache.addDirectory(directory)
          self.config.save()


    @export
    def remove_directory(self, dir_to_remove):
        """Remove the directory if it exists in the configuration"""
        if dir_to_remove in self.config['contentDirectories']:
          self.config['contentDirectories'].remove(dir_to_remove)
          self.cache = getAllFilesInContentDirectories(self.config['contentDirectories'])
          self.config.save()

    @export
    def edit_directory(self, old_dir, new_dir):
        """Edit the value of the provided directory"""
        try:
          i = self.config['contentDirectories'].index(old_dir)
          self.config['contentDirectories'][i] = new_dir
          self.cache = getAllFilesInContentDirectories(self.config['contentDirectories'])
          self.config.save()
        except:
          pass

    @export
    def set_default_action(self, default_action_id):
        """Set the ID of the default action"""
        self.config['defaultAction'] = default_action_id
        self.config.save()

    @export
    def get_default_action(self):
        return self.config['defaultAction']

    @export
    def update_cache(self):
        self.cache = getAllFilesInContentDirectories(self.config['contentDirectories'])


    def add_new_metafile(self, torrent_id):
        # Determine if potential matches exist.
        #  If no potential matches exist, proceed with the default action.
        now = time.time()
        print("New metafile added: {0} at {1}".format(torrent_id, str(now)))
        torrent_manager = component.get("Core").torrentmanager
        current_torrent = torrent_manager.torrents[torrent_id]
        print("Status := ")
        print(current_torrent.get_status({}))
        print("is_seed     := {0}".format(current_torrent.get_status(['is_seed'])['is_seed']))
        print("is_finished := {0}".format(current_torrent.get_status(['is_finished'])['is_finished']))
        time_added = current_torrent.get_status(['time_added'])['time_added']
        print("time_added  := {0}".format(time_added))
        print("            := {0} seconds after added".format(now - time_added))
        # ['is_finished', 'is_seed', 'paused',
        #  'time_added': 1372535519.22622 ]
        # is_in_seeding_state = current_torrent.get_status(['is_seed'])['is_seed']

        # If a metafile is already in a seeding state, or is
        #  already finished, or is older than minAge in seconds,
        #  then it will be skipped. Otherwise, it will be run
        #  through.
        new_metafile_statuses = current_torrent.get_status(
            ['is_seed', 'is_finished', 'time_added']
        )
        is_metafile_older_than_minAge = (
            now > self.config['minAge'] + new_metafile_statuses['time_added']
        )
        if (new_metafile_statuses['is_seed'] or new_metafile_statuses['is_finished'] or is_metafile_older_than_minAge):
            if new_metafile_statuses['is_seed']:
              reason_for_ignoring_metafile = "Payload is already seeding."
            elif new_metafile_statuses['is_finished']:
              reason_for_ignoring_metafile = "Payload is finished downloading."
            elif is_metafile_older_than_minAge:
              reason_for_ignoring_metafile = (
                  "Metafile was added more than {0} seconds ago.".format(
                      self.config['minAge']
                  )
              )

            print("Metafile ID# {0} ignored: {1}".format(
                torrent_id, reason_for_ignoring_metafile
            ))

        else:
            # Get the filenames and file sizes of each payload file
            files = current_torrent.get_files()

            # Iterate through these files, and query the cache for potential
            #  matches.
            some_files_have_no_potential_matches = False
            for f in files:
                potential_matches = self.cache.getAllFilesOfSize(f['size'])
                num_pot_matches = len(potential_matches)
                if num_pot_matches == 0:
                    some_files_have_no_potential_matches = True

            if some_files_have_no_potential_matches:
                print('Some files have no potential matches...')
                if self.config['defaultAction'] == 0:
                    # If the default action is set to Download, then
                    #  go ahead and attempt to relink the files. If
                    #  there are any positive matches, they will be
                    #  relinked, and the missing ones will be downloaded.
                    print('Default action set to Download, so attempting relink')
                    self.relink(torrent_id)

                elif self.config['defaultAction'] == 1:
                    print('Default action set to Deleted, so removing')
                    torrent_manager.remove(torrent_id)

                elif self.config['defaultAction'] == 2:
                    print('Default action set to Pause, so pausing')
                    current_torrent.pause()

            else:
                # If all of the files have potential matches, then we should
                #  automatically attempt to relink.
                print('All files have potential matches! Attemping a relink.')
                self.relink(torrent_id)

        print("#"*80)


    @export
    def find_potential_matches(self, torrent_id):
        print("find_potential_matches({0})".format(torrent_id))
        # Grab the torrent from the torrent manager
        current_torrent = component.get("Core").torrentmanager.torrents[torrent_id]

        # Get the filenames and file sizes of each payload file
        files = current_torrent.get_files()
        potential_match_data = {}
        
        # Iterate through these files, and query the cache for potential
        #  matches.
        for f in files:
            potential_matches = self.cache.getAllFilesOfSize(f['size'])
            potential_match_data[f['path']] = len(potential_matches)

        # Return the number of potential matches for each payload file.
        return potential_match_data


    @export
    def relink(self, torrent_id):
        """Relink this torrent ID to a positive match if one exists"""
        # 1. Find the potential matches for this file.
        #     If no matches are found, perform the default action.
        # Grab the torrent from the torrent manager
        print("Relinking torrent {0}".format(torrent_id))
        torrent_manager = component.get("Core").torrentmanager
        current_torrent = torrent_manager.torrents[torrent_id]

        # Get the filenames and file sizes of each payload file
        files = current_torrent.get_files()
        potential_matches = [None for f in files]

        # Iterate through these files, and query the cache for potential
        #  matches.
        for f in files:
          potential_matches[f['index']] = self.cache.getAllFilesOfSize(f['size'])

        # 2. Build the LocalBitTorrentFileFinder object.

        #######################################################################
        # The following code is a hack. It should be fixed.
        #
        #  In order to get the information stored in the metafile, it is
        #   written to the disk as a .torrent file.
        current_torrent.write_torrentfile()

        #  The absolute path of the file is then grabbed. From some naive
        #   experiments, I found out that when write_torrentfile() is called,
        #   the torrent file is written into the following directory:
        #     deluge.configmanager.get_config_dir()/state/
        #   This directory is stored in the variable metafile_dir below.
        import os
        metafile_dir = os.path.join(
            deluge.configmanager.get_config_dir(),
            "state"
        )

        #  The metafile is named TORRENT_ID.torrent, and is stored in the
        #   directory specified above.
        metafile_path = os.path.join(
          metafile_dir,
          "{0}.torrent".format(torrent_id)
        )

        # With the metafile path known, it can be passed into the match()
        #  function, which is a top-level entrance into the localbff
        #  library. I took this approach because it meant I did not have
        #  to modify much code in the localbff library to accomplish this.
        from common import match 
        positive_matches = match(
          fastVerification=True,
          metafilePath=metafile_path,
          potentialMatches=potential_matches
        )
        #
        # The hack above is stupid, but it works. I (or someone) needs
        #  to correct it.
        #######################################################################

        # If all files are positively matched, then the torrent should be
        #  relinked and set to a seeding state.
        rename_struct = []
        all_files_positively_matched = True
        i = 0
        for matched_path in positive_matches:
          if matched_path is None:
            all_files_positively_matched = False
          
          rename_struct.append((i, matched_path))
          i += 1

        if all_files_positively_matched:
          print("Positive matches for all files!")
          self._relink(current_torrent, rename_struct)

        # If there is some file that is not fully matched, then we must check
        #  the default action as specified by the user.
        elif self.config['defaultAction'] == 0:
          print("Some files had no positive matches. Seeding the matches, downloading the rest")
          # 0 corresponds to Downloading the missing while seeding the present
          positive_matches = [match for match in rename_struct if match[1] is not None]
          self._relink(current_torrent, positive_matches)

        elif self.config['defaultAction'] == 1:
          print("Some files had no positive matches. Deleting torrent.")
          torrent_manager.remove(torrent_id)

        elif self.config['defaultAction'] == 2:
          print("Some files had no positive matches. Pausing torrent.")
          current_torrent.pause()


    def _relink(self, current_torrent, matches):
        download_location = current_torrent.get_options()['download_location']

        renaming_struct = []
        for index, match in matches:
          # A call to current_torrent.rename_file() requires the new relative
          #  path of the payload file. Since matched_path may be on some
          #  other hard drive, a relative path from the root/download path
          #  of the torrent needs to be constructed and fed into rename_file()
          renamed_path = os.path.relpath(match, download_location)
          print('Match path: {0}'.format(renamed_path))
          renaming_struct.append((index, renamed_path))

          # For some reason, renaming of a payload file will be rejected if
          #  the file exists. So let's move the found file so it disappears.
          print("Moving to {0}".format(match + "_localbff_tmp_move"))
          os.rename(
            match,
            match + "_localbff_tmp_move"
          )

        # Apply the renamings and force a recheck on the torrent
        print("Pausing torrent...")
        current_torrent.pause()
        print("Renaming files... {0}".format(renaming_struct))
        current_torrent.rename_files(renaming_struct)

        # Since the files were moved temporarily to allow for renaming,
        #  they must be moved back before the force recheck is executed.
        for i, match in matches:
            print("Moving back to {0}".format(match))
            os.rename(
              match + "_localbff_tmp_move",
              match
            )

        print("Forcing recheck...")
        current_torrent.force_recheck()
        print("Resuming torrent...")
        current_torrent.resume()


