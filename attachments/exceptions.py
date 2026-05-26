class VirusFoundException(Exception):
    """Exception raised for detecting a virus in a file upload"""
    pass

class InvalidExtensionException(Exception):
    """Exception raised for an attachment with an invalid extension"""
    pass

class InvalidFileTypeException(Exception):
    """Exception raised for an attachment of an invalid type"""
    pass

class FileSizeException(Exception):
    """Exception raised for an attachment that is too large"""
    pass
