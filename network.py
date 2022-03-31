import requests
import json

def send_transaction(address: str, port: int, transaction: dict):

    url = f"http://[{address}]:{str(port)}/transaction"

    payload = json.dumps(transaction)
    headers = {
      'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    return response.text

def send_block(address: str, port: int, block: dict):

    url = f"http://[{address}]:{str(port)}/block"

    payload = json.dumps(block)
    headers = {
      'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    return response.text

def send_ring(address: str, port: int, ring: dict):

    url = f"http://[{address}]:{str(port)}/ring"

    payload = json.dumps(ring)
    headers = {
      'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    return response.text

def send_settings(address: str, port: int, settings: dict):

    url = f"http://[{address}]:{str(port)}/settings"

    payload = json.dumps(settings)
    headers = {
      'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    return response.text

def get_init_settings(address: str, port: int):

    url = f"http://[{address}]:{str(port)}/init_settings"

    response = requests.request("GET", url, headers={}, data={})

    return response.json()

def get_chain(address: str, port: int):

    url = f"http://[{address}]:{str(port)}/chain"

    response = requests.request("GET", url, headers={}, data={})

    return response.json()

def send_new_node_arrived(address: str, port: int, new_node_specs: dict):

    url = f"http://[{address}]:{str(port)}/new_node_arrived"

    payload = json.dumps(new_node_specs)
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    return response.text

