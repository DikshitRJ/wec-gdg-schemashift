"""Unit tests for configuration loading.

Spec: foundation/config-test
"""

import os
from schemashift.config import Settings


def test_default_settings():
    settings = Settings()
    assert settings.source.database == "shop"
    assert settings.sampling.size == 1000
    assert settings.scoring.matched == 0.85
    assert settings.migration.batch_size == 500


def test_env_override():
    os.environ["MONGO_URI"] = "mongodb://custom:27017"
    settings = Settings.load("non_existent_file.yaml")
    assert settings.source.uri == "mongodb://custom:27017"
