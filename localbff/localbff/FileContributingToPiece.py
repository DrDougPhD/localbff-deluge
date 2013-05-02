import logging
from utils import pieceOnlyHasOneFile
from utils import fileBeginsBeforePieceAndEndsInsidePiece
from utils import fileBeginsInsidePieceAndEndsAfterPieceEnds
from utils import fileIsCompletelyHeldInsidePiece

module_logger = logging.getLogger(__name__)

def getFromMetafilePieceAndFileObjects(piece, file):
  byteInWhichFileEndsInPiece = None
  byteInWhichFileBeginsInPiece = None
  module_logger.debug("How does the file contribute to piece?")
  module_logger.debug("  " + file.__str__())
  module_logger.debug("  " + piece.__str__())
  
  if pieceOnlyHasOneFile(piece, file):
    module_logger.debug("  Status => Piece only has one file")
    byteInWhichFileBeginsInPiece = piece.streamOffset - file.streamOffset
    byteInWhichFileEndsInPiece = piece.size
  elif fileBeginsBeforePieceAndEndsInsidePiece(piece, file):
    module_logger.debug("  Status => File begins before piece and ends inside piece")
    byteInWhichFileBeginsInPiece = piece.streamOffset - file.streamOffset
    byteInWhichFileEndsInPiece = file.endingOffset - piece.streamOffset
  elif fileBeginsInsidePieceAndEndsAfterPieceEnds(piece, file):
    module_logger.debug("  Status => File begins inside of piece and ends after piece ends")
    byteInWhichFileBeginsInPiece = 0
    byteInWhichFileEndsInPiece = piece.endingOffset - file.streamOffset
  elif fileIsCompletelyHeldInsidePiece(piece, file):
    module_logger.debug("  Status => Entire file is held within piece")
    byteInWhichFileBeginsInPiece = 0
    byteInWhichFileEndsInPiece = file.size
  else:
    raise Exception
  
  fcp = FileContributingToPiece(seek=byteInWhichFileBeginsInPiece, read=byteInWhichFileEndsInPiece, referenceFile=file)

  module_logger.debug("FileContributingToPiece building complete!")
  return fcp

class FileContributingToPiece:
  def __init__(self, seek, read, referenceFile, possibleMatchPath=None):
    self.seekOffset = seek
    self.readOffset = read
    self.referenceFile = referenceFile
    self.possibleMatchPath = possibleMatchPath

    self.logger = logging.getLogger(__name__)
  
  def __repr__(self):
    return self.__str__()

  def __str__(self):
    output = __name__
    output += "\n  Metafile info: " + self.referenceFile.__str__()
    output += "\n  File substream: (Seek=" + str(self.seekOffset) + "B, Read=" + str(self.readOffset) + "B)"
    if self.possibleMatchPath:
      output += "\n  Possible match path: " + self.possibleMatchPath
    return output
  
  def getAllPossibleFilePaths(self):
    if self.referenceFile.status == "MATCH_FOUND":
      return [self.referenceFile.matchedFilePath]
    else:
      return self.referenceFile.possibleMatches
  
  def getData(self):
    data = ''
    with open(self.possibleMatchPath, 'rb') as possibleMatchedFile:
      possibleMatchedFile.seek(self.seekOffset)
      data = possibleMatchedFile.read(self.readOffset)
    
    return data
  
  def applyCurrentMatchPathToReferenceFileAsPositiveMatchPath(self):
    self.logger.debug("Applying " + self.possibleMatchPath + " to " + self.referenceFile.__str__())
    self.referenceFile.matchedFilePath = self.possibleMatchPath
  
  def updateStatus(self, status):
    if not self.referenceFile.status == "MATCH_FOUND":
      self.logger.debug("Updating file status from " + self.referenceFile.status + " to " + status)
      self.referenceFile.status = status
    else:
      self.logger.debug("A match has already been found for " + self.referenceFile.__str__())
      self.logger.debug("Not updating status.")

  def hasBeenMatched(self):
    return (self.referenceFile.status == "MATCH_FOUND")
