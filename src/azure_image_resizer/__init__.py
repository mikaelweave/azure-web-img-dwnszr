import copy, logging, os
import azure.functions as func

from .BlobHelpers import not_website_image, read_blob_to_stream, save_stream_to_cloud, save_image_metadata
from .CloudImage import CloudImage
from .Settings import Settings


def main(event: func.EventGridEvent):

    logging.info(f'Python AzureImageSizerSrcset processed an event: {event.subject}')

    try:
        # Get inputs
        container_name = event.subject.split('/blobs/')[0].split('containers/')[1]
        blob_name = event.subject.split('/blobs/')[1]

        # Check settings, filter non-applicable events
        settings = Settings(os.environ)
        if not_website_image(container_name, blob_name): return

        # Load image from Azure
        orig_stream = read_blob_to_stream(blob_name)
        cloud_image = CloudImage(name=blob_name, stream=orig_stream)

        # Filter list of widths to resize so we only downscale
        resize_widths = filter(lambda w: w <= cloud_image.width(), settings.image_sizes)

        # Resize images (down size only)
        resized_images = [copy.copy(cloud_image.resize(width)) for width in resize_widths]

        # Save resized streams to Azure
        for image in resized_images:
            save_stream_to_cloud(settings, container_name, image.name, image.stream)
            save_stream_to_cloud(settings, container_name, image.webp_name, image.webp_stream)

        # Save metadata file for applications consuming images
        save_image_metadata(settings, "data", blob_name, resize_widths)
    except Exception as ex:
        message, exception = ex.args
        logging.error(message, exception)
