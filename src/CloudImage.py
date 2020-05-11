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

    def downsize(self, width):
        if self.image.width < int(width):
            return

        try:
            self.name = f'{".".join(self.name.split(".")[:-1])}_{width}w.{self.extension}'

            # Having the same size imaged named as a resized image is still useful in most applications
            if self.image.width == int(width):
                return self

            wpercent = (width / float(self.image.size[0]))
            hsize = int((float(self.image.size[1]) * float(wpercent)))
            self.image = self.image.resize((width, hsize), Image.ANTIALIAS)

            self.stream = self.__image_to_stream()
            return self
        except Exception as ex:
            raise Exception('Error resizing image {blob_name} in {container_name} to width {width}', ex)

    @property
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
            self.image.save(stream, format=self.extension.upper().replace('JPG', 'JPEG'), quality=75, optimize=True)
        elif format == 'webp':
            self.image.save(stream, format='webp', quality=75, optimize=True)
        else:
            raise Exception(f'Unknown format {format} provided while converting image to stream')

        stream.seek(0)
        return stream
