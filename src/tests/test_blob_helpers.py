import io

from azure_image_resizer.BlobHelpers import not_website_image
from azure_image_resizer.BlobHelpers import read_blob_to_stream
from azure_image_resizer.Settings import Settings


class NotWebsiteImageTestCase:
    def test_valid_blob(self):
        assert not_website_image('$web', 'test.jpg')
        assert not_website_image('$web', 'test.jpeg')
        assert not_website_image('$web', 'test.png')
        assert not_website_image('$web', 'test.JPG')
        assert not_website_image('$web', 'test.JPEG')
        assert not_website_image('$web', 'test.PNG')

    def test_invalid_continer(self):
        assert not not_website_image('data', 'test.jpg')

    def test_already_processed(self):
        assert not not_website_image('$web', 'test_100w.jpg')


class ReadBlobToStreamTestCase:
    def assign_stream(self, continaer_name, blob_name, stream):
        stream = io.BytesIO(b'test bytes')
        stream.seek(0)
        return stream

    def test_returns_stream(self, mocker):
        # Setup settings
        test_env = {}
        test_env['AzureWebJobsStorage'] = 'DefaultEndpointsProtocol=https;EndpointSuffix=core.windows.net;AccountName=test;AccountKey=test'
        test_env['ImageSizes'] = [1, 2, 3]
        settings = Settings(test_env)

        mocked_blob_service = mocker.patch('azure.storage.blob.BlockBlobService')
        mocked_blob_service.get_blob_to_stream = self.assign_stream

        assert read_blob_to_stream(settings, 'container_name', 'blob_name').read() == b'test bytes'
