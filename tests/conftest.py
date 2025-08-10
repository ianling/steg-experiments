import glob
import os

import pytest


@pytest.fixture(autouse=True)
def cleanup():
    yield
    # teardown
    for file in glob.glob("tests/*.png"):
        os.remove(file)
    for file in glob.glob("tests/*.mp4"):
        os.remove(file)
