class Settings:
    def __init__(self, environ):
        if "AzureWebJobsStorage" in environ:
            self.storage_connection_string = environ["AzureWebJobsStorage"]
        else:
            raise Exception("AzureWebJobsStorage must be set to use this function")

        if "ImageSizes" in environ:
            self.image_sizes = environ["ImageSizes"]
        else:
            raise Exception("ImageSizes must be set to use this function")
