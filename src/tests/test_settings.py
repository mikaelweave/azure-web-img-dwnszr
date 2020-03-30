import pytest
from azure_image_resizer.Settings import Settings

class TestCase:
    def test_settings_set_correctly(self):
        test_env = {}
        test_env["AzureWebJobsStorage"] = "test_connection_string"
        test_env["ImageSizes"] = [1,2,3]

        settings = Settings(test_env)

        assert settings.storage_connection_string == "test_connection_string"
        assert settings.image_sizes == [1,2,3]

    def test_settings_thow_exception_no_connection_string(self):
        test_env = {}
        test_env["ImageSizes"] = [1,2,3]

        with pytest.raises(Exception):
            settings = Settings(test_env)

    def test_settings_thow_exception_no_image_sizes(self):
        test_env = {}
        test_env["AzureWebJobsStorage"] = "test_connection_string"

        with pytest.raises(Exception):
            settings = Settings(test_env)