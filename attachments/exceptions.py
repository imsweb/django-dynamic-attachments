class VirusFoundException(Exception):
    """Exception raised for detecting a virus in a file upload"""
    pass

class FileSizeException(Exception):
    """Exception raised for too large file size in a file upload"""
    pass

class FileTypeException(Exception):
    """Exception raised for unallowable type in a file upload"""
    pass
