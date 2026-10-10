# Copyright 2021-2026 ONDEWO GmbH
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
"""
Release credentials never reach a process argv or the console.

``/proc/<pid>/cmdline`` is world-readable, so a secret on the command line of make, the shell, docker
or twine is visible to every user on the host for the life of the process. make expands ``$(NAME)``
and ``${NAME}`` INTO the recipe line before ``/bin/sh -c`` runs it, so a recipe may only read a secret
as ``$${NAME}`` (expanded by the shell from the exported environment).

Set ``RELEASE_HYGIENE_MAKEFILE`` to scan another Makefile (e.g. ``git show master:Makefile``).
"""

import os
import re
from pathlib import Path
from typing import List

REPO_ROOT: Path = Path(__file__).resolve().parent.parent
MAKEFILE_PATH: Path = Path(os.environ.get("RELEASE_HYGIENE_MAKEFILE", REPO_ROOT / "Makefile"))
MAKEFILE: str = MAKEFILE_PATH.read_text(encoding="utf-8")
RECIPE_LINES: List[str] = [line for line in MAKEFILE.splitlines() if line.startswith("\t")]
WORKFLOWS: List[Path] = sorted((REPO_ROOT / ".github" / "workflows").glob("*.y*ml"))

SECRET: str = r"[A-Z0-9_]*(?:TOKEN|PASSWORD|API_KEY|SECRET|PASSPHRASE|USERNAME)[A-Z0-9_]*"
# The only allowed make expansion of a secret in a recipe: a <set>/<unset> report that never shows the value.
SET_UNSET: str = rf"\$\(if \$[({{]{SECRET}[)}}],<set>,<unset>\)"


def test_make_never_expands_a_secret_into_a_recipe_line() -> None:
    """Verify no recipe line carries ``$(SECRET)`` / ``${SECRET}`` (make puts the value on argv)."""
    offending: List[str] = [
        line
        for line in RECIPE_LINES
        if re.search(rf"(?<!\$)\$[({{]{SECRET}[)}}]", re.sub(SET_UNSET, "", line))
    ]
    assert offending == []


def test_docker_gets_secrets_by_name_only() -> None:
    """Verify ``docker run`` forwards secrets as ``-e NAME``, never ``-e NAME=<value>``."""
    assert re.findall(rf"(?:-e|--env)[ =]+{SECRET}=", MAKEFILE) == []


def test_no_make_variable_named_info_is_passed_to_a_sub_make() -> None:
    """Verify no recipe hands ``$(info)`` (credentials read with ``$(shell grep ...)``) to a sub-make."""
    assert [line for line in RECIPE_LINES if "$(info)" in line] == []


def test_no_sub_make_gets_a_secret_as_an_argument() -> None:
    """Verify no ``make <target> NAME=<value>`` / ``$(MAKE) <target> NAME=<value>`` for a secret."""
    assert [line for line in RECIPE_LINES if re.search(rf"(?:\bmake|\$\(MAKE\))\b[^;&|]*\b{SECRET}=", line)] == []


def test_no_secret_flag_on_argv() -> None:
    """Verify no tool gets a credential as a flag (``-p${...}``, ``--password``, ``--token``, ``Authorization:``)."""
    patterns: List[str] = [rf"-[pu]\s*\$?\$[({{]{SECRET}", r"--token\b", r"--password\b", r"Authorization:"]
    assert [line for line in RECIPE_LINES if any(re.search(pattern, line) for pattern in patterns)] == []


def test_the_devops_release_hands_the_credentials_over_the_environment() -> None:
    """Verify ``run_release_with_devops`` exports anchored ``^NAME=`` lines and runs a bare ``$(MAKE) release``."""
    recipe: str = MAKEFILE.split("\nrun_release_with_devops:", 1)[1].split("\n\n", 1)[0]
    assert "set -a" in recipe
    assert "grep -h -E '^(" in recipe
    assert re.search(r"\$\(MAKE\) release\s*$", recipe) is not None


def test_workflows_never_interpolate_a_secret_into_a_command() -> None:
    """Verify no workflow ``run:`` block contains ``${{ secrets.X }}`` (pass it through ``env:``)."""
    offending: List[str] = []
    for workflow in WORKFLOWS:
        in_run: bool = False
        run_indent: int = 0
        for line in workflow.read_text(encoding="utf-8").splitlines():
            indent: int = len(line) - len(line.lstrip())
            match = re.match(r"\s*(?:-\s+)?run:", line)
            if match:
                in_run, run_indent = True, indent
            elif in_run and line.strip() and indent <= run_indent:
                in_run = False
            if in_run and "${{ secrets." in line:
                offending.append(f"{workflow.name}: {line.strip()}")
    assert offending == []
