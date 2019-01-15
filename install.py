"""
This script uses an embedded copy of virtualenv to create a standalone,
production-ready Rez installation in the specified directory.
"""
import os
import sys
import shutil
import os.path
import textwrap
import subprocess
from optparse import OptionParser

source_path = os.path.dirname(os.path.realpath(__file__))
bin_path = os.path.join(source_path, "bin")
src_path = os.path.join(source_path, "src")
sys.path.insert(0, src_path)

from rez.utils._version import _rez_version
from rez.backport.shutilwhich import which
from rez.package_maker__ import make_package
from rez.system import system
from rez.utils.lint_helper import env, source
from build_utils.virtualenv.virtualenv import Logger, create_environment, \
    path_locations
from build_utils.distlib.scripts import ScriptMaker


class fake_entry(object):
    code_template = textwrap.dedent(
        """
        from rez.cli.{module} import run
        run({target})
        """).strip() + '\n'

    def __init__(self, name):
        self.name = name

    def get_script_text(self):
        module = "_main"
        target = ""
        if self.name == "bez":
            module = "_bez"
        elif self.name == "_rez_fwd":  # TODO rename this binary
            target = "'forward'"
        elif self.name not in ("rez", "rezolve"):
            target = "'%s'" % self.name.split('-', 1)[-1]
        return self.code_template.format(module=module, target=target)


class _ScriptMaker(ScriptMaker):
    def __init__(self, *nargs, **kwargs):
        super(_ScriptMaker, self).__init__(*nargs, **kwargs)
        self.variants = set(('',))

    def _get_script_text(self, entry):
        return entry.get_script_text()


def patch_rez_binaries(dest_dir):
    bin_names = os.listdir(bin_path)
    _, _, _, venv_bin_path = path_locations(dest_dir)
    venv_py_executable = which("python", env={"PATH":venv_bin_path,
                                              "PATHEXT":os.environ.get("PATHEXT", "")})

    # delete rez bin files written by setuptools
    for name in bin_names:
        filepath = os.path.join(venv_bin_path, name)
        if os.path.isfile(filepath):
            os.remove(filepath)

    # write patched bins instead. These go into 'bin/rez' subdirectory, which
    # gives us a bin dir containing only rez binaries. This is what we want -
    # we don't want resolved envs accidentally getting the venv's 'python'.
    dest_bin_path = os.path.join(venv_bin_path, "rez")
    if os.path.exists(dest_bin_path):
        shutil.rmtree(dest_bin_path)
    os.makedirs(dest_bin_path)

    maker = _ScriptMaker(bin_path, dest_bin_path)
    maker.executable = venv_py_executable
    options = dict(interpreter_args=["-E"])

    for name in bin_names:
        entry = fake_entry(name)
        maker._make_script(entry, [], options=options)


def copy_completion_scripts(dest_dir):
    # find completion dir in rez package
    path = os.path.join(dest_dir, "lib")
    completion_path = None
    for root, dirs, _ in os.walk(path):
        if os.path.basename(root) == "completion":
            completion_path = root
            break

    if completion_path:
        dest_path = os.path.join(dest_dir, "completion")
        if os.path.exists(dest_path):
            shutil.rmtree(dest_path)
        shutil.copytree(completion_path, dest_path)
        return dest_path

    return None


def install(dest_dir, verbosity=0):
    """Install rez into the given directory.

    Args:
        dest_dir (str): Full path to the install directory.

    Keyword Args:
        verbosity (int): Level of verbosity (typically from args).
    """
    print "installing rez to %s..." % dest_dir

    # make virtualenv verbose
    log_level = Logger.level_for_integer(2 - verbosity)
    logger = Logger([(log_level, sys.stdout)])

    # create the virtualenv
    create_environment(dest_dir)

    # install rez from source
    _, _, _, venv_bin_dir = path_locations(dest_dir)
    py_executable = which("python", env={"PATH":venv_bin_dir,
                                         "PATHEXT":os.environ.get("PATHEXT",
                                                                  "")})
    args = [py_executable, "setup.py", "install"]
    if verbosity:
        print "running in %s: %s" % (source_path, " ".join(args))
    p = subprocess.Popen(args, cwd=source_path)
    p.wait()

    # patch the rez binaries
    patch_rez_binaries(dest_dir)

    # copy completion scripts into venv
    completion_path = copy_completion_scripts(dest_dir)

    # mark venv as production rez install. Do not remove - rez uses this!
    dest_bin_dir = os.path.join(venv_bin_dir, "rez")
    validation_file = os.path.join(dest_bin_dir, ".rez_production_install")
    with open(validation_file, 'w') as f:
        f.write(_rez_version)

    # done
    print('')
    print("SUCCESS! To activate Rez, add the following path to $PATH:")
    print(dest_bin_dir)

    if completion_path:
        print('')
        shell = os.getenv('SHELL')

        if shell:
            shell = os.path.basename(shell)
            ext = "csh" if "csh" in shell else "sh"  # Basic selection logic

            print("You may also want to source the completion script (for %s):" % shell)
            print("source {0}/complete.{1}".format(completion_path, ext))
        else:
            print("You may also want to source the relevant completion script from:")
            print(completion_path)

    print('')


if __name__ == "__main__":
    usage = ("usage: %prog [options] DEST_DIR ('{version}' in DEST_DIR will "
             "expand to Rez version)")
    parser = OptionParser(usage=usage)
    parser.add_option(
        '-v', '--verbose', action='count', dest='verbose', default=0,
        help="Increase verbosity.")
    parser.add_option(
        '-p', '--as-package', dest='package',
        help="Given a package name, install using rez package structure. "
             "(DEST_DIR should be the rez packages directory)")
    parser.add_option(
        '-s', '--keep-symlinks', action="store_true", default=False,
        help="Don't run realpath on the passed DEST_DIR to resolve symlinks; "
             "ie, the baked script locations may still contain symlinks")
    opts, args = parser.parse_args()

    if " " in os.path.realpath(__file__):
        parser.error("\n"
            "The absolute path of install.py cannot contain spaces "
            "due to setuptools limitation.\n"
            "Please move installation files to another location or "
            "rename offending folder(s).\n")

    # determine install path
    if len(args) != 1:
        error = "expected DEST_DIR"
        if opts.package:
            error += " (rez packages directory)"
        parser.error(error)

    dest_dir = args[0].format(version=_rez_version)
    dest_dir = os.path.expanduser(dest_dir)
    if not opts.keep_symlinks:
        dest_dir = os.path.realpath(dest_dir)

    if opts.package:
        def make_root(variant, root):
            install(root, verbosity=opts.verbose)

        def commands():
            import os
            import rez
            env.PATH.append(os.path.join('{this.root}', 'bin', 'rez'))
            source(os.path.join('{this.root}', 'completion', 'complete.sh'))

            # Setup PYTHONPATH (inspired by src/rez/bind/rez.py)
            rez_path = rez.__path__[0]
            site_path = os.path.dirname(rez_path)
            rezplugins_path = os.path.join(site_path, "rezplugins")
            env.PYTHONPATH.append(rez_path)
            env.PYTHONPATH.append(rezplugins_path)

        with make_package(opts.package, dest_dir, make_root=make_root) as pkg:
            pkg.version = _rez_version
            pkg.commands = commands
            pkg.description = 'Standalone, production-ready Rez installation'
            pkg.variants = [[
                "platform-{0}".format(system.platform),
                "python-{0.major}.{0.minor}".format(sys.version_info)]]
    else:
        install(dest_dir, verbosity=opts.verbose)
