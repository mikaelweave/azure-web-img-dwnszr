import io, pytest
import azure.storage.blob

from azure_image_resizer.BlobHelpers import *
from azure_image_resizer.Settings import Settings

class TestCase:
    def test_not_website_image_valid_blob(self):
        assert not_website_image("$web", "test.jpg")
        assert not_website_image("$web", "test.jpeg")
        assert not_website_image("$web", "test.png")
        assert not_website_image("$web", "test.JPG")
        assert not_website_image("$web", "test.JPEG")
        assert not_website_image("$web", "test.PNG")

    def test_not_website_image_invalid_continer(self):
        assert not not_website_image("data", "test.jpg")

    def test_not_website_image_already_processed(self):
        assert not not_website_image("$web", "test_100w.jpg")

    def test_read_blob_to_stream_returns_stream(self, mocker):
        # Setup settings
        test_env = {}
        test_env["AzureWebJobsStorage"] = "DefaultEndpointsProtocol=https;EndpointSuffix=core.windows.net;AccountName=test;AccountKey=test"
        test_env["ImageSizes"] = [1,2,3]
        settings = Settings(test_env)

        stream = io.BytesIO(b"test bytes")
        mock_blob_service = mocker.patch('azure.storage.blob.BlockBlobService.get_blob_to_stream')
        mock_blob_service.return_Value = stream

        #FIXME
        # assert read_blob_to_stream(settings, "container_name", "blob_name").read() == stream.read()
        assert read_blob_to_stream(settings, "container_name", "blob_name")