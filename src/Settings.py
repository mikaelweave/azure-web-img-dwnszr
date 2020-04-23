class Settings:

    def __init__(self, environ):
        if 'AzureWebJobsStorage' in environ:
            self.__storage_connection_string = environ['AzureWebJobsStorage']
        else:
            raise Exception('AzureWebJobsStorage must be set to use this function')

        if 'ImageSizes' in environ:
            self.__image_sizes = [int(i.strip()) for i in environ['ImageSizes'].split(',')]
        else:
            raise Exception('ImageSizes must be set to use this function')

        self.__image_container_name = ''
        if 'ImageContainerName' in environ:
            self.__image_container_name = environ['ImageContainerName']

        self.__metadata_container_name = 'data'
        if 'MetadataContainerName' in environ:
            self.__metadata_container_name = environ['MetadataContainerName']

    @property
    def storage_connection_string(self):
        return self.__storage_connection_string

    @property
    def image_sizes(self):
        return self.__image_sizes

    @property
    def image_container_name(self):
        return self.__image_container_name

    @property
    def metadata_container_name(self):
        return self.__metadata_container_name
