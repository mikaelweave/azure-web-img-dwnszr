import io, pytest
from unittest.mock import MagicMock
from azure.common import AzureConflictHttpError

from src.BlobHelpers import not_website_image, read_blob_to_stream, save_stream_to_cloud, save_image_metadata
from src.Settings import Settings


def setup_settings_for_test():
    test_env = {}
    test_env['StorageAccountConnectionString'] = 'DefaultEndpointsProtocol=https;EndpointSuffix=core.windows.net;AccountName=test;AccountKey=test'
    test_env['ImageContainerName'] = '$web'
    test_env['ImageSizes'] = '1,2,3'
    return Settings(test_env)


class NotWebsiteImageTestCase:
    def test_valid_blob(self):
        settings = setup_settings_for_test()
        assert not not_website_image(settings, '$web', 'test.jpg')
        assert not not_website_image(settings, '$web', 'test.jpeg')
        assert not not_website_image(settings, '$web', 'test.png')
        assert not not_website_image(settings, '$web', 'test.JPG')
        assert not not_website_image(settings, '$web', 'test.JPEG')
        assert not not_website_image(settings, '$web', 'test.PNG')

    def test_invalid_continer(self):
        settings = setup_settings_for_test()
        assert not_website_image(settings, 'data', 'test.jpg')

    def test_already_processed(self):
        settings = setup_settings_for_test()
        assert not_website_image(settings, '$web', 'test_100w.jpg')


class ReadBlobToStreamTestCase:
    def assign_test_stream(self, continaer_name, blob_name, stream):
        stream.truncate()
        stream.write(b'test bytes')
        stream.seek(0)
        return MagicMock('azure.storage.blob.Blob')

    def test_returns_stream(self, mocker):
        settings = setup_settings_for_test()

        mocked_blob_service = mocker.patch('azure.storage.blob.BlockBlobService')
        instance = mocked_blob_service.return_value
        instance.get_blob_to_stream = self.assign_test_stream
        spy = mocker.spy(instance, 'get_blob_to_stream')

        assert read_blob_to_stream(settings, 'container_name', 'blob_name.jpg').read() == b'test bytes'
        spy.assert_called_once_with('container_name', 'blob_name.jpg', stream=mocker.ANY)

    def test_catches_and_raises_exception(self, mocker):
        settings = setup_settings_for_test()
        test_exception = Exception("test exception")

        mocked_blob_service = mocker.patch('azure.storage.blob.BlockBlobService')
        instance = mocked_blob_service.return_value
        instance.get_blob_to_stream.side_effect = test_exception

        with pytest.raises(Exception) as ex:
            read_blob_to_stream(settings, 'container_name', 'blob_name.jpg')
        assert ex != test_exception
        assert ex.value.args[1] == test_exception


class SaveStreamToCloudTestCase:
    def test_stream_saves_and_calls_service(self, mocker):
        settings = setup_settings_for_test()
        test_stream = io.BytesIO(b'test bytes')

        mocked_blob_service = mocker.patch('azure.storage.blob.BlockBlobService')
        spy = mocker.spy(mocked_blob_service.return_value, 'create_blob_from_stream')
        save_stream_to_cloud(settings, 'container_name', 'blob_name.jpg', test_stream)

        spy.assert_called_once()
        call_args = spy.call_args
        assert call_args.args[0] == 'container_name'
        assert call_args.args[1] == 'blob_name.jpg'
        assert call_args.kwargs['stream'] == test_stream
        assert call_args.kwargs['content_settings'].content_type == 'image/jpg/resized'

    def test_catches_and_raises_exception(self, mocker):
        settings = setup_settings_for_test()
        test_exception = Exception("test exception")

        mocked_blob_service = mocker.patch('azure.storage.blob.BlockBlobService')
        instance = mocked_blob_service.return_value
        instance.get_blob_to_stream.side_effect = test_exception

        with pytest.raises(Exception) as ex:
            read_blob_to_stream(settings, 'container_name', 'blob_name.jpg')
        assert ex != test_exception
        assert ex.value.args[1] == test_exception


class SaveImageMetadataTestCase:
    def test_creates_metadata_blob_if_not_exist(self, mocker):
        # Arrange
        settings = setup_settings_for_test()
        mocked_blob_service = mocker.patch('azure.storage.blob.BlockBlobService')
        mocked_blob_service.return_value.exists.return_value = False
        mocked_blob_service.return_value.get_blob_to_text.return_value.content = '{}'
        spy = mocker.spy(mocked_blob_service.return_value, 'create_blob_from_text')

        # Act
        save_image_metadata(settings, 'container_name', 'folder/blob_name.jpg', [1])

        # Assert
        assert spy.call_count == 2
        call_args = spy.call_args_list[0]
        assert call_args.args[0] == 'data'
        assert call_args.args[1] == 'srcsets.json'
        assert call_args.kwargs['text'] == '{}'
        assert call_args.kwargs['content_settings'].content_type == 'application/json'

    def test_writes_blob_to_azure(self, mocker):
        # Arrange
        settings = setup_settings_for_test()
        mocked_blob_service = mocker.patch('azure.storage.blob.BlockBlobService')
        mocked_blob_service.return_value.exists.return_value = True
        mocked_blob_service.return_value.get_blob_to_text.return_value.content = '{}'
        create_blob_spy = mocker.spy(mocked_blob_service.return_value, 'create_blob_from_text')

        mocked_blob_service.return_value.acquire_blob_lease.return_value = 'm'
        acquire_lease_spy = mocker.spy(mocked_blob_service.return_value, 'acquire_blob_lease')
        release_lease_spy = mocker.spy(mocked_blob_service.return_value, 'release_blob_lease')

        # Act
        save_image_metadata(settings, 'container_name', 'blob_name.jpg', [1])

        # Assert
        expected_text = '{"container_name/blob_name.jpg": {"jpg": [1], "webp": [1]}}'
        create_blob_spy.assert_called_once_with('data', 'srcsets.json', text=expected_text, lease_id='m')
        acquire_lease_spy.assert_called_once_with('data', 'srcsets.json', 15)
        release_lease_spy.assert_called_once_with('data', 'srcsets.json', lease_id='m')

    def test_retry(self, mocker):
        # Arrange
        settings = setup_settings_for_test()
        mocked_blob_service = mocker.patch('azure.storage.blob.BlockBlobService')
        mocked_blob_service.return_value.exists.return_value = True
        mocked_blob_service.return_value.get_blob_to_text.return_value.content = '{}'
        acquire_lease_spy = mocker.spy(mocked_blob_service.return_value, 'acquire_blob_lease')
        release_lease_spy = mocker.spy(mocked_blob_service.return_value, 'release_blob_lease')

        instance = mocked_blob_service.return_value
        instance.acquire_blob_lease.side_effect = [AzureConflictHttpError(message="message", status_code=409), 13]

        save_image_metadata(settings, 'container_name', 'blob_name.jpg', settings.image_sizes)

        assert acquire_lease_spy.call_count == 2
        assert acquire_lease_spy.call_args_list[0].args[0] == 'data'
        assert acquire_lease_spy.call_args_list[0].args[1] == 'srcsets.json'
        assert acquire_lease_spy.call_args_list[1].args[0] == 'data'
        assert acquire_lease_spy.call_args_list[1].args[1] == 'srcsets.json'
        release_lease_spy.assert_called_once_with('data', 'srcsets.json', lease_id=13)

    def test_catches_and_raises_exception(self, mocker):
        settings = setup_settings_for_test()
        test_exception = Exception("test exception")

        mocked_blob_service = mocker.patch('azure.storage.blob.BlockBlobService')
        instance = mocked_blob_service.return_value
        instance.get_blob_to_text.side_effect = test_exception

        with pytest.raises(Exception) as ex:
            save_image_metadata(settings, 'container_name', 'blob_name.jpg', [1, 2, 3])
        assert ex != test_exception
        assert ex.value.args[1] == test_exception
