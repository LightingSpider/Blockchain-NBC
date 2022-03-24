from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
import datetime

'''
A transaction can be created only from the sender who is also the owner of the wallet, in order to sing it.
When someone gets a transaction has to validate it.
We always need UTXOs as input for a transaction, in order to prevent double spending.
'''
class Transaction:

    def __init__(self, sender_address: str, receiver_address: str, amount: str, transaction_inputs: [str] = None,
                 signature: bytes = None, timestamp: str = None):
        self.sender_address = sender_address
        self.receiver_address = receiver_address
        self.amount = amount

        '''
        The transaction_inputs is a list of transaction ids, which shows from the money came from.
        Τhe Transaction Input consists of the previousOutputId fields that are
        the id of the Transaction Output from which the amount transferred is derived.
        '''
        self.transaction_inputs = [] if transaction_inputs is None else transaction_inputs

        # Create the bytearray which contains the necessary fields
        temp_bytearray = bytearray()  # Initialize the bytearray
        temp_bytearray.extend(sender_address.encode('utf-8'))  # Add the sender_address
        temp_bytearray.extend(receiver_address.encode('utf-8'))  # Add the recipient_address
        temp_bytearray.extend(amount.encode('utf-8'))  # Add the value
        trans_inputs_bytes = [input_trans_id.encode('utf-8') for input_trans_id in self.transaction_inputs]
        for x in trans_inputs_bytes:
            temp_bytearray.extend(x)  # Add the transaction inputs

        # Create the hash key based on this bytearray
        self.transaction_id = SHA256.new(data=temp_bytearray)

        # Initialize with None at first and wait till the transaction validation
        # Signature is a type of [TransactionOutput]
        self.transaction_outputs = []

        # Initialize with None the signature at first and wait till the sender signs the transaction
        self.signature = signature
        self.timestamp = str(datetime.datetime.now()) if timestamp is None else timestamp

    # Convert the object into dictionary in order to transfer it to other nodes
    def to_dict(self) -> dict:
        return {
            'id': self.transaction_id.hexdigest(),
            'sender': self.sender_address,
            'receiver': self.receiver_address,
            'amount': self.amount,
            'signature': self.signature.decode('ISO-8859-1'),
            'inputTransactions': self.transaction_inputs,
            'outputTransactions': [trans_out.to_dict() for trans_out in self.transaction_outputs],
            'timestamp': self.timestamp
        }

    '''
    This function is called when a transaction is validated. 
    Every transaction creates 2 transaction outputs
        1. output for the receiver
        2. output for the sender which shows the remaining money
    A transaction output object contains:
        1. A unique transaction id,
        2. Τhe transaction id from which it comes from,
        3. The recipient of the transaction (the new holder of the coins),
        4. The amount that transferred.
    '''
    def add_transaction_outputs(self, surplus_amount: str):

        # In this TransactionOutput the receiver is the Transaction receiver
        receiver_transaction_output = TransactionOutput(official_transaction_id=self.transaction_id,
                                                        receiver_address=self.receiver_address,
                                                        amount=self.amount)

        # In this TransactionOutput the receiver is the Transaction sender
        sender_transaction_output = TransactionOutput(official_transaction_id=self.transaction_id,
                                                      receiver_address=self.sender_address,
                                                      amount=surplus_amount)

        self.transaction_outputs = [receiver_transaction_output, sender_transaction_output]

    '''
    Sign the transaction with the private key of the sender
    This function creates a PKCS#1 v1.5 signature of a message, which is the hash key of some data.
    '''
    def sign_transaction(self, sender_private_key: RSA.RsaKey):
        self.signature = pkcs1_15.new(sender_private_key).sign(self.transaction_id)

'''
There are no accounts or balances 
there are only unspent transaction outputs (UTXO) scattered in the blockchain.
'''
class TransactionOutput:

    def __init__(self, official_transaction_id: SHA256, receiver_address: str, amount: str):

        self.official_transaction_id = official_transaction_id
        self.receiver_address = receiver_address
        self.amount = amount

        # Hash the transaction in order to find its unique id
        temp_bytearray = bytearray()  # Initialize the bytearray
        temp_bytearray.extend(official_transaction_id.hexdigest().encode('utf-8'))  # Add the sender_address
        temp_bytearray.extend(receiver_address.encode('utf-8'))  # Add the recipient_address
        temp_bytearray.extend(amount.encode('utf-8'))  # Add the value

        self.id = SHA256.new(data=temp_bytearray).hexdigest()

    # Convert the object into dictionary in order to transfer it to other nodes
    def to_dict(self):
        return {
            'id': self.id,
            'officialTransactionId': self.official_transaction_id.hexdigest(),
            'receiverAddress': self.receiver_address,
            'amount': self.amount
        }
