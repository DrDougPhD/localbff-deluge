import sqlite3
import logging
import os
from StringIO import StringIO

log = logging.getLogger(__name__)


def load(dirs, persistent_path=None):

    # Test if the cache exists on disk, and load it to memory.
    #  From here: http://stackoverflow.com/a/10856450
    if persistent_path and os.path.exists(persistent_path):
      # The cache already exists on disk, so load it into memory.
      log.debug("Cache already exists on disk. Loading into memory.")
      file_con = sqlite3.connect(persistent_path)
      tempfile = StringIO()
      for line in file_con.iterdump():
        l = "{0}\n".format(line)
        tempfile.write(l)
      file_con.close()
      tempfile.seek(0)

      # Create a database in memory and import from tempfile
      db = sqlite3.connect(":memory:")
      db.cursor().executescript(tempfile.read())
      db.commit()
      db.row_factory = sqlite3.Row

      return ContentDirectoryCache(db=db, save_to=persistent_path)

    else:
      # The sqlite3 file db does not exist, a new database will need
      #  to be created.
      log.debug("A new cache will need to be built by walking the disk.")
      cache = ContentDirectoryCache(save_to=persistent_path)

      # Iterate through the provided directories, and add them to the
      #  cache.
      for d in dirs:
        cache.addDirectory(d)

      return cache


def walkDirectoriesForFiles(*contentDirectories):
  fileInfoFromContentDirectory = []

  for contentDirectory in contentDirectories:
    filesInContentDirectory = 0
    log.info("Collecting all files in content directory => {0}".format(contentDirectory))
    for root, dirs, files in os.walk(contentDirectory, onerror=errorEncounteredWhileWalking):
      for f in files:
        filesInContentDirectory += 1
        filepath = os.path.join( os.path.abspath(root), f )
      
        if os.path.exists( filepath ):
          filesize = os.path.getsize( filepath )
          absolutePath = os.path.abspath( root )
        
          fileInfo = (absolutePath, f, filesize)
          fileInfoFromContentDirectory.append( fileInfo )

        else:
          log.warning("Problem with accessing file => {0}".format(filepath))

  return fileInfoFromContentDirectory


def errorEncounteredWhileWalking( error ):
  log.warning("Error accessing path: '{0}'".format(error.filename))
  log.warning(error)
  log.warning("To fix this problem, perhaps execute the following command:")
  log.warning("# chmod -R +rx '{0}'".format(error.filename))


class ContentDirectoryCache:
  def __init__(self, save_to=None, db=None):
    log.debug("ContentDirectoryCache initialized.")

    # This class should either be instantiated with a pre-existing
    #  database, or nothing at all.
    table_def = """
      create table warez(
        absolute_path text,
        filename text,
        size int,
        PRIMARY KEY (absolute_path, filename) ON CONFLICT REPLACE
      )
    """
    if db is None:
        log.debug("No database passed in, new db to be created.")
    	self.db = sqlite3.connect(":memory:")
        cursor = self.db.cursor().execute(table_def)
        self.db.commit()

        # If a persistent path is provided, initialize the database
        #  on disk.
        if save_to is not None:
          file_db = sqlite3.connect(save_to)
          file_db.cursor().execute(table_def)
          file_db.commit()
          file_db.close()

    else:
       log.debug("Pre-existing database supplied upon instantiation.")
       self.db = db

    # Save the file path in which to persist this database to a file.
    self.persistent_path = save_to


  def getAllFilesOfSize(self, size):
    cursor = self.db.cursor()
    cursor.execute("select absolute_path, filename from warez where size = ?", (size,))
    filesWithSpecifiedSize = cursor.fetchall()
    
    log.debug("Getting all files of size {0}B => {1}".format(size, len(filesWithSpecifiedSize)))
    filenames = []
    for fileInfoRow in filesWithSpecifiedSize:
      fileDirectory = fileInfoRow[0]
      filename = fileInfoRow[1]
      filepath = os.path.join(fileDirectory, filename)

      if os.access(filepath, os.R_OK):
        log.debug("  File added => {0}".format(filepath))
        filenames.append( filepath )
      else:
        log.warning("  Cannot read file due to permissions error, ignoring: '{0}'".format(filepath))
        log.warning("  To fix this problem, perhaps execute the following command:")
        log.warning("   # chmod +r '{0}'".format(filepath))
    
    return filenames


  def addDirectory(self, new_directory):
    # If a new directory is added that is a subdirectory of a content
    #  directory already added, then the directory will be walked, and
    #  any new files will be added to the cache. So, if a user wants to
    #  forceably update only one subdirectory of their content directory,
    #  all they need to to is add that subdirectory to the list of content
    #  directories.
    log.debug("Adding {0} to cache".format(new_directory))
    files = walkDirectoriesForFiles(new_directory)

    if files:
      log.debug("Inserting files into database")
      self.db.executemany("insert into warez values (?,?,?)", files)
      self.db.commit()

      # Load the file backup with the newly added files.
      self.add_files_to_persistent_db(files)
    else:
      log.warning(
        "No files found in {0}. No potential matches will be possible from"
        " this directory.".format(new_directory)
      )


  def add_files_to_persistent_db(self, files):
    if self.persistent_path:
        log.debug("Adding {0} files to persistent db copy at {1}".format(
          len(files),
          self.persistent_path
        ))
        file_con = sqlite3.connect(self.persistent_path)
        file_con.executemany("insert into warez values (?,?,?)", files)
        file_con.commit()
        file_con.close()


  def removeDirectory(self, dir_to_remove):
    # Delete results from the database that have the directory to be removed
    #  as a prefix of their absolute path.
    log.debug("Removing {0} from cache".format(dir_to_remove))
    c = self.db.cursor()
    c.execute(
      "DELETE from warez where absolute_path LIKE ?",
      (dir_to_remove+'%',)
    )
    self.db.commit()
    log.debug("Removal of {0} complete".format(dir_to_remove))

    self.remove_files_from_dir_in_persistent_db(dir_to_remove)


  def remove_files_from_dir_in_persistent_db(dir_to_remove):
    if self.persistent_path:
        log.debug("Removing all files in {0} from persistent db copy at {1}".format(
          dir_to_remove,
          self.persistent_path
        ))
        file_con = sqlite3.connect(self.persistent_path)
        file_con.cursor().execute(
          "DELETE from warez where absolute_path LIKE ?",
          (dir_to_remove+'%',)
        )
        file_con.commit()
        file_con.close()
        log.debug("Removing complete for persistent db copy")

