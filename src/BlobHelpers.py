import io, json, logging, random, re, time
import azure.storage.blob as azblob
from azure.common import AzureConflictHttpError


def not_website_image(settings, container_name, blob_name):
    already_processed = re.compile(r'.*_[0-9]+w\.[a-zA-Z]+$')

    if container_name != settings.image_container_name:
        logging.info(f'Not processing blob {blob_name} in ignored container {container_name}')
        return True

    if already_processed.match(blob_name):
        logging.info(f'Blob {blob_name} in container {container_name} already processed')
        return True

    if not blob_name.lower().endswith(('jpg', 'jpeg', 'png')):
        logging.info(f'Skipping non-image blob {blob_name} in container {container_name}')
        return True

    return False


def read_blob_to_stream(settings, container_name, blob_name):
    try:
        block_blob_service = azblob.BlockBlobService(connection_string=settings.storage_connection_string)
        stream = io.BytesIO()
        block_blob_service.get_blob_to_stream(container_name, blob_name, stream=stream)
        return stream
    except Exception as ex:
        raise Exception(f'Error getting blob {blob_name} from container {container_name}.', ex)


def save_stream_to_cloud(settings, container_name, blob_name, stream):
    try:
        block_blob_service = azblob.BlockBlobService(connection_string=settings.storage_connection_string)
        content_settings = azblob.ContentSettings(content_type=f'image/{blob_name.split(".")[-1]}')
        block_blob_service.create_blob_from_stream(container_name, blob_name, stream=stream, content_settings=content_settings)
    except Exception as ex:
        raise Exception(f'Error saving blob {blob_name} to stream.', ex)


def save_image_metadata(settings, image_container_name, image_blob_name, widths):
    # if there are no resized images do nothing
    if len(widths) == 0: return

    # Metadata blob structure should match image blob structure
    metadata_blob_name = re.sub(f'[^/]+$', 'srcsets.json', image_blob_name)
    extension = image_blob_name.split('.')[-1]

    # Get blob service and create metablob if not exist
    block_blob_service = azblob.BlockBlobService(connection_string=settings.storage_connection_string)
    if not block_blob_service.exists(image_container_name, metadata_blob_name):
        content_settings = azblob.ContentSettings(content_type='application/json')
        block_blob_service.create_blob_from_text(settings.metadata_container_name, metadata_blob_name, text='{}', content_settings=content_settings)

    # Retry logic for writing metadata. Useful with concurrent function executions
    try:
        while True:
            try:
                # Get and convert existing metadata blob
                lease_id = block_blob_service.acquire_blob_lease(settings.metadata_container_name, metadata_blob_name, 15)
                cloud_json_str = block_blob_service.get_blob_to_text(settings.metadata_container_name, metadata_blob_name).content
                cloud_json = json.loads(cloud_json_str)

                # Append metadata for our image sizes
                cloud_json[f'{image_container_name}/{image_blob_name}'] = {extension: widths, "webp": widths}

                # Write metadata blob
                block_blob_service.create_blob_from_text(settings.metadata_container_name, metadata_blob_name, text=json.dumps(cloud_json), lease_id=lease_id)
                block_blob_service.release_blob_lease(settings.metadata_container_name, metadata_blob_name, lease_id=lease_id)

                break
            except AzureConflictHttpError:
                time.sleep(random.randint(1, 3056) / 1000.0)
    except Exception as ex:
        raise Exception(f'Exception encountered writing back to metadata file for blob {image_blob_name}.', ex)
