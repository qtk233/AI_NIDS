class ModelNotLoadedError(Exception):
    """Raised when detection is requested before model is loaded."""
    pass


class InvalidPcapError(Exception):
    """Raised when uploaded file is not a valid pcap."""
    pass


class DetectionError(Exception):
    """Raised when detection pipeline fails."""
    pass
