import logging
from web3 import Web3
from config import chain_ids, dex_ids

def is_address(token):
    return Web3.is_address(token)

def filter_by_chain(pairs):
    filtered_pairs = []
    
    for pair in pairs:
        if pair.chain_id.lower() in chain_ids:
            filtered_pairs.append(pair)

    return filtered_pairs

def filter_by_dex(pairs):
    filtered_pairs = []
    
    for pair in pairs:
        if pair.dex_id.lower() in dex_ids:
            filtered_pairs.append(pair)

    return filtered_pairs

def filter_by_v3(pairs):
    filtered_pairs = []
    
    for pair in pairs:
        if pair.labels != None and ("v3" in pair.labels or "V3" in pair.labels):
            logging.info("V3")
        else:
            filtered_pairs.append(pair)

    return filtered_pairs