#
# common.py
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

def get_resource(filename):
    import pkg_resources, os
    return pkg_resources.resource_filename("localbff", os.path.join("data", filename))
    
# Due to weird importing issues that I have no time to investigate, the whole of
#  the LocalBFF library is stored below.


###############################################################################
### utils.py
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
### utils.py
###############################################################################


###############################################################################
### ContentDirectoryCache.py
import os
import sqlite3
import logging

module_logger = logging.getLogger(__name__)

def getAllFilesInContentDirectories( contentDirectories ):
  print("Loading cache...")
  module_logger.info("""
Walking content directory
-------------------------""")
  
  fileInfoFromContentDirectory = []

  for contentDirectory in contentDirectories:
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
  dao = ContentDirectoryCache(files=fileInfoFromContentDirectory)

  module_logger.info("Content directory walking complete!")
  return dao

def errorEncounteredWhileWalking( error ):
  module_logger.warning("Error accessing path: '" + error.filename + "'")
  module_logger.warning(error)
  module_logger.warning("To fix this problem, perhaps execute the following command:")
  module_logger.warning("# chmod -R +rx '" + error.filename + "'")

class ContentDirectoryCache:
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
### ContentDirectoryCache.py
###############################################################################


###############################################################################
### PayloadFile.py
import os
import json

def getPayloadFilesFromMetafileDict(metafileDict):
  module_logger.debug("Extracting file information from metafile dictionary")
  files = []
  payloadDirectory = metafileDict['info']['name'].decode('utf-8')
  
  if isSingleFileMetafile(metafileDict):
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
### PayloadFile.py
###############################################################################


###############################################################################
### FileContributingToPiece.py
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
### FileContributingToPiece.py
###############################################################################


###############################################################################
### AllContributingFilesToPiece.py
import itertools
from hashlib import sha1

class AllContributingFilesToPiece:
  def __init__(self, listOfContributingFiles=None):
    self.listOfContributingFiles = listOfContributingFiles
    self.combinationProducesPositiveHashMatch = None
    self.logger = logging.getLogger(__name__)
  
  def addContributingFile(self, newFile):
    if self.listOfContributingFiles == None:
      self.listOfContributingFiles = []
    
    self.listOfContributingFiles.append(newFile)
  
  def getNumberOfFiles(self):
    return len(self.listOfContributingFiles)
  
  def findCombinationThatMatchesReferenceHash(self, hash):
    cartesianProductOfPossibleFilePathMatches = self.buildCartesianProductOfPossibleFilePathMatches()
    
    self.logger.debug("Processing through all possible file path combinations...")
    self.logger.debug("  Worst-case scenario of all combinations to process: " + str( self.getCardinalityOfCartesianProductOfAllPossibleCombinations() ))
    self.logger.debug("  Files contributing to piece => " + str( self.getNumberOfFiles() ))
    
    for combination in cartesianProductOfPossibleFilePathMatches:
      self.logger.debug("    Checking combination => " + "\n      ".join(combination) )
      self.applyCombinationToContributingFiles(combination)

      self.logger.debug("      Building up piece from possible file combination")
      data = self.getData()
      computedHash = sha1(data).digest()
      self.logger.debug("      Computed hash for data => " + binToBase64(computedHash))
      
      self.combinationProducesPositiveHashMatch = (computedHash == hash)
      
      if self.combinationProducesPositiveHashMatch:
        self.logger.debug("      Combination found! Ending search now.")
        self.updateReferenceFilesWithAppropriateMatchedPaths()
        self.updateStatusOfReferenceFiles("MATCH_FOUND")
        break
      else:
        self.logger.debug("      Combination does not match :( moving on to next combination")
        self.logger.debug("~"*80)
        self.updateStatusOfReferenceFiles("CHECKED_WITH_NO_MATCH")
  
  def buildCartesianProductOfPossibleFilePathMatches(self):
    listOfListOfFilePaths = []
    for contributingFile in self.listOfContributingFiles:
      listOfListOfFilePaths.append(contributingFile.getAllPossibleFilePaths())
    
    cartesianProduct = itertools.product(*listOfListOfFilePaths)
    return cartesianProduct
  
  def getCardinalityOfCartesianProductOfAllPossibleCombinations(self):
    cardinality = 1
    for contributingFile in self.listOfContributingFiles:
      cardinality *= len(contributingFile.referenceFile.possibleMatches)
    
    return cardinality
  
  def applyCombinationToContributingFiles(self, combination):
    for path, contributingFile in zip(combination, self.listOfContributingFiles):
      contributingFile.possibleMatchPath = path
  
  def getData(self):
    data = ''
    for contributingFile in self.listOfContributingFiles:
      data += contributingFile.getData()
    return data
  
  def updateReferenceFilesWithAppropriateMatchedPaths(self):
    for contributingFile in self.listOfContributingFiles:
      contributingFile.applyCurrentMatchPathToReferenceFileAsPositiveMatchPath()
  
  def updateStatusOfReferenceFiles(self, status):
    for contributingFile in self.listOfContributingFiles:
      contributingFile.updateStatus(status)

  def doAllContributingFilesHaveAtLeastOnePossibleMatch(self):
    return (self.getCardinalityOfCartesianProductOfAllPossibleCombinations() > 0)

  def haveBeenPositivelyMatched(self):
    for contributingFile in self.listOfContributingFiles:
      if not contributingFile.hasBeenMatched():
        return False

    return True
### AllContributingFilesToPiece.py
###############################################################################


###############################################################################
### PayloadPiece.py
def getPiecesFromMetafileDict( metafileDict, files ):
  module_logger.debug("Extracting piece information from metafile dictionary")

  payloadSize = getPayloadSizeFromMetafileDict(metafileDict)
  module_logger.debug('  Payload size => ' + str(payloadSize) + ' Bytes')
  
  hashes = getHashesFromMetafileDict(metafileDict)
  
  pieceSize = getPieceSizeFromDict(metafileDict)
  module_logger.debug('  Piece size => ' + str(pieceSize) + " Bytes")

  finalPieceSize = getFinalPieceSizeFromDict(metafileDict)
  module_logger.debug("  Final piece size => " + str(finalPieceSize) + " Bytes")

  pieces = []
  streamOffset = 0
  numberOfPieces = getNumberOfPiecesFromDict(metafileDict)
  module_logger.debug("  Number of pieces => " + str(numberOfPieces))

  module_logger.debug("  Initializing list of PayloadPieces")
  for pieceIndex in range(numberOfPieces-1):
    module_logger.debug("Constructing piece #" + str(pieceIndex+1))
    piece = PayloadPiece(size=pieceSize, hash=hashes[pieceIndex], streamOffset=streamOffset, index=pieceIndex+1)
    piece.setContributingFilesFromAllFiles(files)
    module_logger.debug(piece.__str__())
    
    pieces.append(piece)
    streamOffset += pieceSize
    module_logger.debug("~"*80)

  module_logger.debug("Constructing piece #" + str(numberOfPieces))
  finalPiece = PayloadPiece(size=finalPieceSize, hash=hashes[-1], streamOffset=streamOffset, index=numberOfPieces)
  finalPiece.setContributingFilesFromAllFiles(files)
  module_logger.debug(finalPiece.__str__())

  pieces.append(finalPiece)

  module_logger.debug("Piece information decoding complete!")
  return pieces

def getPayloadSizeFromMetafileDict( metafileDict ):
  if isSingleFileMetafile(metafileDict):
    return metafileDict['info']['length']
  
  else:
    payloadSize = 0
    for f in metafileDict['info']['files']:
        payloadSize += f['length']
    return payloadSize

def getHashesFromMetafileDict(metafileDict):
  concatenatedHashes = metafileDict['info']['pieces']
  return splitConcatenatedHashes(concatenatedHashes)

def splitConcatenatedHashes(concatenatedHashes):
  SHA1_HASH_LENGTH = 20
  return [concatenatedHashes[start:start+SHA1_HASH_LENGTH] for start in range(0, len(concatenatedHashes), SHA1_HASH_LENGTH)]

def getPieceSizeFromDict(metafileDict):
  return metafileDict['info']['piece length']

def getFinalPieceSizeFromDict(metafileDict):
  return getPayloadSizeFromMetafileDict(metafileDict) % getPieceSizeFromDict(metafileDict)

def getNumberOfPiecesFromDict(metafileDict):
  return len(getHashesFromMetafileDict(metafileDict))

class PayloadPiece:
  def __init__(self, size, streamOffset, hash, index):
    self.size = size
    self.streamOffset = streamOffset
    self.endingOffset = streamOffset+size
    self.hash = hash
    self.b64_hash = binToBase64(hash)
    self.index = index
    self.contributingFiles = AllContributingFilesToPiece()
    self.isVerified = False

    self.logger = logging.getLogger(__name__)
  
  def __repr__(self):
    return self.__str__()

  def __str__(self):
    output = "PayloadPiece #" + str(self.index) + ":(" + str(self.streamOffset) + "B, " + str(self.endingOffset) + "B) "
    output += "(HASH=" + self.b64_hash + ")"
    return output
  
  def setContributingFilesFromAllFiles(self, allFiles):
    self.logger.debug("START: Finding all files contributing to " + self.__str__())
    for payloadFile in allFiles:
      if payloadFile.contributesTo(self):
        contributingFile = getFromMetafilePieceAndFileObjects(piece=self, file=payloadFile)
        self.contributingFiles.addContributingFile( contributingFile )

    self.logger.debug("END: Finding all files contributing to " + self.__str__())

  def findMatch(self, fastVerification):
    if self.isVerifiable():
      doNotContinueWithMatch = (
        fastVerification and self.contributingFiles.haveBeenPositivelyMatched()
      )
      if doNotContinueWithMatch:
        self.logger.debug("All contributing files have been verified for " + self.__str__())
        self.logger.debug("Skipping verification.")
        self.isVerified = True
      else:
        self.logger.debug("Finding all matched files for " + self.__str__())
        self.contributingFiles.findCombinationThatMatchesReferenceHash( hash=self.hash )
        self.isVerified = self.contributingFiles.combinationProducesPositiveHashMatch
    else:
      self.contributingFiles.updateStatusOfReferenceFiles('UNVERIFIABLE')
      self.logger.debug(self.__str__() + " is not verifiable :(")

  def isVerifiable(self):
    return self.contributingFiles.doAllContributingFilesHaveAtLeastOnePossibleMatch()
### PayloadPiece.py
###############################################################################


###############################################################################
### BitTorrentMetafile.py
import os
import bencode
import json

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
  module_logger.debug("Decoding metafile into python dictionary")
  metainfoDict = bencode.bdecode( bencodedData )

  pruned = prunedMetainfoDict(metainfoDict)
  module_logger.debug('Decoded metainfo content =>\n' +
    json.dumps(pruned, indent=2, ensure_ascii=False))

  return getMetafileFromDict( pruned )

def getMetafileFromDict( metafileDict ):
  module_logger.debug("Converting metafile dictionary to BitTorrentMetafile object")
  files = getPayloadFilesFromMetafileDict( metafileDict )
  pieces = getPiecesFromMetafileDict( metafileDict, files )
  pieceSize = getPieceSizeFromDict(metafileDict)
  finalPieceSize = getFinalPieceSizeFromDict(metafileDict)
  numberOfPieces = getNumberOfPiecesFromDict(metafileDict)
  payloadSize = getPayloadSizeFromMetafileDict( metafileDict )
  
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
### BitTorrentMetafile.py
###############################################################################


###############################################################################
### LocalBitTorrentFileFinder.py
class LocalBitTorrentFileFinder:
  def __init__(self, metafilePath, fastVerification=False):
    self.metafilePath = metafilePath
    self.doFastVerification = fastVerification

    self.logger = logging.getLogger(__name__)
    self.logger.info("LocalBitTorrentFileFinder initialized")
    self.logger.info("  Metafile path     => " + metafilePath)
    self.logger.info("  Fast verification => " + str(fastVerification))
    
    self.metafile = None
    self.files = None
    self.percentageMatched = 0.0
  
  def processMetafile(self):
    self.logger.info("""
Processing metainfo file
------------------------""")
    
    self.metafile = getMetafileFromPath(self.metafilePath)

  def connectPayloadFileToPotentialMatches(self, fileIndex, potentialMatches):
    self.logger.info("""
Connecting payload file to potential matches
--------------------------------------------""")
    if self.files is None:
      self.files = self.metafile.files

    payloadFile = self.files[fileIndex]
    self.logger.info("For " + payloadFile.__str__())
    payloadFile.possibleMatches = potentialMatches
      
    self.logger.info("  Number of Possible matches => " + str(len(payloadFile.possibleMatches)))
    self.logger.info("  Possible file matches => " + "\n    ".join(payloadFile.possibleMatches))
    self.logger.info("~"*80)
    
    self.logger.debug("Filesize-based match reduction of possible matches complete!")


  def connectFilesInMetafileToPossibleMatchesInContentDirectory(self):
    self.logger.info("""
Finding all file system files that match by size
------------------------------------------------""")
    
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


def match(fastVerification, metafilePath, potentialMatches):
  finder = LocalBitTorrentFileFinder(metafilePath, fastVerification)
  finder.processMetafile()
  
  i = 0
  for f in potentialMatches:
    finder.connectPayloadFileToPotentialMatches(i, f)
    i += 1

  finder.positivelyMatchFilesInMetafileToPossibleMatches()

  i = 0
  positive_matches = [None for f in potentialMatches]
  for f in finder.files:
    if f.status == 'MATCH_FOUND':
      positive_matches[i] = f.getMatchedPathFromContentDirectory()
    i += 1

  return positive_matches
### LocalBitTorrentFileFinder.py
###############################################################################
