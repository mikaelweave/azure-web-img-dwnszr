import json, logging, os, re, io, json, PIL, time, random
import azure.functions as func
from PIL import Image
from azure.storage.blob import BlockBlobService, PublicAccess, baseblobservice, ContentSettings
from azure.common import AzureConflictHttpError

# Debug locally http://localhost:7071/runtime/webhooks/EventGrid?functionName=AzureImageSizerSrcset
# ngrok http -host-header=localhost 7071

def main(event: func.EventGridEvent):

    #1. Figure out values from input
    logging.info('Python AzureImageSizerSrcsetprocessed an event: %s', event.subject)
    blob_url = event.get_json()['url']
    blob_name = event.subject.split('/blobs/')[1]
    parts = blob_name.split('.')
    container_name = event.subject.split('/blobs/')[0].split('containers/')[1]

    # 1.5 Some input checking
    already_processed = re.compile(r'.*_[0-9]+w\.[a-zA-Z]+$')
    if container_name.startswith("$") or container_name.startswith("azure") or container_name in ['function-releases', 'scm-releases']:
        logging.info(f'Not processing blob {blob_name} in system container {container_name}')
        return
    if already_processed.match(blob_name):
        logging.info(f'Blob {blob_name} in container {container_name} already processed')
        return
    if not blob_name.lower().endswith(('jpg', 'jpeg', 'png')):
        logging.info(f'Skipping non-image blob {blob_name} in container {container_name}')
        return

    # 2. Read Blob file into a stream for us to use
    try:
        block_blob_service = BlockBlobService(connection_string=os.environ["AzureWebJobsStorage"])
        stream = io.BytesIO()
        block_blob_service.get_blob_to_stream(container_name, blob_name, stream=stream)
    except Exception as ex:
        logger.error(f'Error getting blob {blob_name}. {ex}')
        return

    # 3. Open blob as image and LOOP
    try:
        image = Image.open(stream)
    except Exception as ex:
        logger.error(f'Error opening image from stream. {ex}')

    resized_images = {}
    parts = blob_name.split('.')
    pillow_image_type = parts[-1].upper().replace("JPG", "JPEG")

    sizes = os.environ["ImageSizes"].split(',')
    for sizeStr in sizes:
        size = int(sizeStr.strip())
        resized_path = f'{".".join(parts[:-1])}_{size}w.{parts[-1]}'
        webp3_path = f'{".".join(parts[:-1])}_{size}w.webp'
        jpeg2k_path = f'{".".join(parts[:-1])}_{size}w.jp2'

        if image.width <= size:
            continue

        img = image.copy()
        wpercent = (size / float(img.size[0]))
        hsize = int((float(img.size[1]) * float(wpercent)))
        img = img.resize((size, hsize), PIL.Image.ANTIALIAS)
        
        # Resize in same format
        try:
            resized_stream = io.BytesIO()
            img.save(resized_stream, format=pillow_image_type)
            resized_stream.seek(0)
            content_settings = ContentSettings(content_type=f'image/{pillow_image_type.lower()}')
            block_blob_service.create_blob_from_stream(container_name, resized_path, stream=resized_stream, content_settings=content_settings)
            if parts[-1] in resized_images:
                resized_images[parts[-1]].append(size)
            else:
                resized_images[parts[-1]] = [size]
        except Exception as ex:
            logger.error(f'Error converting {resized_path} to size {size}. {ex}')

        # Resize in WEBP
        try:
            webp3_stream = io.BytesIO()
            img.save(webp3_stream, format='webp', quality = 70)
            webp3_stream.seek(0)
            content_settings = ContentSettings(content_type='image/webp')
            block_blob_service.create_blob_from_stream(container_name, webp3_path, stream=webp3_stream, content_settings=content_settings)
            if "webp" in resized_images:
                resized_images["webp"].append(size)
            else:
                resized_images["webp"] = [size]
        except Exception as ex:
            logger.error(f'Error converting {resized_path} to webp. {ex}')

        """try:
            img.save(jpeg2k_path, 'JPEG2000', quality_mode='dB', quality_layers=[38])
            if "jp2" in resized_images:
                resized_images["jp2"].append(size)
            else:
                resized_images["jp2"] = [size]
        except Exception as ex:
            print(f'Error converting {resized_path} to jpeg2k. {ex}')"""

    srcset_path = (os.path.dirname(blob_name) + '/' + 'srcsets.json').lstrip('/')
    if not block_blob_service.exists(container_name, srcset_path):
        content_settings = ContentSettings(content_type='application/json')
        block_blob_service.create_blob_from_text(container_name, srcset_path, "{}", content_settings=content_settings)

    def write_srcset():
        try:
            lease_id = block_blob_service.acquire_blob_lease(container_name, srcset_path, 15)
            srcsets = block_blob_service.get_blob_to_text(container_name, srcset_path)

            srcsets_json = json.loads(srcsets.content)
            srcsets_json[f'{container_name}/{blob_name}'] = resized_images

            block_blob_service.create_blob_from_text(container_name, srcset_path, json.dumps(srcsets_json), lease_id=lease_id)
            block_blob_service.release_blob_lease(container_name, srcset_path, lease_id)
            return True
        except AzureConflictHttpError as ex:
            return False;

    # Try to write back to srcset file. 
    # Since this is a file and not a db, add retry logic
    try:
        while True:
            if (write_srcset()):
                break
            time.sleep (random.randint(1,3056) / 1000.0);
    except Exception as ex:
        logger.error(f'Exception encountered writing back to srcset file. {ex}')