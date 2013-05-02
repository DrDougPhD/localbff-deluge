import copy
import os
from binascii import b2a_base64

def isSingleFileMetafile( metafileDict ):
  return 'length' in metafileDict['info'].keys()

def pieceOnlyHasOneFile( piece, file ):
  fileBeginsBeforePieceBegins = file.streamOffset <= piece.streamOffset
  fileEndsAfterPieceEnds = file.endingOffset >= piece.endingOffset
  return fileBeginsBeforePieceBegins and fileEndsAfterPieceEnds

def fileBeginsBeforePieceAndEndsInsidePiece(piece, file):
  fileBeginsBeforePiece = file.streamOffset < piece.streamOffset
  fileEndsInsidePiece = file.endingOffset > piece.streamOffset and file.endingOffset < piece.endingOffset
  return fileBeginsBeforePiece and fileEndsInsidePiece

def fileBeginsInsidePieceAndEndsAfterPieceEnds(piece, file):
  fileBeginsInsidePiece = file.streamOffset > piece.streamOffset and file.streamOffset < piece.endingOffset
  fileEndsAfterPieceEnds = file.endingOffset > piece.endingOffset
  return fileBeginsInsidePiece and fileEndsAfterPieceEnds

def fileIsCompletelyHeldInsidePiece(piece, file):
  fileBeginsInsidePiece = file.streamOffset >= piece.streamOffset
  fileEndsInsidePiece = file.endingOffset <= piece.endingOffset
  return fileBeginsInsidePiece and fileEndsInsidePiece

def prunedMetainfoDict(metainfoDict):
  pruned = copy.deepcopy(metainfoDict)
  pruned['announce'] = 'PRUNED FOR PRIVACY REASONS'
  pruned['comment'] = 'PRUNED FOR PRIVACY REASONS'
  return pruned

def isFileReadible(path):
  return os.access(path, os.R_OK)

def binToBase64(binary):
 return b2a_base64(binary)[:-1]
