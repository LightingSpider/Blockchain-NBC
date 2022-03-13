from Crypto.PublicKey import RSA

'''
Wallet.rsa_key     --> RSA
Wallet.public_key  --> RSA.RsaKey
Wallet.private_key --> RSA.RsaKey
Wallet.address     --> str
'''
class Wallet:

    def __init__(self):

        # Key length, or size (in bits) of the RSA modulus. It must be at least 1024, but 2048 is recommended. The FIPS standard only defines 1024, 2048 and 3072.
        # We will save the rsa key object also, it will be usefull for signing.
        self.rsa_key = RSA.generate(2048)

        # Public and Private keys as strings
        # use exportKey() in order to extract the Key as a string
        self.public_key = self.rsa_key.public_key()
        self.private_key = self.rsa_key

        # The public address of the wallet is the same with its public key.
        self.address = self.public_key.export_key().decode('utf-8')

    '''
    The balance of a user's wallet is the sum of all unspent transaction outputs
    which have as recipient the specific wallet.
    '''
    def balance(self, UTXOs: dict):

        wallet_balance = 0.0
        wallet_UTXOs = UTXOs[self.address]

        for utxo in wallet_UTXOs.values():
            wallet_balance += float(utxo['amount'])

        return wallet_balance

