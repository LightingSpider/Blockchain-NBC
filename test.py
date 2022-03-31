from block import Block
from transaction import Transaction
from Crypto.Random import get_random_bytes
from Crypto.Hash import SHA256
from subprocess import call, Popen

DIFF = 5
node_id = '0'
import hashlib
import pymongo
client = pymongo.MongoClient(host=['localhost:27017'], replicaset='rs0')

def test_hash_validation():
    # ---------- CREATE BLOCK ----------
    block = Block(prev_hash='1', transaction_list=[])
    trans = Transaction(sender_address='sender', receiver_address='receiver', amount='5.0',
                        transaction_inputs=['trans_in_1', 'trans_in_2'])
    trans.signature = b'signature'
    block.add_transaction(trans)

    # ---------- HASH BEFORE NONCE ----------
    block_bytearray_before_nonce = block.bytearray_before_nonce()
    hash_before_nonce = hashlib.sha256(block_bytearray_before_nonce)
    print('Hash Key without nonce: ', hash_before_nonce.hexdigest())

    # ---------- FIND A NONCE ----------
    nonce = None
    while True:

        # Find a random nonce (in bytes)
        nonce = get_random_bytes(64)

        # Add the nonce to the bytearray
        temp_bytearray = bytearray()
        temp_bytearray.extend(block_bytearray_before_nonce)
        temp_bytearray.extend(nonce)

        # Hash the block with SHA256
        block_hash = hashlib.sha256(temp_bytearray)

        if block_hash.hexdigest()[0:DIFF] == DIFF * '0':
            # print('FOUND nonce:', nonce.decode('ISO-8859-1'))

            print('---------------------------------------')
            print('Found Hash Key:')
            print(block_hash.hexdigest())

            print('temp_bytearray:')
            print(temp_bytearray)
            print('---------------------------------------')

            block.is_mined(nonce=nonce, hash_key=block_hash.hexdigest())
            break

    print('---------------------------------------')
    temp_hash = hashlib.sha256(temp_bytearray)
    print('Hash Key immediately after mining:')
    print(temp_hash.hexdigest())

    hash_after_nonce_with_bytearray = hashlib.sha256(temp_bytearray)
    print('Hash Key with temp_bytearray:')
    print(hash_after_nonce_with_bytearray.hexdigest())

    hash_after_nonce_with_temp_bytearray = hashlib.sha256(temp_bytearray)
    print('Hash Key with temp_bytearray: ', hash_after_nonce_with_temp_bytearray.hexdigest())

    # ---------- HASH WITH NONCE ----------
    block_bytearray_after_nonce = block_bytearray_before_nonce
    block_bytearray_after_nonce.extend(nonce)

    # ---------- COMPARE BYTE ARRAYS ----------
    print('---------------------------------------')
    # print(temp_bytearray)
    # print(block_bytearray_after_nonce)
    # print(temp_bytearray == block_bytearray_after_nonce)
    print('---------------------------------------')

    # ---------- COMPARE HASH KEYS ----------
    hash_after_nonce = hashlib.sha256(block_bytearray_after_nonce)
    hash_after_nonce_with_temp_bytearray = hashlib.sha256(temp_bytearray)
    print('Hash Key with temp_bytearray: ', hash_after_nonce_with_temp_bytearray.hexdigest())
    print('Hash Key with nonce: ', hash_after_nonce.hexdigest())
    print('Hash Key from block object: ', block.hash_key)
    print('---------------------------------------')

    # ---------- COMPARE HASH KEYS FROM SAME BYTEARRAYS ----------
    hash_a = hashlib.sha256(block_bytearray_after_nonce)
    hash_b = hashlib.sha256(temp_bytearray)
    print(hash_a.hexdigest())
    print(hash_b.hexdigest())
    print(hash_a.hexdigest() == hash_b.hexdigest())
    print('---------------------------------------')


def test_parallel_mining():
    # ---------- CREATE BLOCK ----------
    block = Block(prev_hash='1', transaction_list=[])
    trans = Transaction(sender_address='sender', receiver_address='receiver', amount='5.0',
                        transaction_inputs=['trans_in_1', 'trans_in_2'])
    trans.signature = b'signature'
    block.add_transaction(trans)

    # ---------- HASH BEFORE NONCE ----------
    block_bytearray_before_nonce = block.bytearray_before_nonce()

    block_bytearray_before_nonce_str = block_bytearray_before_nonce.decode('utf-8')
    proc = Popen(["python", "mining.py", "-b", block_bytearray_before_nonce_str, "-d", str(DIFF), "-n", node_id])
    import time
    time.sleep(4)
    Popen.terminate(proc)

'''
from wallet import Wallet
from Crypto.Signature import pkcs1_15

a = Wallet()
b = Wallet()
msg_hash = SHA256.new(data=b'1')

signature_ring = pkcs1_15.new(a.private_key).sign(msg_hash)
pkcs1_15.new(b.public_key).verify(
    msg_hash=msg_hash,
    signature=signature_ring
)
'''

def find_utxos(db):
    info = db['info']
    info_doc = list(info.find({"_id": "status_doc"}, {"_id": 0}))[0]
    chain = info_doc['chain']
    ring = info_doc['ring']
    # chain.append(info_doc['current_block'])

    key_to_id = {}
    for node_id, node_obj in ring.items():
        key_to_id[node_obj['public_key']] = node_id

    transaction_outputs = {}
    transaction_inputs = set()

    # Parse the whole chain
    for block in chain:
        # Get all the transactions in a block
        for trans in block['transactions']:

            # Remove the transaction inputs from our dictionary
            for input_trans in trans['inputTransactions']:
                transaction_inputs.add(input_trans)

            # Add the transaction outputs into our dictionary
            for output_trans in trans['outputTransactions']:
                transaction_outputs[output_trans['id']] = output_trans
    try:
        for trans_in in transaction_inputs:
            del transaction_outputs[trans_in]
    except KeyError:
        print('MISS', trans_in)

    # Now we have collected all the unspent transaction outputs,
    # we are ready to create the new UTXOs
    new_UTXOs = {}
    for trans_output_id, trans_output in transaction_outputs.items():
        receiver_address = trans_output['receiverAddress']

        # Ignore the first transaction
        if receiver_address == '0':
            continue

        # Initialize the UTXO for the address
        if receiver_address not in new_UTXOs.keys():
            new_UTXOs[receiver_address] = {}

        new_UTXOs[receiver_address][trans_output_id] = trans_output

    # Check the new UTXOs
    print("New UTXOs from the new accepted chain")
    print(f"UTXOs for: {len(new_UTXOs)} nodes")

    '''
    for pk, values in new_UTXOs.items():
        print(key_to_id[pk])
        for k in values.keys():
            print(k)
        print()
    '''
    final_balance = 0.0
    for node_id, node_obj in ring.items():
        wallet_balance = 0.0
        wallet_UTXOs = new_UTXOs[node_obj['public_key']]

        for utxo in wallet_UTXOs.values():
            wallet_balance += float(utxo['amount'])

        print(f'Wallet of node_{node_id}: {wallet_balance}')
        final_balance += wallet_balance

    print('Final -->', final_balance)

def show_balances(db):
    info = db['info']
    info_doc = list(info.find({"_id": "status_doc"}, {"_id": 0}))[0]
    ring = info_doc['ring']
    UTXOs = info_doc['UTXOs']

    final_balance = 0.0

    for node_id, node_obj in ring.items():
        wallet_balance = 0.0
        wallet_UTXOs = UTXOs[node_obj['public_key']]

        for utxo in wallet_UTXOs.values():
            wallet_balance += float(utxo['amount'])

        print(f'Wallet of node_{node_id}: {wallet_balance}')
        final_balance += wallet_balance

    print('Final -->', final_balance)

for i in range(0, 10):
    show_balances(client[f'node_{str(i)}'])
    print('-------------------------')