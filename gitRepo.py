import os
import configparser


class GitRepository(object):
    worktree: str
    gitdir: str
    conf = None

    def __init__(self, path, force=False):
        self.worktree = path
        self.gitdir = os.path.join(path, ".git")

        if not (force or os.path.isdir(self.gitdir)):
            raise Exception("Not a git repository %s" % path)

        # read config
        self.conf = configparser.ConfigParser()
        cf = repo_file(self, "config")

        if cf and os.path.exists(cf):
            self.conf.read([cf])
        elif not force:
            raise Exception("Config file missing.")

        if not force:
            vers = int(self.conf.get("core", "repositoryformatversion"))
            if vers != 0:
                raise Exception("Unsupported repository format version %s" % vers)


### *helper functions*


# compute path under repo's git dir
def repo_path(repo, *path) -> str:
    return os.path.join(repo.gitdir, *path)


# same as repo_path, but mkdir *path if absent if mkdir = True
def repo_dir(repo, *path, mkdir=False) -> str | None:
    path = repo_path(repo, *path)

    if os.path.exists(path):
        if os.path.isdir(path):
            return path
        else:
            raise Exception("Not a directory %s" % path)

    if mkdir:
        os.makedirs(path)
        return path
    else:
        return None


# same as repo_path, but create dirname(*path) if absent
def repo_file(repo, *path, mkdir=False) -> str | None:
    if repo_dir(repo, *path[:-1], mkdir=mkdir):
        return repo_path(repo, *path)


# create new repo at path
def repo_create(path) -> GitRepository:
    repo = GitRepository(path, True)

    # make sure path doesn't exist nor is empty dir
    if os.path.exists(repo.worktree):
        if not os.path.isdir(repo.worktree):
            raise Exception("%s is not a directory!" % path)
        if os.path.exists(repo.gitdir) and os.listdir(repo.gitdir):
            raise Exception("%s is not empty!" % path)
    else:
        os.makedirs(repo.worktree)

    assert repo_dir(repo, "branches", mkdir=True)
    assert repo_dir(repo, "objects", mkdir=True)
    assert repo_dir(repo, "refs", "tags", mkdir=True)
    assert repo_dir(repo, "refs", "heads", mkdir=True)

    # .git/description
    with open(repo_file(repo, "description"), "w") as f:
        f.write("Unnamed repository; edit this description to name the repository.\n")
    # .git/HEAD
    with open(repo_file(repo, "HEAD"), "w") as f:
        f.write("ref: refs/heads/master\n")
    # .git/config
    with open(repo_file(repo, "config"), "w") as f:
        config = repo_default_config()
        config.write(f)
    return repo


# find root of current repo, starting at current directory and recursing back to /
def repo_find(path=".", required=True) -> GitRepository | None:
    path = os.path.realpath(path)

    if os.path.isdir(os.path.join(path, ".git")):
        return GitRepository(path)

    # if function hasn't returned yet, recurse
    parent = os.path.realpath(os.path.join(path, ".."))

    # bottom case, path is root => os.path.join('/', '..') == '/'
    if parent == path:
        if required:
            raise Exception("No git directory.")
        else:
            return None

    # recursive case
    return repo_find(parent, required)


def repo_default_config():
    ret = configparser.ConfigParser()
    ret.add_section("core")
    ret.set("core", "repositoryformatversion", "0")
    ret.set("core", "filemode", "false")
    ret.set("core", "bare", "false")

    return ret
