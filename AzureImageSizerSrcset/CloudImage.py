import PIL, os, re, io, logging

@dataclass
class CloudImage:
    # input properties
    name: str
    stream: io.BytesIO

    # calculated properties
    extension: str = field(init=False)
    image: PIL.Image = field(default=None)

    def __post_init__(self):
        self.extension = self.name.split('.')[-1]
        self.image = self.__stream_to_image()

    def resize(self, width):
        if self.image.width <= width:
            return

        try:
            wpercent = (width / float(self.image.size[0]))
            hsize = int((float(self.image.size[1]) * float(wpercent)))
            return new_image.resize((width, hsize), PIL.Image.ANTIALIAS)
        except Exception as ex:
            raise Exception("Error resizing image {blob_name} in {container_name} to width {width}", ex)

        self.name = f'{self.name.split('.')[:-1]}_{width}w.{self.extension}'
        self.stream = self.__image_to_stream(self.image)

    def width():
        return self.image.size[0]
        
    @property
    def webp_stream(self):
        return __image_to_stream('webp')

    @property
    def webp_name(self):
        return re.sub(f'{self.extension}$', 'webp', self.name)

    def __stream_to_image(self):
        try:
            return PIL.Image.open(self.stream)
        except Exception as ex:
            logger.error(f'Error opening image {self.name} from stream.', ex)

    def __image_to_stream(self, format=self.extension):
        stream = io.BytesIO()
        if format == self.extension:
            img.save(resized_stream, format=self.extension.upper().replace("JPG", "JPEG"))
        if format == 'webp':
            image.save(stream, format='webp', quality = 70)
        else:
            raise Exception(f'Unknown format {format} provided while converting image to stream')
        stream.seek(0)
        return stream
