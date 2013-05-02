import os
import sqlite3
import logging

module_logger = logging.getLogger(__name__)

def getAllFilesInContentDirectory( contentDirectory ):
  module_logger.info("""
Walking content directory
-------------------------""")
  
  fileInfoFromContentDirectory = []
  filesInContentDirectory = 0
  
  module_logger.info("Collecting all files in content directory => " + contentDirectory)
  for root, dirs, files in os.walk( contentDirectory, onerror=errorEncounteredWhileWalking ):
    for f in files:
      filesInContentDirectory += 1
      filepath = os.path.join( os.path.abspath(root), f )
      
      if os.path.exists( filepath ):
        filesize = os.path.getsize( filepath )
        absolutePath = os.path.abspath( root )
        
        fileInfo = (absolutePath, f, filesize)
        fileInfoFromContentDirectory.append( fileInfo )
      else:
        module_logger.warning("  Problem with accessing file => " + filepath)
      
  module_logger.info("Total files in content directory => " + str(filesInContentDirectory))
  dao = ContentDirectoryDao(files=fileInfoFromContentDirectory)

  module_logger.info("Content directory walking complete!")
  return dao

def errorEncounteredWhileWalking( error ):
  module_logger.warning("Error accessing path: '" + error.filename + "'")
  module_logger.warning(error)
  module_logger.warning("To fix this problem, perhaps execute the following command:")
  module_logger.warning("# chmod -R +rx '" + error.filename + "'")

class ContentDirectoryDao:
  def __init__(self, files=None):
    self.db = sqlite3.connect(":memory:")

    self.logger = logging.getLogger(__name__)
    self.logger.debug("Creating sqlite3 db in memory")

    cursor = self.db.cursor()
    cursor.execute('''
      create table warez(
        absolute_path text,
        filename text,
        size int
      )
    ''')
    self.db.commit()
    
    if files:
      self.logger.debug("Inserting files into database")
      self.db.executemany("insert into warez values (?,?,?)", files)
      self.db.commit()
    else:
      self.logger.warning("No files found. No matches will be found D:")
  
  def getAllFilesOfSize(self, size):
    cursor = self.db.cursor()
    cursor.execute("select absolute_path, filename from warez where size = ?", (size,))
    filesWithSpecifiedSize = cursor.fetchall()
    
    self.logger.debug("Getting all files of size " + str(size) + " bytes => " + str(len(filesWithSpecifiedSize)))
    filenames = []
    for fileInfoRow in filesWithSpecifiedSize:
      fileDirectory = fileInfoRow[0]
      filename = fileInfoRow[1]
      filepath = os.path.join(fileDirectory, filename)

      if os.access(filepath, os.R_OK):
        self.logger.debug("  File added => " + filepath)
        filenames.append( filepath )
      else:
        self.logger.warning("  Cannot read file due to permissions error, ignoring: '" + filepath + "'")
        self.logger.warning("  To fix this problem, perhaps execute the following command:")
        self.logger.warning("   # chmod +r '" + filepath + "'")
    
    return filenames
