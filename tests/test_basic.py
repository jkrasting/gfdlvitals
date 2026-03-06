"""Basic tests for gfdlvitals package"""

import os


def test_import():
    import gfdlvitals


def test_version_exists():
    import gfdlvitals
    assert isinstance(gfdlvitals.__version__, str)
    assert len(gfdlvitals.__version__) > 0


def test_submodule_imports():
    from gfdlvitals import averagers
    from gfdlvitals import cli
    from gfdlvitals import models
    from gfdlvitals import sample
    from gfdlvitals import util


def test_vitals_dataframe():
    from gfdlvitals import VitalsDataFrame
    df = VitalsDataFrame({"a": [1, 2, 3]})
    assert len(df) == 3


def test_sample_files_exist():
    from gfdlvitals import sample
    assert os.path.isfile(sample.historical)
    assert os.path.isfile(sample.picontrol)


def test_open_db():
    from gfdlvitals import open_db, sample, VitalsDataFrame
    df = open_db(sample.historical)
    assert isinstance(df, VitalsDataFrame)
    assert len(df) > 0
