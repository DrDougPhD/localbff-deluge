__version__ = "LocalBFF: 1 July 2013 11:52am"
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
from deluge.plugins.pluginbase import CorePluginBase
import deluge.component as component
import deluge.configmanager
from deluge.core.rpcserver import export
from common import getAllFilesInContentDirectories
from common import match
import time

#from deluge import log as deluge_logging
# This will be available soon.
# log = deluge_logging.getPluginLogger('LocalBFF')
import logging
log = logging.getLogger(__name__)
log.info(__version__)

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
DEFAULT_ACTIONS = [
  "Download Missing Payload, Seed the Rest",
  "Delete BitTorrent",
  "Pause Download"
]

class Core(CorePluginBase):
    def enable(self):
        log.info('LocalBFF enabled.')
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
        log.debug('LocalBFF configuration data set.')
        for key in config.keys():
            log.debug("config['{0}'] = {1}".format(key, config[key]))
            self.config[key] = config[key]
        self.config.save()


    @export
    def get_config(self):
        """Returns the config dictionary"""
        return self.config.config


    @export
    def add_directory(self, directory):
        """Adds a new Content Directory to the configuration"""
        log.info("New content directory added for scanning: {0}".format(directory))
        if not directory in self.config['contentDirectories']:
          self.config['contentDirectories'].append(directory)

          # Load the files in the new content directory into the cache
          self.cache.addDirectory(directory)
          self.config.save()


    @export
    def remove_directory(self, dir_to_remove):
        """Remove the directory if it exists in the configuration"""
        log.info("Content directory removed: {0}".format(dir_to_remove))
        if dir_to_remove in self.config['contentDirectories']:
          self.config['contentDirectories'].remove(dir_to_remove)
          self.cache.removeDirectory(dir_to_remove)
          self.config.save()

    @export
    def edit_directory(self, old_dir, new_dir):
        """Edit the value of the provided directory"""
        log.info("Content directory {0} renamed to {1}".format(old_dir, new_dir))
        try:
          i = self.config['contentDirectories'].index(old_dir)
          self.config['contentDirectories'][i] = new_dir
          self.cache.removeDirectory(old_dir)
          self.cache.addDirectory(new_dir)
          self.config.save()
        except:
          import sys
          import traceback
          exc_type, exc_value, exc_traceback = sys.exc_info()
          lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
          log.error(''.join('!! ' + line for line in lines))
          raise


    @export
    def set_default_action(self, default_action_id):
        """Set the ID of the default action"""
        log.info("Default action updated to {0}".format(DEFAULT_PREFS[default_action_id]))
        self.config['defaultAction'] = default_action_id
        self.config.save()

    @export
    def get_default_action(self):
        return self.config['defaultAction']

    @export
    def update_cache(self):
        log.info("Cache updating...")
        self.cache = getAllFilesInContentDirectories(self.config['contentDirectories'])
        log.info("Cache update complete")


    def add_new_metafile(self, torrent_id):
        # Determine if potential matches exist.
        #  If no potential matches exist, proceed with the default action.
        now = time.time()
        log.debug("New metafile added: {0} at {1}".format(torrent_id, now))
        torrent_manager = component.get("Core").torrentmanager
        current_torrent = torrent_manager.torrents[torrent_id]
        time_added = current_torrent.get_status(['time_added'])['time_added']
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

            log.debug("Metafile ID# {0} ignored: {1}".format(
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
                log.debug('Some files have no potential matches...')
                if self.config['defaultAction'] == 0:
                    # If the default action is set to Download, then
                    #  go ahead and attempt to relink the files. If
                    #  there are any positive matches, they will be
                    #  relinked, and the missing ones will be downloaded.
                    log.info('Default action set to Download, so attempting relink')
                    self.relink(torrent_id)

                elif self.config['defaultAction'] == 1:
                    log.info('Default action set to Deleted, so removing')
                    torrent_manager.remove(torrent_id)

                elif self.config['defaultAction'] == 2:
                    log.info('Default action set to Pause, so pausing')
                    current_torrent.pause()

            else:
                # If all of the files have potential matches, then we should
                #  automatically attempt to relink.
                log.info('All files have potential matches! Attemping a relink.')
                self.relink(torrent_id)


    @export
    def find_potential_matches(self, torrent_id):
        log.debug("Finding potential matches for Torrent ID#{0}".format(torrent_id))
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
        log.info("Relinking torrent {0}".format(torrent_id))
        torrent_manager = component.get("Core").torrentmanager
        current_torrent = torrent_manager.torrents[torrent_id]

        # Get the filenames and file sizes of each payload file
        files = current_torrent.get_files()
        potential_matches = [None for f in files]

        # Iterate through these files, and query the cache for potential
        #  matches.
        for f in files:
          potential_matches[f['index']] = self.cache.getAllFilesOfSize(f['size'])

        # 2. Call LocalBFF to match the files
        metafile_dict = {"info": deluge.bencode.bdecode(current_torrent.torrent_info.metadata())}
        log.debug("Bencoded metafile obtained. Passing on to LocalBFF.")
        from common import match 
        matcher = match(
          fastVerification=True,
          metafileDict=metafile_dict,
          potentialMatches=potential_matches
        )
        log.info("Searching for positive matches complete!")

        # If all files are positively matched, then the torrent should be
        #  relinked and set to a seeding state.
        all_files_positively_matched = True
        for f in matcher.files:
          if f.status != "MATCH_FOUND":
            all_files_positively_matched = False

        # If there is some file that is not fully matched, then we must check
        #  the default action as specified by the user.
        if all_files_positively_matched or self.config['defaultAction'] == 0:
          if all_files_positively_matched:
            log.info("Positive matches for all files!")
          else:
            log.info("Some files had no positive matches."
                     " Seeding the matches, downloading the rest")

          log.info("Pausing torrent for relinking...")
          current_torrent.pause()
          #matcher.relink(current_torrent.get_options()['download_location'])
          self.move_storage_and_relink(current_torrent, matcher)
          
          log.info("Forcing recheck...")
          current_torrent.force_recheck()
          log.info("Resuming torrent...")
          current_torrent.resume()

        elif self.config['defaultAction'] == 1:
          log.info("Some files had no positive matches. Deleting torrent.")
          torrent_manager.remove(torrent_id)

        elif self.config['defaultAction'] == 2:
          log.info("Some files had no positive matches. Pausing torrent.")
          current_torrent.pause()


    def move_storage_and_relink(self, current_torrent, matcher):
        # There may be actual files that are stored all throughout the user's
        #  system, such as:
        #    payload/file1 => /mnt/stuff/FILE_1.txt
        #    payload/file2 => /media/big_ass_hd/fileTWO
        # In order to relink these files, move_storage() will need to be called
        #  with '/' and the directory in which to store, since this is the
        #  deepest common subdirectory of the two files.
        # NOTE: this may be a problem for Windows users, who store files on
        #  one hard drive (C:/ drive) and another hard drive (D:/ drive).

        common_subdirectory = os.path.split(os.path.commonprefix(
            [f.getMatchedPathFromContentDirectory() for f in matcher.files if f.status == "MATCH_FOUND"]
        ))[0]
        
        # If a Windows user has one file on C:/, and another file on D:/,
        #  then common_subdirectory will be empty.
        if common_subdirectory:
            # Move the storage location of the current torrent to the common
            #  subdirectory.
            current_torrent.move_storage(common_subdirectory)

            # Each file in the current torrent must now be reconnected if
            #  a positive match was found.
            rename_struct = []
            i = 0
            for f in matcher.files:
                if f.status == "MATCH_FOUND":
                    rename_struct.append((i, f.getMatchedPathFromContentDirectory()))
                i += 1

            # Try/Catch statement is needed around here. If the file cannot
            #  be moved, and error will occur.
            self.rename(current_torrent, rename_struct, common_subdirectory)


    def rename(self, current_torrent, matches, download_location):
        renaming_struct = []
        rel_path_index = len(download_location)+1
        for index, match in matches:
          # A call to current_torrent.rename_file() requires the new relative
          #  path of the payload file. Since matched_path may be on some
          #  other hard drive, a relative path from the root/download path
          #  of the torrent needs to be constructed and fed into rename_file()
          rel_path = match[rel_path_index:]
          print("Actual path   := {0}".format(match))
          print("Relative path := {0}".format(rel_path))
          renaming_struct.append((index, rel_path))

          # For some reason, renaming of a payload file will be rejected if
          #  the file exists. So let's move the found file so it disappears.
          log.debug("Moving {0} to {1}".format(match, match + "_localbff_tmp_move"))
          os.rename(
            match,
            match + "_localbff_tmp_move"
          )

        # Apply the renamings and force a recheck on the torrent
        log.debug("Connecting metafile to positive matches... {0}".format(renaming_struct))
        current_torrent.rename_files(renaming_struct)

        # Since the files were moved temporarily to allow for renaming,
        #  they must be moved back before the force recheck is executed.
        for i, match in matches:
            log.debug("Moving back to {0}".format(match))
            os.rename(
              match + "_localbff_tmp_move",
              match
            )
