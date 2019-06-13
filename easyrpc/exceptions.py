
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

class PyVersionError(Exception):
	"""Raised when you import this library in python version 3.5 or below."""
	pass

class EventLoopError(Exception):
	"""Raised when automaticly catch event loop failed """
	pass

class ConnectingError(Exception):
	"""Raised when couldn't make connect to server"""
	pass