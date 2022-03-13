import pymongo
import configuration
from node import Node

def create_blocks_collection():
    result = configuration.db.create_collection("incoming_blocks", validator={
        "$jsonSchema": {
            "bsonType": "object",
            "additionalProperties": False,
            "required": ["previousHashKey", "hashKey", "nonce", "timestamp", "transactions"],
            "properties": {
                "previousHashKey": {
                    "bsonType": "string"
                },
                "hashKey": {
                    "bsonType": "string"
                },
                "nonce": {
                    "bsonType": "string"
                },
                "timestamp": {
                    "bsonType": "string"
                },
                "transactions": {
                    "bsonType": "array",
                    "items": {
                        "additionalProperties": False,
                        "required": ["id", "sender", "receiver", "amount", "signature", "inputTransactions", "outputTransactions"],
                        "properties": {
                            "id": {
                                "bsonType": "string"
                            },
                            "sender": {
                                "bsonType": "string"
                            },
                            "receiver": {
                                "bsonType": "string"
                            },
                            "amount": {
                                "bsonType": "string"
                            },
                            "signature": {
                                "bsonType": "string"
                            },
                            "inputTransactions": {
                                "bsonType": "array",
                                "items": {"bsonType": "string"}
                            },
                            "outputTransactions": {
                                "bsonType": "array",
                                "maxItems": 2,
                                "items": {
                                    "additionalProperties": False,
                                    "required": ["id", "officialTransactionId", "receiverAddress", "amount"],
                                    "properties": {
                                        "id": {
                                            "bsonType": "string"
                                        },
                                        "officialTransactionId": {
                                            "bsonType": "string"
                                        },
                                        "receiverAddress": {
                                            "bsonType": "string"
                                        },
                                        "amount": {
                                            "bsonType": "string"
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    })

    return result

# create_blocks_collection()

# Setting up replica set
# https://pymongo.readthedocs.io/en/stable/examples/high_availability.html#id1
