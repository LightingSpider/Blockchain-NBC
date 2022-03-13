import requests
import json

def send_transaction(address: str, port: int, transaction: dict):

    url = f"http://{address}:{str(port)}/transaction"

    payload = json.dumps(transaction)
    headers = {
      'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    return response.text

def send_block(address: str, port: int, block: dict):

    url = f"http://{address}:{str(port)}/block"

    payload = json.dumps(block)
    headers = {
      'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    return response.text

def send_ring(address: str, port: int, ring: dict):

    url = f"http://{address}:{str(port)}/ring"

    payload = json.dumps(ring)
    headers = {
      'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    return response.text

def send_settings(address: str, port: int, settings: dict):

    url = f"http://{address}:{str(port)}/settings"

    payload = json.dumps(settings)
    headers = {
      'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    return response.text

def get_init_settings(address: str, port: int):

    url = f"http://{address}:{str(port)}/init_settings"

    response = requests.request("GET", url, headers={}, data={})

    return response.json()

def send_new_node_arrived(address: str, port: int, new_node_specs: dict):

    url = f"http://{address}:{str(port)}/new_node_arrived"

    payload = json.dumps(new_node_specs)
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    return response.text

dummy_trans = {
    "id": "string1",
    "sender": "string",
    "receiver": "string",
    "signature": "string",
    "inputTransactions": ["string1", "string2"],
    "outputTransactions": [
        {
            "id": "string1",
            "officialTransactionId": "string",
            "receiverAddress": "string",
            "amount": "string"
        },
        {
            "id": "string2",
            "officialTransactionId": "string",
            "receiverAddress": "string",
            "amount": "string"
        }
   ]
}
# print(send_transaction(address='127.0.0.1', port=5000, transaction=dummy_trans))

dummy_block = {
    "previousHashKey": "string",
    "hashKey": "string",
    "nonce": "string",
    "timestamp": "string",
    "transactions": [
        {
            "id": "string1",
            "sender": "string",
            "receiver": "string",
            "signature": "string",
            "inputTransactions": ["string1", "string2"],
            "outputTransactions": [
                {
                    "id": "string1",
                    "officialTransactionId": "string",
                    "receiverAddress": "string",
                    "amount": "string"
                },
                {
                    "id": "string2",
                    "officialTransactionId": "string",
                    "receiverAddress": "string",
                    "amount": "string"
                }
            ]
        },
        {
            "id": "string2",
            "sender": "string",
            "receiver": "string",
            "signature": "string",
            "inputTransactions": ["string1", "string2"],
            "outputTransactions": [
                {
                    "id": "string1",
                    "officialTransactionId": "string",
                    "receiverAddress": "string",
                    "amount": "string"
                },
                {
                    "id": "string2",
                    "officialTransactionId": "string",
                    "receiverAddress": "string",
                    "amount": "string"
                }
            ]
        }
    ]
}
# print(send_block(address='127.0.0.1', port=5000, block=dummy_block))

dummy_ring = {

    "ring_dict": {
        "0": {
            "addres": "127.0.0.1",
            "port": 5000,
            "public_key": "address_string"
        },
        "1": {
            "addres": "127.0.0.1",
            "port": 5000,
            "public_key": "address_string"
        }
    },
    "signature": "signature_string",
    "hash_ring": "hash_ring_string"
}
# print(send_ring(address='127.0.0.1', port=5000, ring=dummy_ring))

dummy_settings = {
    "ring": dummy_ring,
    "UTXOs": {
        "node_1_public_address": {
            "trans_output_id": {
                "id": "string1",
                "officialTransactionId": "string",
                "receiverAddress": "string",
                "amount": "string"
            },
            "trans_output_2_id": {
                "id": "string1",
                "officialTransactionId": "string",
                "receiverAddress": "string",
                "amount": "string"
            }
        },
        "node_2_public_address": {
            "trans_output_3_id": {
                "id": "string1",
                "officialTransactionId": "string",
                "receiverAddress": "string",
                "amount": "string"
            },
            "trans_output_4_id": {
                "id": "string1",
                "officialTransactionId": "string",
                "receiverAddress": "string",
                "amount": "string"
            }
        }
    },
    "chain": [dummy_block, dummy_block]
}
# print(send_settings(address='127.0.0.1', port=5000, settings=dummy_settings))

# print(get_init_settings(address='127.0.0.1', port=5000))

# print(get_init_settings(address='127.0.0.1', port=5000))
