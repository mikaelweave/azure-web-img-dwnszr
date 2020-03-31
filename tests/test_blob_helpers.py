import io, pytest
from unittest.mock import MagicMock

from azure_image_resizer.BlobHelpers import not_website_image, read_blob_to_stream, save_stream_to_cloud
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
    def setup_settings_for_test(self):
        test_env = {}
        test_env['AzureWebJobsStorage'] = 'DefaultEndpointsProtocol=https;EndpointSuffix=core.windows.net;AccountName=test;AccountKey=test'
        test_env['ImageSizes'] = [1, 2, 3]
        return Settings(test_env)

    def assign_test_stream(self, continaer_name, blob_name, stream):
        stream.truncate()
        stream.write(b'test bytes')
        stream.seek(0)
        return MagicMock('azure.storage.blob.Blob')

    def test_returns_stream(self, mocker):
        settings = self.setup_settings_for_test()

        mocked_blob_service = mocker.patch('azure.storage.blob.BlockBlobService')
        instance = mocked_blob_service.return_value
        instance.get_blob_to_stream = self.assign_test_stream
        spy = mocker.spy(instance, 'get_blob_to_stream')

        assert read_blob_to_stream(settings, 'container_name', 'blob_name.jpg').read() == b'test bytes'
        spy.assert_called_once_with('container_name', 'blob_name.jpg', stream=mocker.ANY)

    def test_catches_and_raises_exception(self, mocker):
        settings = self.setup_settings_for_test()
        test_exception = Exception("test exception")

        mocked_blob_service = mocker.patch('azure.storage.blob.BlockBlobService')
        instance = mocked_blob_service.return_value
        instance.get_blob_to_stream.side_effect = test_exception

        with pytest.raises(Exception) as ex:
            read_blob_to_stream(settings, 'container_name', 'blob_name.jpg')
        assert ex != test_exception
        assert ex.value.args[1] == test_exception


class SaveStreamToCloudTestCase:
    def setup_settings_for_test(self):
        test_env = {}
        test_env['AzureWebJobsStorage'] = 'DefaultEndpointsProtocol=https;EndpointSuffix=core.windows.net;AccountName=test;AccountKey=test'
        test_env['ImageSizes'] = [1, 2, 3]
        return Settings(test_env)

    def test_stream_saves_and_calls_service(self, mocker):
        settings = self.setup_settings_for_test()
        test_stream = io.BytesIO(b'test bytes')

        mocked_blob_service = mocker.patch('azure.storage.blob.BlockBlobService')
        spy = mocker.spy(mocked_blob_service.return_value, 'create_blob_from_stream')
        save_stream_to_cloud(settings, 'container_name', 'blob_name.jpg', test_stream)

        spy.assert_called_once()
        call_args = spy.call_args
        assert call_args.args[0] == 'container_name'
        assert call_args.args[1] == 'blob_name.jpg'
        assert call_args.kwargs['stream'] == test_stream
        assert call_args.kwargs['content_settings'].content_type == 'image/jpg'

    def test_catches_and_raises_exception(self, mocker):
        settings = self.setup_settings_for_test()
        test_exception = Exception("test exception")

        mocked_blob_service = mocker.patch('azure.storage.blob.BlockBlobService')
        instance = mocked_blob_service.return_value
        instance.get_blob_to_stream.side_effect = test_exception

        with pytest.raises(Exception) as ex:
            read_blob_to_stream(settings, 'container_name', 'blob_name.jpg')
        assert ex != test_exception
        assert ex.value.args[1] == test_exception
