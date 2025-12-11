# Copyright 2014 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from .builder import Builder
from .table import Table
from .compat import range_func as compat_range
from ._version import __version__
from ._git_version import __git_version__
from . import util


def version() -> str:
    """
    Return the exact git version of the vendored FlatBuffers runtime.

    This returns the output of ``git describe --tags`` from the
    deps/flatbuffers submodule at build time, e.g. "v25.9.23" for
    a tagged release or "v25.9.23-2-g95053e6a" for a post-tag commit.

    :returns: Git describe version string of the FlatBuffers runtime.
    """
    return __git_version__
