import logging
from utils import prunedMetainfoDict
import PayloadFile
import PayloadPiece
import json
module_logger = logging.getLogger(__name__)

def getMetafileFromPath( metafilePath ):
  module_logger.info("Loading metafile from URI " + metafilePath)
  try:
    with open( metafilePath, 'rb' ) as metafile:
      bencodedData = metafile.read()
      module_logger.debug("File read successfully")
    return getMetafileFromBencodedData( bencodedData )

  except IOError as e:
    module_logger.critical('Metafile is not readible, aborting program.')
    module_logger.critical('Perhaps change the file permissions on "' + metafilePath + '"?')
    module_logger.critical(' # chmod +r "' + metafilePath + '"')
    raise e


def getMetafileFromBencodedData( bencodedData ):
  import bencode
  module_logger.debug("Decoding metafile into python dictionary")
  metainfoDict = bencode.bdecode( bencodedData )

  pruned = prunedMetainfoDict(metainfoDict)
  module_logger.debug('Decoded metainfo content =>\n{0}'.format(
    json.dumps(pruned, indent=2, ensure_ascii=False)
  ))

  module_logger.debug("Decoding metafile dictionary")
  return getMetafileFromDict( pruned )


def getMetafileFromDict( metafileDict ):
  module_logger.debug("Converting metafile dictionary to BitTorrentMetafile object")
  files = PayloadFile.getPayloadFilesFromMetafileDict( metafileDict )
  pieces = PayloadPiece.getPiecesFromMetafileDict( metafileDict, files )
  pieceSize = PayloadPiece.getPieceSizeFromDict(metafileDict)
  finalPieceSize = PayloadPiece.getFinalPieceSizeFromDict(metafileDict)
  numberOfPieces = PayloadPiece.getNumberOfPiecesFromDict(metafileDict)
  payloadSize = PayloadPiece.getPayloadSizeFromMetafileDict( metafileDict )

  metafile = BitTorrentMetafile(
    files=files,
    pieces=pieces,
    pieceSize=pieceSize, 
    finalPieceSize=finalPieceSize, 
    numberOfPieces=numberOfPieces, 
    payloadSize=payloadSize
  )
  
  module_logger.debug("Metafile decoding complete!") 
  return metafile


class BitTorrentMetafile:
  def __init__(self, files, pieces, pieceSize=None, finalPieceSize=None, numberOfPieces=None, payloadSize=None, tracker=""):
    self.files = files
    self.numberOfFiles = len(files)
    self.pieces = pieces
    self.pieceSize = pieceSize
    self.finalPieceSize = finalPieceSize
    self.numberOfPieces = numberOfPieces
    self.payloadSize = payloadSize
    self.tracker = tracker

  def __repr__(self):
    return self.__str__()

  def __str__(self):
    output = u""
    output += __name__ + "\n"
    output += "Tracker => " + self.tracker + "\n"
    output += "Payload size => " + str(self.payloadSize) + " Bytes\n"
    output += "Number of files => " + str(self.numberOfFiles) + "\n"
    
    for f in self.files:
      output += "  " + f.__str__() + "\n"
    
    output += "Number of pieces => " + str(self.numberOfPieces) + "\n"
    output += "Piece size => " + str(self.pieceSize) + " Bytes\n"
    output += "Final piece size => " + str(self.finalPieceSize) + " Bytes\n"

    for p in self.pieces:
      output += "  " + p.__str__() + "\n"
    
    return output

