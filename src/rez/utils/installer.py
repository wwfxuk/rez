from __future__ import print_function

import os.path
import sys
import shutil
import subprocess

import rez
from rez.package_maker import make_package
from rez.system import system


def install_as_rez_package(repo_path, pkg_name='rez'):
    """Install the current rez installation as a rez package.

    Note: This is very similar to 'rez-bind rez', however rez-bind is intended
    for deprecation. Rez itself is a special case.

    Args:
        repo_path (str): Repository to install the rez package into.
        pkg_name (str): Rez package's package name (Default: rez).
    """
    def commands():
        env.PYTHONPATH.append('{this.root}')

    def make_root(variant, root):
        # copy source
        rez_path = rez.__path__[0]
        site_path = os.path.dirname(rez_path)
        rezplugins_path = os.path.join(site_path, "rezplugins")

        shutil.copytree(rez_path, os.path.join(root, "rez"))
        shutil.copytree(rezplugins_path, os.path.join(root, "rezplugins"))

    variant = system.variant
    variant.append("python-{0.major}.{0.minor}".format(sys.version_info))

    with make_package(pkg_name, repo_path, make_root=make_root) as pkg:
        pkg.version = rez.__version__
        pkg.commands = commands
        pkg.variants = [variant]
        print("installing rez as Python package under", repo_path)

    print('')
    for installed_variant in pkg.installed_variants:
        install_path = installed_variant.base
        print("SUCCESS! Rez Python package was installed to", install_path)


def install_as_production_package(install_py, repo_path, pkg_name='rez'):
    """Install a production rez installation as a rez package.

    Note: This is very similar to 'rez-bind rez', however rez-bind is intended
    for deprecation. Rez itself is a special case.

    Args:
        install_py (list[str]): Command line args to call "install.py".
        repo_path (str): Repository to install the rez package into.
        pkg_name (str): Rez package's package name (Default: rez).
    """
    def commands():
        import os
        bin_folder = "Scripts" if os.name == "nt" else "bin"
        env.PATH.append(os.path.join("{this.root}", bin_folder, "rez"))
        env.PYTHONPATH.append(os.path.join("{this.root}", "python"))

    def make_root(variant, root):
        subprocess.check_call(list(install_py) + [root])

        # copy source
        rez_path = rez.__path__[0]
        site_path = os.path.dirname(rez_path)
        rezplugins_path = os.path.join(site_path, "rezplugins")

        py_root = os.path.join(root, "python")
        os.mkdir(py_root)
        shutil.copytree(rez_path, os.path.join(py_root, "rez"))
        shutil.copytree(rezplugins_path, os.path.join(py_root, "rezplugins"))

        print('Setting up "%s"' % os.path.join(variant.base, 'package.py'))

    with make_package(pkg_name, repo_path, make_root=make_root) as pkg:
        # Production Python venv probably works for same platform + arch combo
        pkg.variants = [system.variant[:-1]]
        pkg.version = rez.__version__
        pkg.commands = commands

    print('SUCCESS! After activated Rez, you can then:')
    print('rez env %s' % pkg_name)
