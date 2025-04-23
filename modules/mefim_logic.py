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
        items = transaction['items']
        transaction_utility = transaction['transaction_utility']
        for item in items:
            lu[item] += transaction_utility
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

def calculate_su(transactions):
    su = defaultdict(float)  
    for transaction in transactions:
        cumulative_sum = 0.0
        for item, utility in zip(reversed(transaction['items']), reversed(transaction['item_utilities'])):
            cumulative_sum += utility
            su[item] += cumulative_sum  
    return su

def determine_primary_secondary_items(su, lu, minutil):
    primary_items = [item for item in su if su[item] >= minutil]
    secondary_items = [item for item in lu if lu[item] >= minutil]
    primary_items.sort(key=lambda x: lu[x])
    secondary_items.sort(key=lambda x: lu[x])
    return primary_items, secondary_items

def search_recursive(alpha, projected_transactions, primary_items, secondary_items, minutil,original_transactions):
    high_utility_itemsets = []  
    for item in primary_items:
        beta = alpha + [item]  
        beta_transactions = [] 
        beta_utility = 0.0  
        for transaction in projected_transactions:
            current_tid = transaction['TID']
            original_transaction = next(t for t in original_transactions if t['TID'] == current_tid)
            if all(beta_item in original_transaction['items'] for beta_item in beta):
                beta_utility_for_transaction = sum(
                    original_transaction['item_utilities'][original_transaction['items'].index(beta_item)]
                    for beta_item in beta
                )

                beta_utility += beta_utility_for_transaction
               
                last_index = max(transaction['items'].index(beta_item) for beta_item in beta if beta_item in transaction['items'])
                new_items = transaction['items'][last_index + 1:]
                new_utilities = transaction['item_utilities'][last_index + 1:]

                if new_items:
                    beta_transactions.append({
                        'TID': transaction['TID'],  
                        'items': new_items,
                        'transaction_utility': transaction['transaction_utility'],
                        'item_utilities': new_utilities
                    })

        if beta_utility >= minutil:
            high_utility_itemsets.append((beta, beta_utility))

        su_beta = defaultdict(float)
        lu_beta = defaultdict(float)

        for transaction in beta_transactions:
            cumulative_sum = 0.0
            tID = transaction['TID']  
            sum_ultility_beta = 0.0
            check = True
            for item_beta in beta:
              utility_beta = next((t['item_utilities'][t['items'].index(item_beta)] for t in original_transactions if t['TID'] == tID), None)
              sum_ultility_beta += utility_beta
            for item, utility in zip(reversed(transaction['items']), reversed(transaction['item_utilities'])):
                if(check):
                  cumulative_sum += utility + sum_ultility_beta
                  check = False
                else:
                  cumulative_sum += utility
                su_beta[item] += cumulative_sum 
                lu_beta[item] += transaction['transaction_utility']  
       
        new_primary_items = [z for z in secondary_items if su_beta[z] >= minutil]
        new_secondary_items = [z for z in secondary_items if lu_beta[z] >= minutil]
        new_primary_items.sort(key=lambda x: lu_beta[x])
        new_secondary_items.sort(key=lambda x: lu_beta[x])
        high_utility_itemsets += search_recursive(
            beta, beta_transactions, new_primary_items, new_secondary_items, minutil, original_transactions
        )

    return high_utility_itemsets
def run_mefim(file_path, minutil):
    transactions = parse_file(file_path)
    lu = calculate_lu(transactions)
    filtered_transactions = filter_transactions(transactions, lu, minutil)
    sorted_transactions = sort_items_and_transactions(filtered_transactions, lu)
    su = calculate_su(sorted_transactions)
    primary_items, secondary_items = determine_primary_secondary_items(su, lu, minutil)
    high_utility_itemsets = search_recursive(
    alpha=[],
    projected_transactions=sorted_transactions,
    primary_items=primary_items,
    secondary_items=secondary_items,
    minutil=minutil, 
    original_transactions= transactions
)   
    return high_utility_itemsets