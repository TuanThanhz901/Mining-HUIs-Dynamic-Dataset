from collections import defaultdict
import os

def parse_file(file_path):
    transactions = []
    with open(file_path, 'r') as file:
        for tid, line in enumerate(file):
            parts = line.strip().split(":")
            items = list(map(int, parts[0].split()))
            transaction_utility = float(parts[1])
            item_utilities = list(map(float, parts[2].split()))
            transactions.append({
                'TID': tid + 1,
                'items': items,
                'transaction_utility': transaction_utility,
                'item_utilities': item_utilities
            })
    return transactions

def calculate_lu(transactions):
    lu = defaultdict(float)
    for transaction in transactions:
        for item in transaction['items']:
            lu[item] += transaction['transaction_utility']
    return lu

def filter_transactions(transactions, lu, minutil):
    filtered_transactions = []
    for transaction in transactions:
        filtered_items = []
        filtered_utilities = []
        for item, utility in zip(transaction['items'], transaction['item_utilities']):
            if lu[item] >= minutil:
                filtered_items.append(item)
                filtered_utilities.append(utility)
        if filtered_items:
            filtered_transactions.append({
                'TID': transaction['TID'],
                'items': filtered_items,
                'transaction_utility': transaction['transaction_utility'],
                'item_utilities': filtered_utilities
            })
    return filtered_transactions

def sort_items_and_transactions(transactions, lu):
    sorted_transactions = []
    for transaction in transactions:
        sorted_items_with_utilities = sorted(
            zip(transaction['items'], transaction['item_utilities']),
            key=lambda x: lu[x[0]]
        )
        sorted_items, sorted_utilities = zip(*sorted_items_with_utilities)
        sorted_transactions.append({
            'TID': transaction['TID'],
            'items': list(sorted_items),
            'transaction_utility': transaction['transaction_utility'],
            'item_utilities': list(sorted_utilities)
        })
    sorted_transactions.sort(
        key=lambda t: lu[t['items'][0]] if t['items'] else float('inf')
    )
    return sorted_transactions

def calculate_su_pset(transactions):
    su = defaultdict(float)
    pset = defaultdict(set)
    for transaction in transactions:
        cumulative_sum = 0.0
        for item, utility in zip(reversed(transaction['items']), reversed(transaction['item_utilities'])):
            cumulative_sum += utility
            su[item] += cumulative_sum
            pset[item].add(transaction['TID'])
    return su, pset
def calculate_pex_set(pset, transactions, item):
    pex_set = defaultdict(set)
    for tid in pset[item]:
        transaction = next((t for t in transactions if t['TID'] == tid), None)
        if transaction:
            for other_item in transaction['items']:
                if other_item != item:
                    pex_set[other_item].add(tid)
    return pex_set

def search_recursive_imefim(alpha, transactions, primary_items, secondary_items, minutil, pset):
    high_utility_itemsets = []
    for item in primary_items:
        beta = alpha + [item]
        beta_utility = 0.0
        beta_transactions = []
        for tid in pset[item]:
            transaction = next(t for t in transactions if t['TID'] == tid)
            if all(b in transaction['items'] for b in beta):
                idx = max(transaction['items'].index(b) for b in beta)
                beta_utility += sum(transaction['item_utilities'][transaction['items'].index(b)] for b in beta)
                new_items = transaction['items'][idx + 1:]
                new_utilities = transaction['item_utilities'][idx + 1:]
                if new_items:
                    beta_transactions.append({
                        'TID': tid,
                        'items': new_items,
                        'transaction_utility': transaction['transaction_utility'],
                        'item_utilities': new_utilities
                    })
        if beta_utility >= minutil:
            high_utility_itemsets.append((beta, beta_utility))
        pex_set = calculate_pex_set(pset, beta_transactions, item)
        su_beta = defaultdict(float)
        lu_beta = defaultdict(float)
        for transaction in beta_transactions:
            cumulative_sum = 0.0
            sum_utility_beta = 0.0
            check = True
            tid = transaction['TID']
            for beta_item in beta:
                utility_beta = next(
                    (t['item_utilities'][t['items'].index(beta_item)] for t in transactions if t['TID'] == tid),
                    None
                )
                sum_utility_beta += utility_beta
            for item, utility in zip(reversed(transaction['items']), reversed(transaction['item_utilities'])):
                if check:
                    cumulative_sum += utility + sum_utility_beta
                    check = False
                else:
                    cumulative_sum += utility
                su_beta[item] += cumulative_sum
                lu_beta[item] += transaction['transaction_utility']
        new_primary_items = [z for z in secondary_items if su_beta[z] >= minutil]
        new_secondary_items = [z for z in secondary_items if lu_beta[z] >= minutil]
        high_utility_itemsets += search_recursive_imefim(
            beta, transactions, new_primary_items, new_secondary_items, minutil, pex_set
        )
    return high_utility_itemsets

def run_imefim(file_path, minutil):
    transactions = parse_file(file_path)
    lu = calculate_lu(transactions)
    filtered_transactions = filter_transactions(transactions, lu, minutil)
    sorted_transactions = sort_items_and_transactions(filtered_transactions, lu)
    su, pset = calculate_su_pset(sorted_transactions)
    primary_items = [item for item in su if su[item] >= minutil]
    secondary_items = [item for item in lu if lu[item] >= minutil]
    primary_items.sort(key=lambda x: lu[x])
    secondary_items.sort(key=lambda x: lu[x])
    high_utility_itemsets = search_recursive_imefim(
        [], sorted_transactions, primary_items, secondary_items, minutil, pset
    )
    return high_utility_itemsets
