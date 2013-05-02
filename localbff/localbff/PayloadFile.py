import utils
import os
import logging
import json

module_logger = logging.getLogger(__name__)

def getPayloadFilesFromMetafileDict(metafileDict):
  module_logger.debug("Extracting file information from metafile dictionary")
  files = []
  payloadDirectory = metafileDict['info']['name'].decode('utf-8')
  
  if utils.isSingleFileMetafile(metafileDict):
    module_logger.debug('Metafile is in single-file mode')

    filename = payloadDirectory
    module_logger.debug("  Filename => " + filename)

    size = metafileDict['info']['length']
    module_logger.debug("  Filesize => " + str(size) + " Bytes")
    
    files.append( PayloadFile(path="", filename=filename, size=size, streamOffset=0) )
  
  else:
    module_logger.debug('Metafile is in multi-file mode')
    
    numberOfFiles = len(metafileDict['info']['files'])
    module_logger.debug('Total files => ' + str(numberOfFiles))
    
    currentStreamOffset = 0
    for i in range(0, numberOfFiles):
      module_logger.debug("START: Decoding file #" + str(i+1))

      currentFile = metafileDict['info']['files'][i]
      module_logger.debug("  JSON => \n" + json.dumps(currentFile, indent=2))

      path = os.path.join(payloadDirectory, *currentFile['path'][:-1])
      module_logger.debug("  Path => " + path )

      filename = currentFile['path'][-1].decode('utf-8')
      module_logger.debug("  Filename => " + filename )

      size = currentFile['length']
      module_logger.debug("  Filesize => " + str(size) )

      index = i
      streamOffset = currentStreamOffset
      module_logger.debug("  Payload offset => " + str(streamOffset) + " Bytes")
      
      files.append( PayloadFile(path=path, filename=filename, size=size, streamOffset=streamOffset, index=index+1) )
      
      module_logger.debug("END: Decoding file #" + str(i+1))
      currentStreamOffset += size
  
  module_logger.debug("File information decoding complete!")
  return files

class PayloadFile:
  def __init__(self, path, filename, size, streamOffset, index=1):
    self.path = path
    self.filename = filename
    self.size = size
    self.streamOffset = streamOffset
    self.endingOffset = streamOffset+size
    self.matchedFilePath = None
    self.status = "NOT_CHECKED"
    self.index = index

    self.logger = logging.getLogger(__name__)
  
  def __repr__(self):
    return self.__str__()

  def __str__(self):
    output =  "PayloadFile #" + str(self.index) + " => " + self.getPathFromMetafile() + ":"
    output += str(self.size) + "B"
    output += ":PayloadSubstream=(" + str(self.streamOffset) + "B, " + str(self.endingOffset) + "B)"
    output += ":Status=" + self.status
    if self.matchedFilePath:
      output += "~" + self.matchedFilePath
    return output
 
  def contributesTo(self, piece):
    fileEndingOffset = self.streamOffset + self.size
    pieceEndingOffset = piece.streamOffset + piece.size
    
    pieceIsWholelyContainedInFile = ( self.streamOffset <= piece.streamOffset and fileEndingOffset >= pieceEndingOffset )

    fileBeginsBeforePieceBegins = self.streamOffset <= piece.streamOffset
    fileEndsAfterPieceBegins = fileEndingOffset > piece.streamOffset
    
    fileBeginsInsidePiece = self.streamOffset < pieceEndingOffset
    fileEndsAfterPieceEnds = fileEndingOffset > pieceEndingOffset
    
    fileIsPartiallyContainedInPiece = (fileBeginsBeforePieceBegins and fileEndsAfterPieceBegins) or (fileBeginsInsidePiece and fileEndsAfterPieceEnds)
    
    fileBeginsAfterPieceBegins = self.streamOffset >= piece.streamOffset
    fileEndsBeforePieceEnds = fileEndingOffset <= pieceEndingOffset
    
    fileIsWholelyContainedInPiece = fileBeginsAfterPieceBegins and fileEndsBeforePieceEnds
    return pieceIsWholelyContainedInFile or fileIsWholelyContainedInPiece or fileIsPartiallyContainedInPiece
  
  def hasNotBeenMatched(self):
    return not bool( self.matchedFilePath )
  
  def getPathFromMetafile(self):
    return os.path.join(self.path, self.filename)
  
  def getMatchedPathFromContentDirectory(self):
    return self.matchedFilePath
