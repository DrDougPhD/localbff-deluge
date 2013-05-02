import BitTorrentMetafile
import logging

class LocalBitTorrentFileFinder:
  def __init__(self, metafilePath, dao, fastVerification=False):
    self.metafilePath = metafilePath
    self.doFastVerification = fastVerification

    self.logger = logging.getLogger(__name__)
    self.logger.info("LocalBitTorrentFileFinder initialized")
    self.logger.info("  Metafile path     => " + metafilePath)
    self.logger.info("  Fast verification => " + str(fastVerification))
    
    self.metafile = None
    self.dao = dao
    self.files = None
    self.percentageMatched = 0.0
  
  def processMetafile(self):
    self.logger.info("""
Processing metainfo file
------------------------""")
    
    self.metafile = BitTorrentMetafile.getMetafileFromPath(self.metafilePath)
  
  def connectFilesInMetafileToPossibleMatchesInContentDirectory(self):
    self.logger.info("""
Finding all file system files that match by size
------------------------------------------------""")
    self.files = self.metafile.files
    
    for payloadFile in self.files:
      self.logger.info("For " + payloadFile.__str__())
      payloadFile.possibleMatches = self.dao.getAllFilesOfSize( payloadFile.size )
      
      self.logger.info("  Number of Possible matches => " + str(len(payloadFile.possibleMatches)))
      self.logger.info("  Possible file matches => " + "\n    ".join(payloadFile.possibleMatches))
      self.logger.info("~"*80)
    
    self.logger.debug("Filesize-based match reduction of possible matches complete!")
  
  def positivelyMatchFilesInMetafileToPossibleMatches(self):
    self.logger.info("""
Matching files in the file system to files in metafile
------------------------------------------------------""")
    
    for piece in self.metafile.pieces:
      piece.findMatch(fastVerification=self.doFastVerification)
      if piece.isVerified:
        newPercentageAdded = (float(piece.size)/self.metafile.payloadSize)*100
        self.logger.debug("Updating percentage stats => +" + str(newPercentageAdded) + "%")
        self.percentageMatched += newPercentageAdded
      self.logger.debug("~"*80)
    self.logger.info("Percentage of Metafile matched => " + str(self.percentageMatched) + "%")

    for file in self.files:
      self.logger.info("FILE METADATA => " + file.getPathFromMetafile())
      self.logger.info(" STATUS       => " + file.status)
      if file.status == "MATCH_FOUND":
        self.logger.info(" MATCH PATH   => " + file.getMatchedPathFromContentDirectory())

