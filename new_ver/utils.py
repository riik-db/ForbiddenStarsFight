'''
Some simulator utils.
'''

import game_set_up as gsu 

import random

import copy

from collections import Counter

def unit_selection(faction,n,unit_prob,unit_selection):
    '''
    Selects units based on random selection. If the pool is empty then will end.
    '''

    if n == 0:
        n += 1
    if n > 5:
        n = 5

    faction_selected_units = []

    faction_units = [copy.deepcopy(unit) for unit in gsu.all_units if unit['faction']==faction]

    # Update `unit_count` in `org` where `unit_selection` is not None
    for unit, new_count in zip(faction_units, unit_selection):
        if new_count is not None:
            unit['unit_count'] = new_count

    for _ in range(n):
        # Select an index based on the probabilities
        selected_index = random.choices(range(len(unit_prob)), weights=unit_prob, k=1)[0]
        selected_unit = faction_units[selected_index]
        selected_unit['is_routed'] = False
        selected_unit['is_killed'] = False

        # Add to list
        faction_selected_units += [selected_unit] 

        # Reduce the unit count by 1
        selected_unit["unit_count"] -= 1

        #print(f"Selected unit: {selected_unit['unit_name']}, Remaining count: {selected_unit['unit_count']}")

        # Check if the unit count reaches 0 and adjust its probability
        if selected_unit["unit_count"] <= 0:
            unit_prob[selected_index] = 0  # Set probability to 0 for units with no count
            
            # Normalize probabilities to ensure they still sum to 1
            total_prob = sum(unit_prob)
            if total_prob > 0:  # Avoid division by zero
                unit_prob = [prob / total_prob for prob in unit_prob]
            else:
                break #don't add more units

    #Add reinf
    reinf_count_raw = random.choices([0,1,2,3],weights=(.3,.4, .2, .1), k=1)[0]
    #if faction in ['Orks','SM','Tyranid']:
    #    reinf_count_raw = random.choices([0,1,2,3],weights=(.1,.3, .5, .1), k=1)[0]
    
    reinf_count = min(reinf_count_raw,n)

    if reinf_count > 0:
        reinf = [copy.deepcopy(unit) for unit in gsu.all_units if unit['faction']==faction and unit['tier']==0][0]
        reinf['dice'] = 0
        reinf['is_routed'] = False
        reinf['is_killed'] = False
        reinf_units = [reinf]*reinf_count
        faction_selected_units += reinf_units


    # Return selected units
    remove_elements = ['faction','space_unit','unit_count']
    
    return [{
                key: value for key, value in unit.items() if key not in remove_elements
            } for unit in faction_selected_units]

def rollDice():
    return 'Bolter' if (rand := random.random()) <= 3/6 else 'Shield' if rand <= 5/6 else 'Morale'

def rollNdice(diceAmount: int):

    adj_dice = min(8,diceAmount)

    counted_rolls = Counter([rollDice() for _ in range(adj_dice)])

    return {category: counted_rolls.get(category, 0) for category in ['Bolter', 'Shield', 'Morale']}

def rollNdice_after(dice_set: dict, n:int, side = 'player'):
    
    diceAmount = sum(dice_set.values())

    adj_dice = min(n,8-diceAmount)

    counted_rolls = Counter([rollDice() for _ in range(adj_dice)])

    if side == 'enemy':
        return {'new_dice_enemy': {category: counted_rolls.get(category, 0) for category in ['Bolter', 'Shield', 'Morale']}}
    
    return {'new_dice': {category: counted_rolls.get(category, 0) for category in ['Bolter', 'Shield', 'Morale']}}


def upgraded_deck(nr_of_cards,odds,upgrades):

    complete_deck = []

    for i in range(3):

        if upgrades[i] == 0:
            new_cards = [False] * nr_of_cards[i]
            complete_deck += new_cards
            continue

        new_cards = random.choices(range(upgrades[i]),odds[i])[0] + 1
        tier_cards = [True] * new_cards + [False] * (nr_of_cards[i] - new_cards)
        random.shuffle(tier_cards)
        complete_deck += tier_cards

    start_cards = [False] * sum(complete_deck) + [True] * (5 - sum(complete_deck))
    random.shuffle(start_cards)

    final_deck = start_cards + complete_deck

    return final_deck

def card_weight(card_idx, state):
    if state == 'early':
        return 1.0

    if state == 'mid':
        if card_idx <= 4:
            return 1.0
        else:
            return 1.5

    # late
    if card_idx <= 4:
        return 1
    elif card_idx <= 8:
        return 1.5
    else:
        return 2
    
def weighted_draw(pool, weights, k):
    pool, weights = pool.copy(), weights.copy()
    chosen = []
    for _ in range(min(k, len(pool))):
        i = random.choices(range(len(pool)), weights=weights, k=1)[0]
        chosen.append(pool.pop(i))
        weights.pop(i)
    return chosen

def battle_cards(state,nr_of_cards,odds,upgrades):

    deck = upgraded_deck(nr_of_cards,odds,upgrades)

    # Create a list of indices where the value is True
    indices = [i for i, value in enumerate(deck) if value]  # Only take indices where value is True

    # Duplicate the indices
    duplicated_indices = [i for i in indices for _ in range(2)]  # Duplicate each index twice

    # Shuffle the list of duplicated indices
    random.shuffle(duplicated_indices)

    drawn_cards = duplicated_indices[:5]
    rest = duplicated_indices[5:]

    weights = [card_weight(i, state) for i in drawn_cards]
    sorted_drawn_cards = weighted_draw(drawn_cards, weights, 5)

    return (
        sorted_drawn_cards,
        rest
    )

def card_icons(faction,card_nr):
    return [v for tier in gsu.combat_cards[faction].values() for k,v in tier.items() if k == card_nr][0]