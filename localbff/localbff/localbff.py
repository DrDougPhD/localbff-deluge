import os
import logging
log = logging.getLogger(__name__)

class LocalBitTorrentFileFinder:
  def __init__(self, metafile=None, fastVerification=False):
    # There are two ways of veriying if a potential match is a postive match:
    #  Thorough := check all piece hashes that contribute to a file
    #  Fast := check only one piece hash that contributes to a file.
    self.doFastVerification = fastVerification

    log.info("LocalBitTorrentFileFinder initialized")
    log.info("  Fast verification => {0}".format(fastVerification))
    
    self.metafile = metafile
    self.files = None
    self.percentageMatched = 0.0


  def connectPayloadFileToPotentialMatches(self, fileIndex, potentialMatches):
    log.info("Connecting payload file to potential matches")
    if self.files is None:
      self.files = self.metafile.files

    payloadFile = self.files[fileIndex]
    log.info("For {0}".format(payloadFile))
    payloadFile.possibleMatches = potentialMatches
      
    log.info("  Number of Possible matches => {0}".format(len(payloadFile.possibleMatches)))
    log.info("  Possible file matches => {0}".format("\n    ".join(payloadFile.possibleMatches)))
    
    log.debug("Filesize-based match reduction of possible matches complete!")

 
  def positivelyMatchFilesInMetafileToPossibleMatches(self):
    log.info("Matching files in the file system to files in metafile")
    
    for piece in self.metafile.pieces:
      piece.findMatch(fastVerification=self.doFastVerification)
      if piece.isVerified:
        newPercentageAdded = (float(piece.size)/self.metafile.payloadSize)*100
        log.debug("Updating percentage stats => +" + str(newPercentageAdded) + "%")
        self.percentageMatched += newPercentageAdded
      log.debug("~"*80)
    log.info("Percentage of Metafile matched => " + str(self.percentageMatched) + "%")

    for file in self.files:
      log.info("FILE METADATA => " + file.getPathFromMetafile())
      log.info(" STATUS       => " + file.status)
      if file.status == "MATCH_FOUND":
        log.info(" MATCH PATH   => " + file.getMatchedPathFromContentDirectory())


  def createPayloadDirectoryStructure(self, directory):
    """For the directory structure outlined in the metafile, there may be
    other directories that need to be created in order to properly relink
    this metafile to its lost payload. This function will create that
    directory structure, allowing for the symbolic links to be created
    later."""
    has_directories = (
      1 != len(self.files) or
      os.path.dirname(self.files[0].getPathFromMetafile()) != self.files[0].getPathFromMetafile()
    )
    if has_directories:
      log.debug("Metafile is multi-file. Creating directories.")
      # If the metafile is a single-file metafile, then no directories
      #  need to be created. However, if it is multifile, then at least
      #  one directory will need to be created.
      for f in self.files:
        # Test if the directory already exists. If not, create it.
        relative_dir = os.path.dirname(f.getPathFromMetafile())
        abs_path = os.path.join(
          directory,
          relative_dir
        )
        log.debug("Making directory {0}".format(abs_path))
        os.makedirs(abs_path)

    else:
      log.debug("Metafile is single-file. No directories to be made.")


  def createPayloadSymbolicLinks(self, directory):
    """Assuming the directory structure of the payload has already been
    created, this function will create the symbolic links for those files
    that have positive matches found."""
    for f in self.files:
      if f.status == 'MATCH_FOUND':
        actual_file = f.getMatchedPathFromContentDirectory()
        relative_path = f.getPathFromMetafile()
        abs_path = os.path.join(
          directory,
          relative_path
        )

        # Make the symbolic link
        # NOTE: this won't work with Windows. Maybe try this for Windows: http://stackoverflow.com/a/1447651/412495
        log.info("Creating link: {0} => {1}".format(abs_path, actual_file))
        os.symlink(actual_file, abs_path)

      else:
        log.info("Skipping linking of {0}".format(f.getPathFromMetafile()))


  def relink(self, directory):
    """Create the directory structure and the symbolic link structure for
    the current metafile in the provided directory."""
    self.createPayloadDirectoryStructure(directory)
    self.createPayloadSymbolicLinks(directory)

