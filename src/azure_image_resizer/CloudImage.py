import io, re
from dataclasses import dataclass, field
from PIL import Image


@dataclass
class CloudImage:
    # input properties
    name: str
    stream: io.BytesIO

    # calculated properties
    extension: str = field(init=False)
    image: Image = field(default=None)

    def __post_init__(self):
        self.extension = self.name.split('.')[-1]
        self.image = self.__stream_to_image()

    def resize(self, width):
        if self.image.width <= width:
            return

        try:
            wpercent = (width / float(self.image.size[0]))
            hsize = int((float(self.image.size[1]) * float(wpercent)))
            self.image.resize((width, hsize), Image.ANTIALIAS)

            self.name = f'{self.name.split(".")[:-1]}_{width}w.{self.extension}'
            self.stream = self.__image_to_stream(self.image)
            return self
        except Exception as ex:
            raise Exception('Error resizing image {blob_name} in {container_name} to width {width}', ex)

    def width(self):
        return self.image.size[0]

    @property
    def webp_stream(self):
        return self.__image_to_stream('webp')

    @property
    def webp_name(self):
        return re.sub(f'{self.extension}$', 'webp', self.name)

    def __stream_to_image(self):
        try:
            return Image.open(self.stream)
        except Exception as ex:
            raise Exception('Error opening image {self.name} from stream.', ex)

    def __image_to_stream(self, format=None):
        stream = io.BytesIO()
        if format in [None, self.extension]:
            self.image.save(stream, format=self.extension.upper().replace('JPG', 'JPEG'))
        if format == 'webp':
            self.image.save(stream, format='webp', quality=70)
        else:
            raise Exception(f'Unknown format {format} provided while converting image to stream')

        stream.seek(0)
        return stream
