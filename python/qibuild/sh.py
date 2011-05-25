## Copyright (C) 2011 Aldebaran Robotics

""" sh like functions """

# Mostly wrappers around somehow strange-behaving
# shutil functions ...

import sys
import os
import shutil
import tempfile
import logging
import subprocess

LOGGER = logging.getLogger("buildtool.sh")

def mkdir(dest_dir, recursive=False):
    """ Recursive mkdir (do not fail if file exists) """
    try:
        if recursive:
            os.makedirs(dest_dir)
        else:
            os.mkdir(dest_dir)
    except OSError, e:
        if e.errno == 17:
            # Directory already exists -> we don't care
            pass
        else:
            raise

#pylint: disable-msg=C0103
def ln(src, dst, symlink=True):
    """ ln (do not fail if file exists) """
    try:
        if symlink:
            os.symlink(src, dst)
        else:
            raise NotImplementedError
    except OSError, e:
        if e.errno == 17:
            pass
        else:
            raise

def configure_file(in_path, out_path, copy_only=False, *args, **kwargs):
    """Configure a file.
    in_path : input file
    out_path : output file

    The out_path needs not to exist, missing leading directories will
    be create if necessary.

    If copy_only is True, the contents will be copied "as is".

    If not, we will use the args and kwargs parameter as in:
    in_content.format(*args, **kwargs)

    """
    mkdir(os.path.dirname(os.path.abspath(out_path)), recursive=True)
    with open(in_path, "r") as in_file:
        in_content = in_file.read()
        if copy_only:
            out_content = in_content
        else:
            out_content = in_content.format(*args, **kwargs)
        with open(out_path, "w") as out_file:
            out_file.write(out_content)

def install(src, dest, filter=None):
    """Install a directory to a destination.

    If filter is not None, then the file will only be
    installed if filter(relative/path/to/file) returns
    True.

    Few notes: rewriting `cp' or `install' is a hard problem.
    This version will happily erase whatever is inside dest,
    and won't complain if dest does not exists (missing
    directories will simply be created)


    Note that if src contains empty directories, they won't be
    installled.

    """
    LOGGER.debug("Installing %s -> %s", src, dest)
    if filter is None:
        def filter(filename):
            return True

    if os.path.isdir(src):
        mkdir(dest, recursive=True)
        for (root, dirs, files) in os.walk(src):
            new_root = os.path.relpath(root, src)
            for file in files:
                rel_path = os.path.join(new_root, file)
                if not filter(rel_path):
                    continue
                file_src = os.path.join(root, file)
                mkdir(os.path.join(dest, new_root), recursive=True)
                file_dest = os.path.join(dest, new_root, file)
                # If this is not run interactively, avoid polluting
                # stdout:
                if sys.stdout.isatty():
                    print "-- Installing:", file_dest
                shutil.copy(file_src, file_dest)
    else:
        if os.path.isdir(dest):
            dest = os.path.join(dest, os.path.basename(src))
        mkdir(os.path.dirname(dest), recursive=True)
        shutil.copy(src, dest)

def rm(name):
    """This one can take a file or a directory.
    Contrary to shutil.remove or os.remove, it:

    * won't fail if the directory does not exists
    * won't fail if the directory contains read-only files
    * won't fail if the file does not exists

    Please avoid using shutil.rmtree ...
    """
    if not os.path.exists(name):
        return
    def _rmtree_handler(func, path, _execinfo):
        """Call by rmtree when there was an error.

        if this is called because we could not remove a file, then see if
        it is readonly, change it back to nornal and try again

        """
        import stat
        if (func == os.remove) and not os.access(path, os.W_OK):
            os.chmod(path, stat.S_IWRITE)
            os.remove(path)
        else:
            # Something else must be wrong...
            raise

    if os.path.isdir(name):
        LOGGER.debug("Removing directory: %s", name)
        shutil.rmtree(name, False, _rmtree_handler)
    else:
        LOGGER.debug("Removing %s", name)
        os.remove(name)


def mv(src, dest):
    """Move a file into a directory, but do not crash
    if dest/src exists

    """
    if os.path.isdir(dest):
        dest = os.path.join(dest, os.path.basename(src))
    if os.path.exists(dest):
        os.remove(dest)
    shutil.move(src, dest)


def ls_r(directory):
    """Returns a sorted list of all the files present in a diretory,
    relative to this directory.

    For instance, with:

    foo
    |-- eggs
    |   |-- c
    |   |-- d
    |-- empty
    |-- spam
    |   |-- a
    |   |-- b

    ls_r(foo) returns:
    ["eggs/c", "eggs/d", "empty/", "spam/a", "spam/b"]

    """
    res = list()
    for root, dirs, files in os.walk(directory):
        new_root = os.path.relpath(root, directory)
        if new_root == "." and not files:
            continue
        if new_root == "." and files:
            res.extend(files)
            continue
        if not files and not dirs:
            res.append(new_root + os.path.sep)
            continue
        for f in files:
            res.append(os.path.join(new_root, f))
    res.sort()
    return res

def which(program):
    """
    find program in the environment PATH
    @return path to program if found, None otherwise
    """
    import warnings
    warnings.warn("qibuild.sh.which is deprecated, "
     "use qibuild.command.find_program instead")
    from qibuild.command import find_program
    return find_program(program)


def run(program, args):
    """ exec a process.
        linux: this will call exec and replace the current process
        win  : this will call spawn and wait till the end
        ex:
        run("python.exe", "toto.py")
    """
    real_args = [ program ]
    real_args.extend(args)

    if sys.platform.startswith("win32"):
        retcode = 0
        try:
            retcode = subprocess.call(real_args)
        except subprocess.CalledProcessError:
            print "problem when calling", program
            retcode = 2
        sys.exit(retcode)
        return

    os.execvp(program, real_args)

def to_posix_path(path):
    """
    Returns a POSIX path from a DOS path

    Useful because cmake *needs* POSIX paths.

    Guidelines:
        * always use os.path insternally
        * convert to POSIX path at the very last moment

    """
    res = os.path.expanduser(path)
    res = os.path.abspath(res)
    res = path.replace("\\", "/")
    return res

def to_dos_path(path):
    """Return a DOS path from a "windows with /" path.
    Useful because people sometimes use forward slash in
    environment variable, for instance
    """
    res = path.replace("/", "\\")
    return res

def to_native_path(path):
    """Return an absolute, native path from a path

    """
    path = os.path.expanduser(path)
    path = os.path.normpath(path)
    path = os.path.abspath(path)
    if sys.platform.startswith("win"):
        path = to_dos_path(path)
    return path


class TempDir:
    """This is a nice wrapper around tempfile module.

    Usage:

        with TempDir("foo-bar") as temp_dir:
            subdir = os.path.join(temp_dir, "subdir")
            do_foo(subdir)

    This piece of code makes sure that:
       - a temporary directory named temp_dir has been
     created (guaranteed to exist, be empty, and writeable)

       - the directory will be removed when the scope of
     temp_dir has ended unless an exception has occurred
     and DEBUG environment variable is set.

    """
    def __init__(self, name="tmp"):
        self._temp_dir = tempfile.mkdtemp(prefix=name+"-")

    def __enter__(self):
        return self._temp_dir

    def __exit__(self, type, value, tb):
        if os.environ.get("DEBUG"):
            if tb is not None:
                print "=="
                print "Not removing ", self._temp_dir
                print "=="
                return
        rm(self._temp_dir)