#!/usr/bin/env python3
import os
import sys
import web3
from web3 import Web3
import json
import requests

# Change these values to your values....
ESCROW = '0xC24F371c8656A06844207B312879b44053b55Ee9'
RANSOM = '0x435Eadd7743AcF8504d3AC141129350555C6b78b'
VICTIM_ID = '0xeb56d54d25c88a14edcb8ccf0190a3aa056086308b62cd5e141c136fc13d4aa0'
REGISTRY = ''
URL = 'https://codebreaker.ltsnet.net/eth/3a6f3a9ea2b9e53d/8e49a73b727d217fe13f45f70d8a8eaa71d9ae89f16b5b5158660260b9bfcc4e'

def connect_to_web3(url=None):
    if url is None: url = os.environ['URL']
    return Web3(Web3.HTTPProvider(url))

def increase_value_by(value, by):
    if len(value) == 32:
        hex_value = value.hex()
    else:
        hex_value = value

    int_value = int(hex_value, 16)

    if type(by) == int:
        int_by = by
    else:
        if len(by) == 32:
            hex_by = by.hex()
        else:
            hex_by = by
        int_by = int(hex_by, 16)

    hex_result = "%064x" % (int_value + int_by)
    return bytes.fromhex(hex_result)

def main(argv):

    # Connect to web3
    w3 = connect_to_web3(URL)
    escrow = w3.eth.contract(ESCROW)
    ransom = w3.eth.contract(RANSOM)
    # Accessing escrow, from Escrow.sol
    """
        Storage NAME                            Storage Number
        -------------------------------------------------------
        address owner;                          // 0
        uint ownerBalance;                      // 1
        address registry;                       // 2
        mapping(uint => address) vicToPayerMap; // 3
        mapping(uint => Victim) victimMap;      // 4
        mapping(uint => bytes32) decKeyMap;     // 5
        mapping(address => uint) ransomMap;     // 6
        mapping(uint => uint) escrowMap;        // 7
        mapping(uint => string) encFileMap;     // 8
        address[] ransomContracts;              // 9
        address oracleAccount;                  // 10
    """


    # Accessing each variables. Use getStorageAt(address, storage_number)

    # owner is at 0
    escrow_owner = w3.eth.getStorageAt(ESCROW, 0)
    print('Escrow owner: ' + escrow_owner.hex())

    # owner balance is at 1
    escrow_owner_balance = w3.eth.getStorageAt(ESCROW, 1)
    print('Escrow ownerBalance: ' + escrow_owner_balance.hex())

    # accessing array, ransomContracts at 9
    # accessing 9 returns the length
    escrow_ransom_array_length = w3.eth.getStorageAt(ESCROW, 9)
    print("Escrow ransomContracts length: " + escrow_ransom_array_length.hex())

    # store the length of array
    array_length = int(escrow_ransom_array_length.hex(), 16)

    # Accessing array element
    # 1) we need to get the index sum from the array.
    #    that is, sha3 of the index.
    #    so for the array at position 9, we need to get a sum for
    # i ='0000000000000000000000000000000000000000000000000000000000000009'
    #    '0' * 63 + '9'.
    #    and then we will calculate
    #    index_sum = w3.sha3(i)
    # 2) add array index to that sum.
    #    index_sum is a 256bit integer, and we will add the element index
    #    of the array to access it via getStorageAt().
    #    To do this, we will use increase_value_by(sum, idx) function.
    #    In other words, increase_value_by(a, b) will add b to a.
    # See: https://medium.com/aigang-network/how-to-read-ethereum-contract-storage-44252c8af925


    # create an hexadecimal index for the ransomContracts, 9,
    # justified with 63 zeros (make it to be a 64 digit hex integer)
    index = bytes.fromhex("%064x" % 9)
    index_sum = w3.sha3(index)

    for i in range(array_length):
        array_idx_i = increase_value_by(index_sum, i)
        array_elem_i = w3.eth.getStorageAt(ESCROW, array_idx_i)
        print('IDX  %d: ' % i + array_idx_i.hex())
        print('ELEM %d: ' % i + array_elem_i.hex())


    # Map access. Let's access ransomMap at 6 using the ransom address that we have...
    # ransomMap[RANSOM_ADDRESS] = victim_id
    # To do this, we need to do:
    # 1) create index by concatenating key + storage index.
    #  e.g., [64 digit hexadecimal RANSOM_ADDRESS][64 digit storage index, 6]
    # We can do this as follows.
    # index = "%064x" % int(RANSOM.lower(), 16) + "%064x" % 6
    #         ^ 64 digit ransom address in hex    ^ 64 digit storage index in hex
    # 2) Change that into bytestream and apply sha3
    # ransom_addr_sum = w3.sha3(bytes.fromhex(index))
    # 3) access with that sum
    # w3.eth.getStorageAt(ESCROW, ransom_addr_sum)
    # See: https://medium.com/coinmonks/a-practical-walkthrough-smart-contract-storage-d3383360ea1b
    map_index = bytes.fromhex("%064x" % 6)
    # Translate RANSOM address to 256bit hex
    ransom_hex = "%064x" % int(RANSOM.lower(), 16)
    ransom_addr_index = bytes.fromhex(ransom_hex) + map_index
    print(ransom_addr_index.hex())
    ransom_addr_sum = w3.sha3(ransom_addr_index)
    print(ransom_addr_sum.hex())
    ransom_map_result = w3.eth.getStorageAt(ESCROW, ransom_addr_sum)
    # this must be the same as your victim ID
    print("Escrow ransomMap[VICTIM_ID]: " + ransom_map_result.hex())


def load_contract(w3, json_path):
    with open(json_path) as fobj:
        info = json.load(fobj)
        return w3.eth.contract(abi=info['abi'], bytecode=info['bytecode'])

##################################

if __name__ == '__main__':
    sys.exit(main(sys.argv))
