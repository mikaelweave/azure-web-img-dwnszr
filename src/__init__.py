import copy, logging, os
import azure.functions as func

from . import BlobHelpers
from . import CloudImage
from . import Settings


def main(event: func.EventGridEvent):

    logging.info(f'Python azure_image_resizer processed an event: {event.subject}')

    # Get inputs
    container_name = event.subject.split('/blobs/')[0].split('containers/')[1]
    blob_name = event.subject.split('/blobs/')[1]

    # Check settings, filter non-applicable events
    settings = Settings.Settings(os.environ)
    if BlobHelpers.not_website_image(settings, container_name, blob_name): return

    # Load image from Azure
    orig_stream = BlobHelpers.read_blob_to_stream(settings, container_name, blob_name)
    cloud_image = CloudImage.CloudImage(name=blob_name, stream=orig_stream)

    # Filter list of widths to resize so we only downscale
    downsize_widths = list(filter(lambda w: w <= cloud_image.width, settings.image_sizes))

    # Resize images (down size only)
    downsized_images = [copy.copy(cloud_image).downsize(width) for width in downsize_widths]

    # Save resized streams to Azure
    for image in downsized_images:
        BlobHelpers.save_stream_to_cloud(settings, container_name, image.name, image.stream)
        BlobHelpers.save_stream_to_cloud(settings, container_name, image.webp_name, image.webp_stream)

    # Save metadata file for applications consuming images
    BlobHelpers.save_image_metadata(settings, container_name, blob_name, downsize_widths)
