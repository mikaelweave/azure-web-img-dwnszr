import io
from PIL import Image

from src.CloudImage import CloudImage


# Helper to create in memory test image
def create_test_image():
    stream = io.BytesIO()
    image = Image.new('RGB', size=(100, 100), color=(69, 69, 69))
    image.save(stream, 'jpeg')
    stream.seek(0)
    return stream


class CloudImageTestCase:
    def test_creates_image(self):
        # Arrange
        stream = create_test_image()

        # Act
        ci = CloudImage(name="MyImage.jpg", stream=stream)

        # Assert
        assert ci.stream == stream
        assert ci.image.size == (100, 100)
        assert ci.width == 100

    def test_creates_webp_image(self):
        # Arrange
        stream = create_test_image()
        ci = CloudImage(name="MyImage.jpg", stream=stream)

        # Act
        image = Image.open(ci.webp_stream)

        # Assert
        assert image.format.lower() == 'webp'
        assert image.size == (100, 100)
        assert ci.webp_name == "MyImage.webp"

    def test_downsize(self, mocker):
        # Arrange
        stream = create_test_image()
        ci = CloudImage(name="MyImage.jpg", stream=stream)

        # Act
        ci.downsize(50)

        # Assert
        assert ci.stream != stream
        assert ci.image.size == (50, 50)
        assert ci.name == "MyImage_50w.jpg"

    def test_upsize_doesnt_modify(self, mocker):
        # Arrange
        stream = create_test_image()
        ci = CloudImage(name="MyImage.jpg", stream=stream)

        # Act
        ci.downsize(1000)

        # Assert
        assert ci.stream == stream
        assert ci.image.size == (100, 100)
