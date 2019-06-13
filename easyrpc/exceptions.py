
class SerializeError(Exception):
    """Raised when sending message can not be serialize."""
    pass

class DecodingError(Exception):
    """Raised when successfully recv message but have a decoding error."""
    pass

class BusyError(Exception):
    """Raised when incomming message count larger than overflow control."""
    pass

class InstantiationError(Exception):
    """Raised if you call a async function but did not instantiate client."""
    pass