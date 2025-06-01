# SPDX-License-Identifier: GPL-2.0+
#
# Copyright (c) 2016 Google, Inc
#

from contextlib import contextmanager
import glob
import os
import sys

import command

from io import StringIO  # Python 3 only


def RunTestCoverage(prog, filter_fname, exclude_list, build_dir, required=None):
    """Run tests and check that we get 100% coverage

    Args:
        prog: Program to run (will be passed a '-t' argument to run tests)
        filter_fname: If not None, only filenames containing this string are included
        exclude_list: List of file patterns to exclude from coverage calculation
        build_dir: Build directory, used to locate libfdt.py
        required: Set of module names that must be in the coverage report

    Raises:
        ValueError: If the code coverage is not 100% or required modules are missing
    """
    path = os.path.dirname(prog)
    glob_list = []
    if filter_fname:
        all_files = glob.glob(os.path.join(path, '*.py'))
        glob_list = [fname for fname in all_files if filter_fname in fname]

    glob_list += exclude_list
    glob_list += ['*libfdt.py', '*site-packages*']

    omit_list = ','.join(glob_list)
    cmd = (
        f'PYTHONPATH=$PYTHONPATH:{build_dir}/sandbox_spl/tools '
        f'python3 -m coverage run --omit "{omit_list}" {prog} -t'
    )
    os.system(cmd)

    stdout = command.Output('python3 -m coverage', 'report')
    lines = stdout.splitlines()
    ok = True

    if required:
        # Convert '/path/to/name.py' to 'name'
        test_set = {
            os.path.splitext(os.path.basename(line.split()[0]))[0]
            for line in lines if '/etype/' in line
        }
        missing_list = required - test_set
        if missing_list:
            print(f"Missing tests for {', '.join(sorted(missing_list))}")
            print(stdout)
            ok = False

    coverage = lines[-1].split()[-1]
    print(coverage)
    if coverage != '100%':
        print(stdout)
        print("Type 'python3 -m coverage html' to get a report in htmlcov/index.html")
        print(f'Coverage error: {coverage}, but should be 100%')
        ok = False

    if not ok:
        raise ValueError('Test coverage failure')


# Use this to suppress stdout/stderr output:
# with capture_sys_output() as (stdout, stderr)
@contextmanager
def capture_sys_output():
    capture_out, capture_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = capture_out, capture_err
        yield capture_out, capture_err
    finally:
        sys.stdout, sys.stderr = old_out, old_err
