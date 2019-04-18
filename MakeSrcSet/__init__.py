import json, logging, os, re, io, json, PIL, time, random
import azure.functions as func
from PIL import Image
from azure.storage.blob import BlockBlobService, PublicAccess, baseblobservice
from azure.common import AzureConflictHttpError

# Debug locally http://localhost:7071/runtime/webhooks/EventGrid?functionName=MakeSrcSet
# ngrok http -host-header=localhost 7071
#import PIL
#from PIL import Image

#def main(event: func.EventGridEvent, inputblob: func.InputStream):
def main(event: func.EventGridEvent):
    print("I made it!!")
    result = json.dumps({
        'id': event.id,
        'data': event.get_json(),
        'topic': event.topic,
        'subject': event.subject,
        'event_type': event.event_type,
    })

    #1. Figure out values from input
    logging.info('Python EventGrid trigger processed an event: %s', result)
    blob_url = event.get_json()['url']
    blob_name = event.subject.split('/blobs/')[1]
    parts = blob_name.split('.')
    container_name = event.subject.split('/blobs/')[0].split('containers/')[1]

    # 1.5 Some input checking
    already_processed = re.compile(r'.*_[0-9]+w\.[a-zA-Z]+$')
    if container_name.startswith("$") or container_name.startswith("azure") or already_processed.match(blob_name):
        return

    # 2. Read Blob file (the File name is the same as the item name from Queue message )
    block_blob_service = BlockBlobService(connection_string=os.environ["AzureWebJobsStorage"])

    stream = io.BytesIO()
    try:
        block_blob_service.get_blob_to_stream(container_name, blob_name, stream=stream)
    except Exception as ex:
        print(f'Error getting blob {blob_name}. {ex}')
        return

    # 3. Open blob as image and LOOP
    image = Image.open(stream)
    resized_images = {}
    parts = blob_name.split('.')
    pillow_image_type = parts[-1].upper().replace("JPG", "JPEG")

    for size in [480, 768, 1200, 1400, 1700, 2000, 2436]:        
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
        resized_stream = io.BytesIO()
        img.save(resized_stream, format=pillow_image_type)
        resized_stream.seek(0)
        block_blob_service.create_blob_from_stream(container_name, resized_path, stream=resized_stream)
        if parts[-1] in resized_images:
            resized_images[parts[-1]].append(size)
        else:
            resized_images[parts[-1]] = [size]

        # Resize in WEBP
        try:
            webp3_stream = io.BytesIO()
            img.save(webp3_stream, format='webp', quality = 70)
            webp3_stream.seek(0)
            block_blob_service.create_blob_from_stream(container_name, webp3_path, stream=webp3_stream)
            if "webp" in resized_images:
                resized_images["webp"].append(size)
            else:
                resized_images["webp"] = [size]
        except Exception as ex:
            print(f'Error converting {resized_path} to webp. {ex}')

        """try:
            img.save(jpeg2k_path, 'JPEG2000', quality_mode='dB', quality_layers=[38])
            if "jp2" in resized_images:
                resized_images["jp2"].append(size)
            else:
                resized_images["jp2"] = [size]
        except Exception as ex:
            print(f'Error converting {resized_path} to jpeg2k. {ex}')"""
    
    if not block_blob_service.exists("$web", "srcsets.json"):
        block_blob_service.create_blob_from_text("$web", "srcsets.json", "{}")

    def write_srcset():
        try:
            lease_id = block_blob_service.acquire_blob_lease("$web", "srcsets.json", 15)
            srcsets = block_blob_service.get_blob_to_text("$web", "srcsets.json")

            srcsets_json = json.loads(srcsets.content)
            srcsets_json[f'{container_name}/{blob_name}'] = resized_images

            block_blob_service.create_blob_from_text("$web", "srcsets.json", json.dumps(srcsets_json), lease_id=lease_id)
            block_blob_service.release_blob_lease("$web", "srcsets.json", lease_id)
            return True
        except AzureConflictHttpError as ex:
            return False;

    try:
        while True:
            if (write_srcset()):
                break
            time.sleep (random.randint(1,3056) / 1000.0);
    except Exception as ex:
        print(f'Exception encountered writing back to srcset. {ex}')