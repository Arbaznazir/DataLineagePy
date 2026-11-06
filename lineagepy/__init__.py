"""Import alias for code that still uses the original package name.

``lineagepy`` was renamed to ``datalineagepy``. This package loads the new
implementation and resolves ``lineagepy.<module>`` to ``datalineagepy.<module>``
so existing tests, examples, and notebooks keep importing.
"""

import importlib
import importlib.abc
import importlib.machinery
import importlib.util
import sys


class _AliasLoader(importlib.abc.Loader):
    def __init__(self, target_name):
        self.target_name = target_name

    def create_module(self, spec):
        module = importlib.import_module(self.target_name)
        # Share the module object so patches on either name hit the same code.
        sys.modules[spec.name] = module
        return module

    def exec_module(self, module):
        return None


class _AliasFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        prefix = "lineagepy."
        if not fullname.startswith(prefix):
            return None
        target_name = "datalineagepy." + fullname[len(prefix):]
        target_spec = importlib.util.find_spec(target_name)
        if target_spec is None:
            return None
        is_package = target_spec.submodule_search_locations is not None
        spec = importlib.machinery.ModuleSpec(
            fullname,
            _AliasLoader(target_name),
            is_package=is_package,
        )
        if is_package:
            spec.submodule_search_locations = list(
                target_spec.submodule_search_locations
            )
        return spec


if not any(isinstance(finder, _AliasFinder) for finder in sys.meta_path):
    sys.meta_path.insert(0, _AliasFinder())

from datalineagepy import *  # noqa: E402,F401,F403
import datalineagepy as _datalineagepy

__version__ = _datalineagepy.__version__


def __getattr__(name):
    return getattr(_datalineagepy, name)
