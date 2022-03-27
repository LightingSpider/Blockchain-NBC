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

class UnableResolveConflict(Exception):
    def __init__(self, err: str):
        self.err = err

    def __str__(self):
        return self.err

class NoValidationNeeded(Exception):
    def __init__(self, err: str):
        self.err = err

    def __str__(self):
        return self.err

class InvalidBlockCommonTransactions(Exception):
    def __init__(self, err: str, block_for_validation: dict, common_trans_ids: [str] = None):
        self.err = err
        self.block_for_validation = block_for_validation
        self.common_trans_ids = common_trans_ids

    def __str__(self):
        return self.err

class TransactionAlreadyAdded(Exception):
    def __init__(self, err: str):
        self.err = err

    def __str__(self):
        return self.err
