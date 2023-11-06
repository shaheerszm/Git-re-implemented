import zlib
import hashlib
import os
import sys

from icecream import ic

from gitRepo import repo_file


class GitObject(object):
    def __init__(self, data=None):
        if data is not None:
            self.deserialize(data)
        else:
            self.init()

    # this func must be implemented by subclasses
    # read the object's contents from self.data and convert it into meaningful represenation
    def serialize(self, repo):
        raise Exception("Unimplemented")

    def deserialize(self, data):
        raise Exception("Unimplemented")

    def init(self):
        pass


class GitBlob(GitObject):
    fmt = b"blob"

    def serialize(self):
        return self.blobdata

    def deserialize(self, data):
        self.blobdata = data


# read object SHA from git repository repo
# return a git object whose type varies
def object_read(repo, sha):
    path = repo_file(repo, "objects", sha[0:2], sha[2:])

    ic(path)
    if not os.path.isfile(path):
        return None

    with open(path, "rb") as f:
        raw = zlib.decompress(f.read())

        # read object type
        x = raw.find(b" ")
        fmt = raw[0:x]

        # read and validate object size
        y = raw.find(b"\x00", x)
        size = int(raw[x:y].decode("ascii"))
        if size != len(raw) - y - 1:
            raise Exception("Malformed object {0}: bad length".format(sha))

        # pick constructor
        match fmt:
            case b"commit":
                c = GitCommit
            case b"tree":
                c = GitTree
            case b"tag":
                c = GitTag
            case b"blob":
                c = GitBlob
            case _:
                raise Exception(
                    "Unknown type {0} for object {1}".format(fmt.decode("ascii"), sha)
                )

        # call constructor and return object
        return c(raw[y + 1 :])


# serialize object data
def object_write(obj, repo=None):
    data = obj.serialize()

    # add header and compute hash
    result = obj.fmt + b" " + str(len(data)).encode() + b"\x00" + data
    sha = hashlib.sha1(result).hexdigest()

    # compute path
    if repo:
        path = repo_file(repo, "objects", sha[0:2], sha[2:], mkdir=True)
        if not os.path.exists(path):
            with open(path, "wb") as f:
                f.write(zlib.compress(result))
    return sha


def object_find(repo, name, fmt=None, follow=True):
    return name


def cat_file(repo, obj, fmt=None):
    obj = object_read(repo, object_find(repo, obj, fmt=fmt))

    assert obj
    sys.stdout.buffer.write(obj.serialize())


# hash object and write to repo if provided
# fd is file descriptor
def object_hash(fd, fmt, repo=None):
    data = fd.read()

    # choose constructor according to fmt
    match fmt:
        case b"commit":
            obj = GitCommit(data)
        case b"tree":
            obj = GitTree(data)
        case b"tag":
            obj = GitTag(data)
        case b"blob":
            obj = GitBlob(data)
        case _:
            raise Exception("Unknown type %s!" % fmt)
    return object_write(obj, repo)
