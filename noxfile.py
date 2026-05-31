import functools
import os
import re
import urllib.request

import nox

nox.options.envdir = "build/nox"
nox.options.sessions = ["lint", "tests", "mypy", "docs", "dry_release"]

VERSIONS = ["3.12", "3.13", "3.14"]

PUBLISH_ACTION = "pypa/gh-action-pypi-publish"
# The interpreter the publish action uploads with (its Docker base image).
# Committed so nox can select it before the session runs, but verified
# against the pinned action at runtime (_verify_publish_python) so it cannot
# silently drift. The dry_release row in pr-main.yml must use this version
# too, or nox's --python filter fails the job.
PUBLISH_PYTHON = "3.11"


def _publish_action_sha():
    workflow = os.path.join(
        os.path.dirname(__file__), ".github", "workflows", "release.yml"
    )
    with open(workflow, encoding="utf-8") as stream:
        pattern = re.escape(PUBLISH_ACTION) + r"@([0-9a-f]{40})"
        match = re.search(pattern, stream.read())
    return match.group(1)


def _publish_action_file(sha, path):
    url = f"https://raw.githubusercontent.com/{PUBLISH_ACTION}/{sha}/{path}"
    with urllib.request.urlopen(url) as response:
        return response.read().decode()


def _verify_publish_python(sha):
    dockerfile = _publish_action_file(sha, "Dockerfile")
    match = re.search(r"^FROM python:(\d+\.\d+)", dockerfile, re.MULTILINE)
    found = match.group(1) if match else None
    if found != PUBLISH_PYTHON:
        raise ValueError(
            f"{PUBLISH_ACTION}@{sha} uploads on Python {found}, but "
            f"PUBLISH_PYTHON is {PUBLISH_PYTHON}. Update PUBLISH_PYTHON and "
            "the dry_release row in pr-main.yml to match the pinned action."
        )


def _publish_twine_requirement(sha):
    runtime = _publish_action_file(sha, "requirements/runtime.txt")
    return re.search(r"^twine==\S+", runtime, re.MULTILINE).group(0)


@nox.session(python=VERSIONS)
def tests(session):
    tmpdir = session.create_tmp()
    session.install("-r", "requirements-tests.txt")
    session.install("-e", ".")
    tests = session.posargs or ["gather.tests"]
    session.run(
        "coverage",
        "run",
        "--branch",
        "--source=gather",
        "-m",
        "virtue",
        *tests,
        env=dict(COVERAGE_FILE=os.path.join(tmpdir, "coverage"), TMPDIR=tmpdir),
    )
    fail_under = "--fail-under=100"
    session.run(
        "coverage",
        "report",
        fail_under,
        "--show-missing",
        "--skip-covered",
        env=dict(COVERAGE_FILE=os.path.join(tmpdir, "coverage")),
    )


@nox.session(python=VERSIONS[-1])
def build(session):
    session.install("build")
    session.run("python", "-m", "build", "--wheel")


@nox.session(python=PUBLISH_PYTHON)
def dry_release(session):
    """Build sdist and wheel and validate them with the publish toolchain.

    Runs on the same Python and twine the pinned publish action uploads
    with, so anything the real upload would reject fails here first.
    """
    sha = _publish_action_sha()
    _verify_publish_python(sha)
    output = os.path.abspath(os.path.join(session.create_tmp(), "dist"))
    session.install("build", _publish_twine_requirement(sha))
    session.run("python", "-m", "build", "--outdir", output)
    files = sorted(os.path.join(output, name) for name in os.listdir(output))
    session.run("twine", "check", "--strict", *files)


@nox.session(python=VERSIONS[-1])
def lint(session):
    files = ["src/", "noxfile.py"]
    session.install("-r", "requirements-lint.txt")
    session.install("-e", ".")
    session.run("black", "--check", "--diff", *files)
    session.run(
        "python",
        "-m",
        "stolid",
        "--max-line-length=88",
        "--ignore=E203,E503,W503",
        "--style=google",
        "--skip-checking-short-docstrings=False",
        "--arg-type-hints-in-docstring=False",
        "--check-return-types=False",
        "--check-yield-types=False",
        "src/",
    )


@nox.session(python=VERSIONS[-1])
def mypy(session):
    session.install("-r", "requirements-mypy.txt")
    session.install("-r", "requirements-tests.txt")
    session.install("-e", ".")
    session.run(
        "mypy",
        "--strict",
        "--disallow-any-explicit",
        "src/",
    )


@nox.session(python=VERSIONS[-1])
def docs(session):
    """Build the documentation."""
    output_dir = os.path.abspath(os.path.join(session.create_tmp(), "output"))
    doctrees, html = map(
        functools.partial(os.path.join, output_dir), ["doctrees", "html"]
    )
    session.run("rm", "-rf", output_dir, external=True)
    session.install("-r", "requirements-docs.txt")
    session.install("-e", ".")
    sphinx = ["sphinx-build", "-b", "html", "-W", "-d", doctrees, ".", html]
    session.cd("doc")
    session.run(*sphinx)


@nox.session(python=VERSIONS[-1])
def refresh_deps(session):
    """Refresh the requirements-*.txt files"""
    session.install("pip-tools")
    for deps in ["tests", "docs", "lint", "mypy"]:
        session.run(
            "pip-compile",
            "--upgrade",
            "--extra",
            deps,
            "pyproject.toml",
            "--output-file",
            f"requirements-{deps}.txt",
        )
