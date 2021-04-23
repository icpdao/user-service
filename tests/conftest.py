import os, sys
import pytest

ROOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../')
sys.path.append(ROOT_DIR)

from app import app as flask_app

@pytest.fixture
def app():
    return flask_app
