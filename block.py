import datetime
from transaction import Transaction
from Crypto.Hash import SHA256

class Block:

    def __init__(self, transaction_list: [Transaction], hash_key: str = None, nonce: bytes = None, prev_hash: str = None):

        # When we create a block we know its previous block
        self.previous_hash = prev_hash
        self.timestamp = str(datetime.datetime.now())

        # This a list which contains Transaction objects. At first is empty.
        self.list_of_transactions = transaction_list

        # These values will be known when the block is mined from some node.
        self.hash_key = hash_key
        self.nonce = nonce

    '''
    Converts the block's transactions and previous_hash into a bytearray
    '''
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

    '''
    Get a list of transactions.
    When only_ids is True we return only the transaction ids (into digest), otherwise the whole Transaction object
    '''
    def get_transactions(self, only_ids=False) -> list:

        if only_ids:
            return [trans.transaction_id.hexdigest() for trans in self.list_of_transactions]
        else:
            return self.list_of_transactions

    '''
    Convert the object into dictionary in order to transfer it to other nodes with JSON format
    '''
    def to_dict(self) -> dict:

        return {
            'previousHashKey': self.previous_hash,
            'hashKey': self.hash_key,
            'nonce': self.nonce.decode('ISO-8859-1') if self.nonce is not None else None,
            'timestamp': self.timestamp,
            'transactions': [trans.to_dict() for trans in self.list_of_transactions]
        }

    '''
    Add a new transaction the block but first check if it already exists
    '''
    def add_transaction(self, new_transaction: Transaction) -> None:

        my_trans_ids = [x.transaction_id.hexdigest() for x in self.list_of_transactions]
        if new_transaction.transaction_id.hexdigest() not in my_trans_ids:
            self.list_of_transactions.append(new_transaction)
        else:
            print('Transaction is already in this block.')

    '''
    When a node finds a correct nonce number then the block is mined, 
    so we can add the nonce and hash_key fields
    '''
    def is_mined(self, nonce: bytes, hash_key: str) -> None:

        # If we want to convert the nonce into int: int.from_bytes(nonce, 'big')
        self.nonce = nonce
        self.hash_key = hash_key

    '''
    Remove common transactions from my current block.
    This function is called when a new block arrives or when we get a new chain
    '''
    def remove_common_transactions(self, transactions: [dict]) -> None:

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
