import os
import copy
from binascii import b2a_base64
from functools import cmp_to_key
from locale import strcoll


def isSingleFileMetafile( metafileDict ):
  return 'length' in metafileDict['info'].keys()


def prunedMetainfoDict(metainfoDict):
  pruned = copy.deepcopy(metainfoDict)
  pruned['announce'] = 'PRUNED FOR PRIVACY REASONS'
  pruned['comment'] = 'PRUNED FOR PRIVACY REASONS'
  return pruned


def isFileReadible(path):
  return os.access(path, os.R_OK)


def binToBase64(binary):
 return b2a_base64(binary)[:-1]


# From here: http://stackoverflow.com/questions/8854421/how-to-determine-if-a-path-is-a-subdirectory-of-another
def unique_path_roots(paths):
    """Given a list of paths, if one of the paths is a subdirectory of another,
       then it will not be returned. Only those paths that are unique roots
       will be returned."""
    visited = set()
    paths = list(set(paths))
    for path in sorted(paths,key=cmp_to_key(strcoll)):
        path = os.path.normcase(os.path.normpath(os.path.realpath(path)))
        head, tail = os.path.split(path)
        while head and tail:
            if head in visited:
                break
            head, tail = os.path.split(head)
        else:
            # yield path
            visited.add(path)
    return visited

