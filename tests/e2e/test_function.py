from PIL import Image
import io, json, time
import azure.storage.blob as azblob


# Helper to create in memory test image
def create_test_image(width, height):
    stream = io.BytesIO()
    image = Image.new('RGB', size=(width, height), color=(69, 69, 69))
    image.save(stream, 'jpeg')
    stream.seek(0)
    return stream


def delete_blob_if_exist(block_blob_service, continer_name, blob_name):
    if block_blob_service.exists(continer_name, blob_name):
        block_blob_service.delete_blob(continer_name, blob_name)


class FullE2ETestCase:
    def test_function_resizes_image_basic(self, settings):
        test_image = create_test_image(1000, 1000)
        test_image2 = create_test_image(1000, 1000)

        # Delete any blobs from past tests
        block_blob_service = azblob.BlockBlobService(connection_string=settings.storage_connection_string)
        for size in filter(lambda w: w <= 1000, settings.image_sizes):
            delete_blob_if_exist(block_blob_service, settings.image_container_name, f'test1_{size}w.jpg')
            delete_blob_if_exist(block_blob_service, settings.image_container_name, f'nested/test1_{size}w.jpg')
        delete_blob_if_exist(block_blob_service, settings.image_container_name, 'nested/test1.jpg')

        # Upload our image, triggering the function via a `BlobCreated` event
        block_blob_service.create_blob_from_stream(settings.image_container_name, 'test1.jpg', test_image)
        block_blob_service.create_blob_from_stream(settings.image_container_name, 'nested/test1.jpg', test_image2)

        # Give our resizer function some time to...resize
        time.sleep(30)

        # Look for resized images
        blobs = block_blob_service.list_blobs(settings.image_container_name)

        # Expect our resized blobs
        assert any(x.name == 'test1.jpg' for x in blobs.items)
        assert any(x.name == 'nested/test1.jpg' for x in blobs.items)
        for size in filter(lambda w: w <= 1000, settings.image_sizes):
            assert any(x.name == f'test1_{size}w.jpg' for x in blobs.items)
            assert any(x.name == f'test1_{size}w.webp' for x in blobs.items)
            assert any(x.name == f'nested/test1_{size}w.jpg' for x in blobs.items)
            assert any(x.name == f'nested/test1_{size}w.webp' for x in blobs.items)

        # Expect our metadata file
        metadata_json = block_blob_service.get_blob_to_text(settings.metadata_container_name, 'srcsets.json')
        metadata_json_nested = block_blob_service.get_blob_to_text(settings.metadata_container_name, 'nested/srcsets.json')

        # Parse JSON, check contents
        metadata = json.loads(metadata_json.content)
        metadata_nested = json.loads(metadata_json_nested.content)

        # Check root metadata
        assert f'{settings.image_container_name}/test1.jpg' in metadata
        assert 'jpg' in metadata[f'{settings.image_container_name}/test1.jpg']
        assert 'webp' in metadata[f'{settings.image_container_name}/test1.jpg']
        assert metadata[f'{settings.image_container_name}/test1.jpg']['jpg'] == list(filter(lambda w: w <= 1000, settings.image_sizes))
        assert metadata[f'{settings.image_container_name}/test1.jpg']['webp'] == list(filter(lambda w: w <= 1000, settings.image_sizes))

        # Check nested metadata
        assert f'{settings.image_container_name}/nested/test1.jpg' in metadata_nested
        assert 'jpg' in metadata_nested[f'{settings.image_container_name}/nested/test1.jpg']
        assert 'webp' in metadata_nested[f'{settings.image_container_name}/nested/test1.jpg']
        assert metadata_nested[f'{settings.image_container_name}/nested/test1.jpg']['jpg'] == list(filter(lambda w: w <= 1000, settings.image_sizes))
        assert metadata_nested[f'{settings.image_container_name}/nested/test1.jpg']['webp'] == list(filter(lambda w: w <= 1000, settings.image_sizes))
