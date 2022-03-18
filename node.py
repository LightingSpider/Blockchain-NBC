import subprocess

N = 4
C = 3
DIFF = 5

import json
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from subprocess import Popen

import custom_errors
from block import Block
from wallet import Wallet
import network
from transaction import Transaction

class Node:

	# The chain is a list of blocks in the form of a dictionary
	# The ring is a dictionary which contains all the necessary communication information with the other nodes
	def __init__(self,  wallet: Wallet, chain: [dict], ring: dict, UTXOs: dict, node_id: str = '0', address: str = '127.0.0.1', port: int = 5000):

		self.network_address = address
		self.port = port
		self.node_id = node_id
		self.wallet = wallet
		self.mining_proc = None

		# Key: Node public addresses
		# Value: List of TransactionOutput.to_dict()
		self.UTXOs = {}

		print('Creating the Node object.')

		# The creation of the boostrap node
		if node_id == '0':

			# The ring is where we store information for every node, as its id, its address (ip:port) its public key and its balance
			# That's why here we only add at the ring the boostrap node
			# It is a dictionary where the key is the id of each node
			self.ring = {
				'0': {
					'address': address,
					'port': port,
					'public_key': self.wallet.address
				}
			}

			# Create the first transaction where the boostrap node takes the first NBCs
			first_transaction = Transaction(
				sender_address='0',
				receiver_address=self.wallet.address,
				amount=str(100.0*N),
				transaction_inputs=[]
			)

			# This transaction does not need validation
			first_transaction.add_transaction_outputs(surplus_amount='0')
			first_transaction.sign_transaction(wallet.private_key)

			# Create the genesis block
			self.current_block = Block(prev_hash='1', transaction_list=[])
			self.current_block.add_transaction(first_transaction)

			# This block contains only the first transaction,
			# and we are ready to find its hash key because we are given the nonce
			nonce = b'0'
			block_bytearray = self.current_block.bytearray_before_nonce()
			block_bytearray.extend(nonce)
			block_hash = SHA256.new(data=block_bytearray)
			self.current_block.is_mined(nonce=nonce, hash_key=block_hash.hexdigest())

			# The genesis block does not need validation and that's why it is added to the chain
			self.chain = [self.current_block.to_dict()]
			self.create_new_block()

			# Now the bootstrap node owns 100*N NBCs
			bootstrap_trans_output = first_transaction.transaction_outputs[0]

			self.UTXOs[self.wallet.address] = {}
			self.UTXOs[self.wallet.address][bootstrap_trans_output.id] = bootstrap_trans_output.to_dict()

		# This is for all the other nodes which are not bootstrap.
		else:

			# We take the current chain from the bootstrap node which means
			self.chain = chain
			self.validate_chain()

			# The node will get the full ring when all the nodes arrive.
			self.ring = ring

			# The node takes the UTXOs from the bootstrap
			self.UTXOs = UTXOs

			# Create the block where all the incoming transactions will be added.
			last_block = self.chain[-1]
			self.current_block = Block(prev_hash=last_block['hashKey'], transaction_list=[])

		print('Node object created, with id: ', node_id)
		print('---------------------------------------')

	# -------------- General  ---------------

	def to_dict(self):

		"""
		Find the chain hash in order to sign it,
		we will use these values when there is a conflict in the chain,
		and we need tot avoid malicious chain broadcasting.
		"""

		# First encode the dict into bytearray
		encoded_chain = json.dumps(self.chain).encode('utf-8')
		bytes_chain = bytearray(encoded_chain)

		# Create the hash key based on this bytearray
		hash_chain = SHA256.new(data=bytes_chain)

		# Now create the signature
		signature_chain = pkcs1_15.new(self.wallet.private_key).sign(hash_chain)

		return {
			"address": self.network_address,
			"port": self.port,
			"node_id": self.node_id,
			"ring": self.ring,
			"public_key": self.wallet.address,
			"chain": self.chain,
			"current_block": self.current_block.to_dict(),
			"UTXOs": self.UTXOs,
			"chain_hash": hash_chain.hexdigest(),
			"signature_chain": signature_chain.decode('ISO-8859-1'),
			"last_block_timestamp": self.chain[-1]['timestamp']
		}

	# -------------- Receiver actions --------------

	def add_transaction_to_block(self, transaction: Transaction):

		# Add it to the current block
		block = self.current_block
		block.add_transaction(transaction)

		# Check if block is full of capacity
		block_current_capacity = len(block.list_of_transactions)
		if block_current_capacity == C:
			print('Block is full.')
			self.mine_block()

	'''
	We call this function when another node broadcasts its block and we have to
		1. Validate it
		2. Add it to our chain
	We don't create a new block here, we just remove the common transactions
	'''
	def receive_block(self, block: dict):

		# First validate the incoming block
		self.validate_block(block)

		# Add block to our chain
		self.chain.append(block)

		# Remove the common transactions (if they exist)
		self.current_block.remove_common_transactions(block['transactions'])

		# Update the previous_hash_key of the current block since a new block added to the chain
		self.current_block.previous_hash = block['hashKey']

	# ---------------- Creation ---------------

	def create_transaction(self, receiver_node_id: str, amount: str):

		print("Create a transaction")
		print(f"node_{self.node_id} --> node_{receiver_node_id} : {amount} NBCs")
		print('---------------------------------------')

		# Get the public keys
		rec_pub_key = self.ring[receiver_node_id]['public_key']
		send_pub_key = self.wallet.address

		print('Collect the needed UTXOs')
		print('---------------------------------------')

		# Find the UTXOs which can provide a total amount >= needed amount
		# When we use a UTXO we have to remove it from the saved UTXOs
		coins_cnt = 0.0
		input_transactions = []
		for utxo_key, utxo_value in self.UTXOs[send_pub_key].items():

			# Add the UTXO to input transactions
			print(f"Collect {utxo_value['amount']}")
			coins_cnt += float(utxo_value['amount'])
			input_transactions.append(utxo_key)

			# Check if we have sufficient amount of coins
			if coins_cnt >= float(amount):
				print(f"Needed {amount} and collected {str(coins_cnt)}")
				break

		print('Check the balance')
		print('---------------------------------------')

		if coins_cnt < float(amount):
			raise custom_errors.InsufficientAmount(
				err="Can't create the transaction. Insufficient amount"
			)

		# At this point means that we have sufficient amount of money for the transaction
		# So remove the used UTXOs from the saved UTXOs
		# for utxo_key in input_transactions:
			# del self.UTXOs[send_pub_key][utxo_key]

		print('Create the transaction object')
		print('---------------------------------------')

		# Create the transaction
		transaction = Transaction(
			sender_address=send_pub_key,
			receiver_address=rec_pub_key,
			amount=amount,
			transaction_inputs=input_transactions
		)

		print('Sign the transaction with my private key')
		print('---------------------------------------')

		# Sign the transaction with the sender's private key
		transaction.sign_transaction(self.wallet.private_key)

		'''
		print('Fix the UTXOs')
		print('---------------------------------------')

		# Once we have checked the balance it means that this transaction is valid,
		# se we need to update the UTXOs by producing the correct transactionOutputs
		transaction.add_transaction_outputs(surplus_amount=str(coins_cnt - float(amount)))
		for trans_output in transaction.transaction_outputs:
			receiver_address = trans_output.receiver_address
			if receiver_address not in self.UTXOs.keys():
				self.UTXOs[receiver_address] = {}
			self.UTXOs[receiver_address][trans_output.id] = trans_output.to_dict()
		'''

		print('Transaction object created')
		print('---------------------------------------')

		# Broadcast the transaction to all the other nodes
		self.broadcast_transaction(transaction)

	'''
	When the current blocked is broadcast we need to create a new one
	'''
	def create_new_block(self):

		# Initialize a new empty block
		self.current_block = Block(
			prev_hash=self.chain[-1]['hashKey'],
			transaction_list=[]
		)

	# ----------------  Validation  ---------------

	'''
	1. Verify the signature
	2. Check the UTXOs
	3. Check the balance
	4. Allow the transaction or abort
	5. Transaction Outputs are created and added to the list of UTXOs
	'''
	def validate_transaction(self, transaction: dict):

		print(f"Validating new transaction with amount {transaction['amount']}")

		# Extract all the necessary information form the transaction
		sender_address = transaction['sender']
		transaction_id = transaction['id']
		signature = transaction['signature'].encode('ISO-8859-1')
		amount = transaction['amount']

		# Create the transaction object from the given dictionary
		transaction_object = Transaction(
			sender_address=sender_address,
			receiver_address=transaction['receiver'],
			amount=amount,
			transaction_inputs=transaction['inputTransactions'],
			signature=signature
		)

		# From the address we can create a public key in order to verify the signature
		sender_public_key = RSA.importKey(extern_key=sender_address)

		# Verify the signature
		pkcs1_15.new(sender_public_key).verify(transaction_object.transaction_id, signature)

		# Check that the transaction_object hash to be the same with the given transaction_id
		if transaction_object.transaction_id.hexdigest() != transaction_id:
			raise custom_errors.InvalidHash(
				err=f"Could not validate the HashKey of the transaction {transaction_id}"
			)

		print('Check UTXOs')

		# Check the inputTransactions
		# 1. If they are UTXOs
		sender_UTXOs = self.UTXOs[sender_address]
		input_balance = 0.0
		for trans_id in transaction['inputTransactions']:

			# If the transaction id refers to a UTXO:
			# 1. add the amount to the balance
			# 2. remove it from the sender's UTXOs in order to avoid double spending
			try:
				input_balance += float(sender_UTXOs[trans_id]['amount'])
				del sender_UTXOs[trans_id]

			except KeyError:

				# Find the sender node_id
				node_id = None
				for k, v in self.ring.items():
					if v['public_key'] == sender_address:
						node_id = k
						break

				raise custom_errors.InvalidUTXOs(
					err=f"Invalid UTXO from node {node_id} with ID: '{trans_id}'"
				)

		print("Check Balance")

		# 2. If they have sufficient amount of coins
		surplus = input_balance - float(amount)
		if surplus < 0.0:
			raise custom_errors.InsufficientAmount(
				err=f"Insufficient amount from node '{sender_address}' at the transaction {transaction_id}"
			)

		# At this point we have validated the transaction,
		# and we can produce the transaction outputs
		transaction_object.add_transaction_outputs(surplus_amount=str(surplus))
		for trans_output in transaction_object.transaction_outputs:
			receiver_address = trans_output.receiver_address
			if receiver_address not in self.UTXOs.keys():
				self.UTXOs[receiver_address] = {}
			self.UTXOs[receiver_address][trans_output.id] = trans_output.to_dict()

		print("Transaction validated")
		print('---------------------------------------')

		self.add_transaction_to_block(transaction_object)

	'''
	Validate the given chain either from the bootstrap node either for the consensus algorithm
	The validate_block is called for all the blocks except the genesis block
	'''
	def validate_chain(self):

		# Validate each block in the chain which is a list of dicts
		for block in self.chain:

			# Don't validate the genesis block
			if block['nonce'].encode('utf-8') != b'0':
				self.validate_block(block)

	'''
	Check a block's validity by checking its hash and 
	check that the previous_hash field is equal to the hash of the previous block.
	'''
	def validate_block(self, block: dict):

		# Check the validity of the hash_key with the difficulty
		block_hash = block['hashKey']
		if block_hash[0:DIFF] != DIFF*'0':
			raise custom_errors.InvalidHash(
				err="Block hash does not satisfy the difficulty level."
			)

		# Check if the given nonce can produce the given hash
		hash_key = Block.find_hash_key(
			nonce=block['nonce'],
			timestamp=block['timestamp'],
			previous_hash=block['previousHashKey'],
			transactions=block['transactions']
		)
		if hash_key.hexdigest() != block_hash:
			raise custom_errors.InvalidHash(
				err="Invalid block hash. Cannot generate the same hash key with the given nonce number."
			)

		# Check the validity of the prev_hash
		prev_block_hash = self.chain[-1]['hashKey']
		if prev_block_hash != block['previousHashKey']:
			raise custom_errors.InvalidPreviousHashKey(
				err="The given PreviousHashKey is not the same with my previous block."
			)

	# ---------------- Broadcasting ---------------

	def broadcast_transaction(self, transaction: Transaction):

		print(f"Start broadcasting the transaction with id {transaction.transaction_id.hexdigest()}")
		print('---------------------------------------')

		# Send the mined transaction to all the other nodes
		for node_id, node in self.ring.items():

			# if node_id != self.node_id:

			print(f"Send it: node_{node_id} @ {node['address']}:{str(node['port'])}")
			network.send_transaction(
				address=node['address'],
				port=node['port'],
				transaction=transaction.to_dict()
			)
		print('---------------------------------------')

		# I trust myself, so I will not send this transaction to myself in order to avoid validation
		# self.add_transaction_to_block(transaction)

	'''
	Once the node finds the nonce first, sends the block to everyone.
	'''
	def broadcast_block(self):

		print('Start Block broadcasting')
		print('---------------------------------------')

		block_dict = self.current_block.to_dict()

		# Send the mined block to all the other nodes
		for node_id, node in self.ring.items():

			if node_id != self.node_id:

				print(f"Send it: node_{node_id} @ {node['address']}:{str(node['port'])}")
				network.send_block(
					address=node['address'],
					port=node['port'],
					block=block_dict
				)

		print('Add the block to my current chain.')
		print('---------------------------------------')

		# I trust myself, so I will not send this block to myself in order to avoid validation
		self.chain.append(block_dict)
		self.create_new_block()

	'''
	Broadcast the final ring to all the other nodes. This function is only called from the bootstrap
	'''
	def broadcast_final_ring(self, signature_ring: str, hash_ring: str):

		print('Start broadcasting the final ring.')
		print('---------------------------------------')

		# Send the final ring to all the other nodes
		for node_id, node in self.ring.items():

			if node_id != self.node_id:

				print(f"Send it: node_{node_id} @ {node['address']}:{str(node['port'])}")
				network.send_ring(
					address=node['address'],
					port=node['port'],
					ring={
						"ring_dict": self.ring,
						"signature": signature_ring,
						"hash_ring": hash_ring
					}
				)

	# ---------------- Settings & Ring ---------------

	'''
	Only the bootstrap node can add a node to the ring after checking his wallet and ip:port address
	After adding, bootstrap node informs all other nodes and gives the request node an id and 100 NBCs
	'''
	def register_node_to_network(self, address: str, port: int, public_key: str):

		# Only the bootstrap node can execute this function
		if self.node_id != '0':
			raise custom_errors.UnauthorizedNode(
				err="Only the bootstrap node can execute the function 'register_node_to_network'."
			)

		# Add the node to the ring
		new_node_id = str(len(self.ring))
		self.ring[new_node_id] = {
			'address': address,
			'port': port,
			'public_key': public_key
		}

		print("Current Ring:")
		for k, v in self.ring.items():
			print(k, ":", v)
			print('---------')
		print('---------------------------------------')

		# Give the new node 100 NBC
		self.create_transaction(receiver_node_id=new_node_id, amount='100.0')

		# This means that all the nodes have arrived, and we are ready to broadcast the ring
		if int(new_node_id) + 1 == N:

			# Sign the message by the bootstrap node in order to avoid malicious ring broadcasting
			# First encode the dict into bytearray
			encoded_ring = json.dumps(self.ring).encode('utf-8')
			bytes_ring = bytearray(encoded_ring)

			# Create the hash key based on this bytearray
			hash_ring = SHA256.new(data=bytes_ring)

			# Now create the signature
			signature_ring = pkcs1_15.new(self.wallet.private_key).sign(hash_ring)

			# Broadcast:
			# 1. ring      --> 'dict'
			# 2. signature --> 'str' decode the signature with ISO-8859-1
			# 3. hash_ring --> 'str' from hex-digest
			self.broadcast_final_ring(
				signature_ring=signature_ring.decode('ISO-8859-1'),
				hash_ring=hash_ring.hexdigest()
			)

	'''
	Send the node_id, chain, UTXOs and ring to new node came into the network
	'''
	def send_init_settings(self, new_node_id: str):
		settings = {
			'node_id': new_node_id,
			'ring': self.ring,
			'UTXOs': self.UTXOs,
			'chain': self.chain
		}

		network.send_settings(
			address=self.ring[new_node_id]['address'],
			port=self.ring[new_node_id]['port'],
			settings=settings
		)

	'''
	This is function is used only by simple nodes.
	When all the nodes have arrived, the ring will be broadcast from the bootstrap node.
	So each node has to validate the message and update its ring.
	'''
	def get_the_final_ring(self, ring: dict, signature: str, hash_ring: str):

		print('Get the final Ring.')
		print('---------------------------------------')

		if self.node_id == '0':
			raise custom_errors.UnauthorizedNode(
				err="The bootstrap cannot take the final ring."
			)

		# Check the validity of the content by comparing the hash keys
		encoded_ring = json.dumps(ring).encode('utf-8')
		bytes_ring = bytearray(encoded_ring)
		temp_hash_ring = SHA256.new(data=bytes_ring)
		if temp_hash_ring.hexdigest() != hash_ring:
			raise custom_errors.InvalidHash(err="Invalid Hash Ring.")

		# Check the validity of the sender by verifying the signature
		bootstrap_public_key = RSA.importKey(extern_key=self.ring['0']['public_key'])
		pkcs1_15.new(bootstrap_public_key).verify(temp_hash_ring, signature.encode('ISO-8859-1'))

		# Update the ring
		self.ring = ring

	# ---------------- Mining ---------------

	'''
		When a block has reached the capacity is ready to find the nonce (proof-of-work).
		We will try random 'nonce' until the hash_key of block meets the requirements 
	'''
	def mine_block(self):

		print('Start mining')
		print('---------------------------------------')

		# Get the bytes of the current block
		block_bytearray_before_nonce = self.current_block.bytearray_before_nonce()

		# Start mining, the whole program blocks until mining is done
		block_bytearray_before_nonce_str = block_bytearray_before_nonce.decode('utf-8')
		self.mining_proc = Popen(["python", "mining.py", "-b", block_bytearray_before_nonce_str, "-d", str(DIFF), "-n", self.node_id])

	# ---------------- Consensus ---------------

	'''
	This function is called when a node receives a block that it cannot be validated
	because the previous_hash field is not equal to the hash of the previous block. 
	The node asks the other nodes for the length of the blockchain and 
	chooses to adopt this with the longer length.
	'''
	def resolve_conflicts(self):

		# Ask the other nodes for their chain
		chains = self.ask_for_chain()

		# Find the right chain
		right_chain = self.find_the_right_chain(chains)

		# Update the node
		self.chain = right_chain

		# Remove the common transactions between my current block and the blocks of the given chain
		for block in self.chain:
			self.current_block.remove_common_transactions(block['transactions'])

		# Update the previous_hash_key of the current block since a new block added to the chain
		self.current_block.previous_hash = self.chain[-1]['hashKey']

	'''
	Ask every node in the network for their chain until this moment
	'''
	def ask_for_chain(self) -> dict:

		print('Start asking for chain.')
		print('---------------------------------------')

		chains = {}

		# Ask everybody for their chain except myself
		for node_id, node in self.ring.items():

			print(f"Ask for chain from: node_{node_id} @ {node['address']}:{str(node['port'])}")
			chains[node_id] = network.get_chain(
				address=node['address'],
				port=node['port']
			)

		return chains

	'''
	After getting all the chains from all the nodes in the network,
	we need to find the chain which is:
		1. Valid, 
		2. Longest, 
		3. with the Oldest Block
	'''
	def find_the_right_chain(self, chains: dict) -> [dict]:

		print('Trying to find the correct chain.')
		print('---------------------------------------')

		# Sort the keys based on the len(chain) and the timestamp of the last valid block
		sorted_keys = sorted(chains, key=lambda k: (-len(chains[k]['chain']), chains[k]['last_block_timestamp']))

		accepted_chain = None
		for node_id in sorted_keys:

			print(f'Checking the chain from node_{node_id}')

			# Try to validate the given chain
			try:
				# Check the validity of the content by comparing the hash keys
				encoded_chain = json.dumps(chains[node_id]['chain']).encode('utf-8')
				bytes_chain = bytearray(encoded_chain)
				temp_hash_chain = SHA256.new(data=bytes_chain)
				if temp_hash_chain.hexdigest() != chains[node_id]['chain_hash']:
					raise custom_errors.InvalidHash(err="Invalid Hash Chain.")

				# Check the validity of the sender by verifying the signature
				sender_public_key = RSA.importKey(extern_key=self.ring[node_id]['public_key'])
				pkcs1_15.new(sender_public_key).verify(
					msg_hash=temp_hash_chain,
					signature=chains[node_id]['signature_chain'].encode('ISO-8859-1')
				)

				# Check now the validity of the blocks in the chain
				# self.chain = chains[node_id]['chain']
				# self.validate_chain()

				# If we reach at this point it means the chain is valid,
				# so stop checking the other chains
				accepted_chain = chains[node_id]['chain']
				break

			# Catch all the possible exceptions
			except (
					custom_errors.InvalidHash,
					custom_errors.InvalidPreviousHashKey,
					ValueError
			) as e:
				print(f'Error at validating a given chain --> {str(e)}')
				print('Try the next one')
				pass

		if accepted_chain is not None:
			print(f'Accepted the chain from the node_{node_id}')
			return accepted_chain
		else:
			raise custom_errors.UnableResolveConflict(
				err='Could not find a valid chain. Unable to resolve the conflict.'
			)
