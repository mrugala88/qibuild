"""
This modules contains wrapper classes
around subprocess

"""

import os
import logging
import subprocess

LOGGER = logging.getLogger(__name__)

DRYRUN           = False

class CommandFailedException(Exception):
    """Custom exception """
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message

class NotInPath(Exception):
    """Custom exception """
    def __init__(self, executable):
        self.executable = executable

    def __str__(self):
        mess  = "Could not find executable: %s\n" % self.executable
        mess += "Looked in:\n"
        mess += "\n".join(os.environ["PATH"].split(os.pathsep))
        return mess


def check_is_in_path(executable):
    """Check that the given executable is to be found in %PATH%"""
    env_path = os.environ["PATH"]
    for path in env_path.split(os.pathsep):
        full_path = os.path.join(path, executable)
        if os.access(full_path, os.X_OK):
            return
        pathext = os.environ.get("PATHEXT")
        if pathext:
            for ext in pathext.split(";"):
                with_ext = full_path + ext
                if os.access(with_ext, os.X_OK):
                    return
    raise NotInPath(executable)

def check_call(cmd, ignore_ret_code=False,
                    cwd=None,
                    shell=False,
                    env=None,
                    return_ret_code=False,
                    output_to_logger=False,
                    verbose_exception=False):
    """
    call a command from a working dir.
    Raise a CommandFailedException if the return code
    is not zero and ignore_ret_code is not False

    Warning: if output_to_logger is activated, the log will be stored in RAM

    """
    #changing the working directory is not enough.. change the env var too (or git at least will not be happy)
    if cwd:
        if not env:
            env = os.environ.copy()
        env["PWD"] = cwd

    # Check that exe is in PATH
    # (uber-useful on windows)
    check_is_in_path(cmd[0])

    LOGGER.debug("calling: %s", " ".join(cmd))
    if DRYRUN:
        return 0
    try:
        outputlist = list()
        if output_to_logger or verbose_exception:
            process = subprocess.Popen(cmd, cwd=cwd, env=env,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT)
            outputlist = process.communicate()[0].split("\n")
            if output_to_logger:
                for line in outputlist:
                    LOGGER.info(line)
            retcode = process.returncode
        else:
            retcode = subprocess.call(cmd, cwd=cwd, env=env)

    except OSError as e:
        _raise_error(cmd, cwd, shell, exception=e, output=outputlist)
    except subprocess.CalledProcessError as e:
        _raise_error(cmd, cwd, shell, exception=e, output=outputlist)

    if ignore_ret_code:
        return 0

    if retcode != 0:
        if return_ret_code == False:
            _raise_error(cmd, cwd, shell, retcode=retcode, output=outputlist)
    return retcode

def call(cmd, cwd=None, shell=False, env=None):
    """
    call without exception if retcode is not 0
    """
    return check_call(cmd, ignore_ret_code=True, shell=shell, cwd=cwd, env=env)

def call_retcode(cmd, cwd=None, shell=False, env=None):
    """
    call which returns the true return code
    """
    return check_call(cmd, shell=shell, cwd=cwd, env=env, return_ret_code=True)

def call_output(cmd, cwd=None, shell=False, env=None):
    """
    Get the stdout of a command as a list of split lines.

    Raise a CommandFailedException if something went wrong

    """
    res = ""
    LOGGER.debug("calling: %s", " ".join(cmd))
    if DRYRUN:
        return [""]
    try:
        process = subprocess.Popen(cmd, cwd=cwd, env=env,
                                   stdout=subprocess.PIPE)
        res = process.communicate()[0].split("\n")
    except OSError as e:
        _raise_error(cmd, cwd, shell, e)
    except subprocess.CalledProcessError as e:
        _raise_error(cmd, cwd, shell, e)
    return res


def _raise_error(cmd, cwd, shell, exception=None, retcode=None, output=None):
    """
    Raise a CommandFailedException with a nice message

    """
    mess = "qitools.command failed\n"
    if exception:
        mess += "# error  : %s\n" % (exception)
    if retcode:
        mess += "# error  : retcode is %d\n" % (retcode)
    if cwd is not None:
        mess += "# workdir: %s\n" % (cwd)
    mess += "# run in shell: %s\n" % (shell)
    mess += "# command: %s\n" % " ".join(cmd)
    if output and len(output):
        mess += "# output: %s\n" % "\n".join(output)
    raise CommandFailedException(mess)


