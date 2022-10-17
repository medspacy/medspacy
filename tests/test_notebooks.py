import pytest

import os
import subprocess
import tempfile
from sys import platform

os.environ["KMP_DUPLICATE_LIB_OK"] = "True"


class TestNotebooks:
    # @pytest.mark.skip(
    #    "revisit notebook tests later, currently failing in CI while all other tests passing."
    # )
    def test_execute_example_notebooks(self):
        successful_executions = 0
        os.chdir("../")  # move to medspacy folder
        for root, dirs, files in os.walk(os.path.join(os.getcwd(), "notebooks")):
            for file in files:
                if file.endswith(".ipynb"):

                    # Skip this one since it has some large dependencies and downloads
                    if "using-pretrained-models" in file.lower():
                        continue

                    # Skip this one since it has some large dependencies and manual downloads
                    # if "12-io" in file.lower():
                    #    continue

                    # Skip this one since it has some large dependencies and manual downloads
                    if "11a" in file.lower():
                        continue

                    if "11b" in file.lower():
                        continue

                    # TODO: skip pre-trained notebook until we can find a replacement for med7
                    if "06" in file.lower():
                        continue

                    # Skip this one since it has an Exception which currently occurs intentionally
                    # Now sure if we can work around this in some way
                    if "advanced-modifiers" in file.lower():
                        continue

                    # Skip this on Windows since there are other pieces which must be installed
                    # manually on this platform for now
                    if platform.startswith("win") and "quickumls" in file.lower():
                        continue

                    notebook_full_path = os.path.join(root, file)

                    # do not run on checkpoints of notebooks!
                    if ".ipynb_checkpoints" in notebook_full_path.lower():
                        continue

                    # Following a pattern from here:
                    # https://github.com/ghego/travis_anaconda_jupyter/blob/master/test_nb.py
                    with tempfile.NamedTemporaryFile(
                        suffix=".ipynb", delete=False
                    ) as fout:
                        args = [
                            "jupyter",
                            "nbconvert",
                            "--to",
                            "notebook",
                            "--execute",
                            "--ExecutePreprocessor.timeout=1000",
                            # Need to specify a kernel so we don't use the default
                            "--ExecutePreprocessor.kernel_name=python3",
                            "--output",
                            fout.name,
                            notebook_full_path,
                        ]
                        subprocess.check_call(args)
                        successful_executions += 1

        # Make sure we executed something
        # (ensure that the logic above is still actually running notebooks)
        assert successful_executions > 0
