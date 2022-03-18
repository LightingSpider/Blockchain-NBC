from pymongo import errors as pymongo_errors
import custom_errors
from argparse import ArgumentParser
import requests
from subprocess import Popen
from wallet import Wallet
from node import Node
import network
import time

# Bootstrap information
bootstrap_address = '127.0.0.1'
bootstrap_port = 5000

# At first create a wallet
my_wallet = Wallet()

# Get command line arguments
parser = ArgumentParser()
parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
parser.add_argument('-a', '--address', default='127.0.0.1', type=str, help='Network address')
args = parser.parse_args()

# Take the port & address & node_id of the new node
port = args.port
address = args.address
print('Address: ', address)
print('Port: ', str(port))
print('---------------------------------------')

# ----------- Create the node object -----------

# So we need to heck if this is the first node in the network
print('Check the existence of the Bootstrap node')
print('---------------------------------------')
try:

    # This means that there is a bootstrap node in the network so
    # Try to communicate with bootstrap node

    print('I will try now to communicate with the bootstrap node')
    init_settings = network.get_init_settings(address=bootstrap_address, port=bootstrap_port)

    node_id = init_settings['new_node_id']
    ring = init_settings['ring']
    UTXOs = init_settings['UTXOs']
    chain = init_settings['chain']

    print('I am not the bootstrap.')
    print('---------------------------------------')

    # Create the node object with the settings that we got from bootstrap
    my_node = Node(wallet=my_wallet, chain=chain, ring=ring, UTXOs=UTXOs, node_id=node_id, address=address, port=port)

except (requests.exceptions.ConnectionError, KeyError):

    # This means that this is the first node in the network
    print("I am the Bootstrap node yeah!")
    print('---------------------------------------')
    node_id = '0'
    my_node = Node(wallet=my_wallet, chain=[], ring={}, UTXOs={}, node_id=node_id, address=bootstrap_address, port=bootstrap_port)

# ----------- Database Configuration -----------
# We have now created a Node object, so we are ready to configure the database
import configuration
configuration.init(node=my_node)

# ----------- Set Up Api Server -----------
server_proc = Popen(["python", "server.py", "-a", address, "-p", str(port), "-n", node_id])
time.sleep(2)   # Wait till the server is up
# call(f"python server.py -a {address} -p {str(port)} -n {node_id} &", shell=True)

# Now we are ready to notify the bootstrap node that a new node has arrived
if node_id != '0':
    network.send_new_node_arrived(
        address=bootstrap_address,
        port=bootstrap_port,
        new_node_specs={
            "address": address,
            "port": port,
            "public_key": my_node.wallet.address
        }
    )

# This function will be used only from bootstrap in order to update its settings
# We update the settings in order to response fast whenever a new node arrives
def update_init_settings(bootstrap_node: Node):

    query = {"_id": "settings_doc"}
    new_values = {"$set": {
        "chain": bootstrap_node.chain,
        "UTXOs": bootstrap_node.UTXOs,
        "ring": bootstrap_node.ring
    }}
    configuration.db["info"].update_one(query, new_values)

    print("Settings updated")
    print('---------------------------------------')

# This function is for all the nodes
def update_status(node: Node):

    query = {"_id": "status_doc"}
    new_values = {"$set": node.to_dict()}
    configuration.db["info"].update_one(query, new_values)

    print("STATUS UPDATED")
    print('---------------------------------------')

queued_transactions = []
def process_the_message(message_type: str, message_data: dict, message_id: str):

    try:
        if message_type == 'block':

            print('New block arrived.')

            # Need to stop every mining process running
            if my_node.mining_proc is not None:
                if my_node.mining_proc.poll() is None:
                    print('Stop mining.')
                    Popen.terminate(my_node.mining_proc)
            print('---------------------------------------')

            # Receive the new block
            my_node.receive_block(message_data)

            # Process the queued transactions
            for _ in range(len(queued_transactions)):

                print('Get some transactions from my Queue (BlockArrived)')
                print('---------------------------------------')

                # If the node started mining then stop
                time.sleep(1)
                if my_node.mining_proc.poll() is None:
                    print('Mining started again, so stop getting transactions from the queue')
                    break

                # Add the transaction
                q_trans = queued_transactions.pop(0)
                my_node.validate_transaction(q_trans)

        elif message_type == 'transaction':

            # Check if we are in a mining process
            if my_node.mining_proc is not None:
                if my_node.mining_proc.poll() is None:
                    print('Node is mining so we will queue this transaction.')
                    queued_transactions.append(message_data)
                else:
                    my_node.validate_transaction(message_data)
            else:
                my_node.validate_transaction(message_data)

        elif message_type == 'ring':

            my_node.get_the_final_ring(
                ring=message_data['ring_dict'],
                signature=message_data['signature'],
                hash_ring=message_data['hash_ring']
            )

        elif message_type == 'NewNodeArrived':

            my_node.register_node_to_network(
                address=message_data['address'],
                port=message_data['port'],
                public_key=message_data['public_key']
            )

            # Save the current chain, which maybe contains only the genesis block
            # Save the ring and UTXOs, which contains all the nodes' info at the current time
            # update_init_settings(bootstrap_node=my_node)

        elif message_type == 'NewTransaction':

            my_node.create_transaction(
                receiver_node_id=message_data['recipient_node_id'],
                amount=message_data['amount']
            )

        elif message_type == 'FoundNonce':

            my_node.current_block.is_mined(
                nonce=message_data['nonce'].encode('ISO-8859-1'),
                hash_key=message_data['hashKey']
            )
            my_node.broadcast_block()

            # Process the queued transactions
            for _ in range(len(queued_transactions)):

                print('Get some transactions from my Queue (FoundNonce)')
                print('---------------------------------------')

                # If the node started mining then stop
                if my_node.mining_proc.poll() is None:
                    print('Mining started again, so stop getting transactions from the queue')
                    break

                # Add the transaction
                q_trans = queued_transactions.pop(0)
                my_node.validate_transaction(q_trans)

        else:
            raise custom_errors.InvalidMessageType(message_type=message_type)

    except custom_errors.InvalidMessageType as e:
        print('---------------------------------')
        print(f'Error at node_{my_node.node_id}')
        print(str(e))

    except custom_errors.InvalidHash as e:
        print('---------------------------------')
        print(f'Error at node_{my_node.node_id}')
        print(str(e))

    except custom_errors.UnauthorizedNode as e:
        print('---------------------------------')
        print(f'Error at node_{my_node.node_id}')
        print(str(e))

    except custom_errors.InsufficientAmount as e:
        print('---------------------------------')
        print(f'Error at node_{my_node.node_id}')
        print(str(e))

    except custom_errors.InvalidPreviousHashKey as e:
        print('---------------------------------')
        print(f'Error at node_{my_node.node_id}')
        print(str(e))
        print('Maybe it is time to call the Consensus Algorithm.')
        my_node.resolve_conflicts()

    except custom_errors.InvalidUTXOs as e:
        print('---------------------------------')
        print(f'Error at node_{my_node.node_id}')
        print(str(e))

    except custom_errors.UnableResolveConflict as e:
        print('---------------------------------')
        print(f'Error at node_{my_node.node_id}')
        print(str(e))

    '''
    except KeyError:
        print(f'Invalid message format with type {message_type}')
    '''

    # Update status on every new action
    update_status(my_node)

    # Remove the message from the message collection in MongoDB
    configuration.message_queue.delete_one({'_id': message_id})

# -------------------- Streaming messages --------------------
pipeline = [{'$match': {'operationType': 'insert'}}]
try:
    resume_token = None
    queued_messages = []

    with configuration.message_queue.watch(pipeline) as stream:
        for insert_change in stream:

            # Get the message type and keep only the usefull data
            new_message_type = insert_change['fullDocument']['type']
            new_message_data = {k: v for k, v in insert_change['fullDocument'].items() if k not in ['_id', 'type']}
            new_message_id = insert_change['fullDocument']['_id']
            new_message = (new_message_type, new_message_data, new_message_id)

            process_the_message(
                message_type=new_message_type,
                message_data=new_message_data,
                message_id=new_message_id
            )

            time.sleep(1)

            resume_token = stream.resume_token

except pymongo_errors.PyMongoError as e:

    # The ChangeStream encountered an unrecoverable error or the
    # resume attempt failed to recreate the cursor.
    if resume_token is None:

        # There is no usable resume token because there was a
        # failure during ChangeStream initialization.
        print(str(e))

    else:
        # Use the interrupted ChangeStream's resume token to create
        # a new ChangeStream. The new stream will continue from the
        # last seen insert change without missing any events.
        with configuration.message_queue.watch(
                pipeline, resume_after=resume_token) as stream:
            for insert_change in stream:
                print(insert_change)

# Terminate the sever process
Popen.terminate(server_proc)
