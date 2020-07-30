# Copyright (c) 2020, NVIDIA CORPORATION.  All rights reserved.
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

import tarfile
import urllib.request
from os import mkdir
from os.path import dirname, exists, getsize, join
from shutil import rmtree

import pytest

# Those variables probably should go to main NeMo configuration file (config.yaml).
__TEST_DATA_FILENAME = "test_data.tar.gz"
__TEST_DATA_URL = "https://github.com/NVIDIA/NeMo/releases/download/v0.11.0/"
__TEST_DATA_SUBDIR = ".data"


def pytest_addoption(parser):
    """ Additional command-line arguments passed to pytest. For now: --cpu """
    parser.addoption('--cpu', action='store_true', help="pass that argument to use CPU during testing (default: GPU)")


@pytest.fixture
def device(request):
    """ Simple fixture returning string denoting the device [CPU | GPU] """
    if request.config.getoption("--cpu"):
        return "CPU"
    else:
        return "GPU"


@pytest.fixture(autouse=True)
def run_only_on_device_fixture(request, device):
    if request.node.get_closest_marker('run_only_on'):
        if request.node.get_closest_marker('run_only_on').args[0] != device:
            pytest.skip('skipped on this device: {}'.format(device))


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "run_only_on(device): runs the test only on a given device [CPU | GPU]",
    )


@pytest.fixture()
def test_data_dir():
    """ Fixture returns test_data_dir. """
    # Test dir.
    test_data_dir_ = join(dirname(__file__), __TEST_DATA_SUBDIR)
    return test_data_dir_


def pytest_configure(config):
    """
    Initial configuration of conftest.
    The function checks if test_data.tar.gz is present in tests/.data.
    If so, compares its size with github's test_data.tar.gz.
    If file absent or sizes not equal, function downloads the archive from github and unpacks it.
    """
    # Test dir and archive filepath.
    test_dir = join(dirname(__file__), __TEST_DATA_SUBDIR)
    test_data_archive = join(dirname(__file__), __TEST_DATA_SUBDIR, __TEST_DATA_FILENAME)

    # Get size of local test_data archive.
    try:
        test_data_local_size = getsize(test_data_archive)
    except:
        # File does not exist.
        test_data_local_size = -1

    # Get size of remote test_data archive.
    url = __TEST_DATA_URL + __TEST_DATA_FILENAME
    u = urllib.request.urlopen(url)
    # Get metadata.
    meta = u.info()
    test_data_remote_size = int(meta["Content-Length"])

    # Compare sizes.
    if test_data_local_size != test_data_remote_size:
        print(
            "Downloading the `{}` test archive from `{}`, please wait...".format(__TEST_DATA_FILENAME, __TEST_DATA_URL)
        )
        # Remove .data folder.
        if exists(test_dir):
            rmtree(test_dir)
        # Create one .data folder.
        mkdir(test_dir)
        # Download
        urllib.request.urlretrieve(url, test_data_archive)
        # Extract tar
        print("Extracting the `{}` test archive, please wait...".format(test_data_archive))
        tar = tarfile.open(test_data_archive)
        tar.extractall(path=test_dir)
        tar.close()
    else:
        print(
            "A valid `{}` test archive ({}B) found in the `{}` folder.".format(
                __TEST_DATA_FILENAME, test_data_local_size, test_dir
            )
        )
