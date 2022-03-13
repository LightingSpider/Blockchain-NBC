import datetime
from transaction import Transaction
from Crypto.Hash import SHA256


class Block:

    def __init__(self, prev_hash: str, transaction_list: [Transaction], hash_key: str = None, nonce: bytes = None):

        # When we create a block we know its previous block
        self.previous_hash = prev_hash
        self.timestamp = str(datetime.datetime.now())

        # This a list which contains Transaction objects. At first is empty.
        self.list_of_transactions = transaction_list

        # These values will be known when the block is mined from some node.
        self.hash_key = hash_key
        self.nonce = nonce

    # Converts the block's transactions and previous_hash into a bytearray
    def bytearray_before_nonce(self) -> bytearray:

        # Convert all the info of the block into bytearray, in order to hash it with SHA256
        block_bytearray = bytearray()

        # We will use the transaction_ids and not the Transaction Objects
        for trans in self.list_of_transactions:

            # Add it to the bytearray by converting the string into bytes
            block_bytearray.extend(trans.transaction_id.hexdigest().encode('utf-8'))

        # Add the previous_hash & timestamp into the bytearray
        block_bytearray.extend(self.previous_hash.encode('utf-8'))
        block_bytearray.extend(self.timestamp.encode('utf-8'))

        return block_bytearray

    # Get the hash_key of the block in order to secure the object's attributes
    def get_hash(self) -> str:
        return self.hash_key

    def get_nonce(self) -> bytes:
        return self.nonce

    def get_prev_hash(self) -> str:
        return self.previous_hash

    # Get a list of transactions.
    # When only_ids is True we return only the transaction ids (into digest), otherwise the whole Transaction object
    def get_transactions(self, only_ids=False):

        if only_ids:
            return [trans.transaction_id.hexdigest() for trans in self.list_of_transactions]
        else:
            return self.list_of_transactions

    # Convert the object into dictionary in order to transfer it to other nodes
    def to_dict(self):

        return {
            'previousHashKey': self.previous_hash,
            'hashKey': self.hash_key,
            'nonce': self.nonce.decode('ISO-8859-1') if self.nonce is not None else None,
            'timestamp': self.timestamp,
            'transactions': [trans.to_dict() for trans in self.list_of_transactions]
        }

    def add_transaction(self, new_transaction: Transaction):
        self.list_of_transactions.append(new_transaction)

    # When a node finds a correct nonce number then the block is mined, so we can add the nonce and hash_key fields
    def is_mined(self, nonce: bytes, hash_key: str):

        # If we want to convert the nonce into int: int.from_bytes(nonce, 'big')
        self.nonce = nonce
        self.hash_key = hash_key

    def remove_common_transactions(self, transactions: [dict]):

        print('Remove the common transactions.')
        print('---------------------------------------')

        # Convert the lists into sets in order to find differences
        curr_transactions_ids = set(self.get_transactions(only_ids=True))
        other_transactions_ids = {trans['id'] for trans in transactions}

        # Remove from the current block the transactions that are validated from another block
        unique_transactions_ids = curr_transactions_ids - other_transactions_ids
        self.list_of_transactions = [trans for trans in self.list_of_transactions
                                     if trans.transaction_id.hexdigest() in unique_transactions_ids]

    '''
    This function is used when we try to validate a block and 
    and we have to check the block hash
    '''
    @staticmethod
    def find_hash_key(nonce: str, timestamp: str, previous_hash: str, transactions: [dict]) -> SHA256:

        # Convert all the info of the block into bytearray, in order to hash it with SHA256
        block_bytearray = bytearray()

        # Fetch the transaction_ids from the dictionary where are all the transactions
        # contained in the given block
        for trans in transactions:

            # Add it to the bytearray
            block_bytearray.extend(trans['id'].encode('utf-8'))

        # Add the previous_hash & timestamp & nonce into the bytearray
        block_bytearray.extend(previous_hash.encode('utf-8'))
        block_bytearray.extend(timestamp.encode('utf-8'))
        block_bytearray.extend(nonce.encode('ISO-8859-1'))

        return SHA256.new(data=block_bytearray)
