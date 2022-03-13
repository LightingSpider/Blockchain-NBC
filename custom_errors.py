class UnauthorizedNode(Exception):
    def __init__(self, err: str):
        self.err = err

    def __str__(self):
        return self.err

class InvalidHash(Exception):
    def __init__(self, err: str):
        self.err = err

    def __str__(self):
        return self.err

class InvalidUTXOs(Exception):
    def __init__(self, err: str):
        self.err = err

    def __str__(self):
        return self.err

class InsufficientAmount(Exception):
    def __init__(self, err: str):
        self.err = err

    def __str__(self):
        return self.err

class InvalidPreviousHashKey(Exception):
    def __init__(self, err: str):
        self.err = err

    def __str__(self):
        return self.err

class InvalidMessageType(Exception):
    def __init__(self, message_type: str):
        self.message_type = message_type

    def __str__(self):
        return f"Invalid message type '{self.message_type}'"
