import itertools
import utils
from hashlib import sha1
import logging

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
      self.logger.debug("      Computed hash for data => " + utils.binToBase64(computedHash))
      
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
