import utils as game_utils
import random
from collections import Counter
import copy

def choose_temp_tokens(n:int, prob = [0.5,0.5]):
    coin_flip = random.choices(range(2),prob)[0]

    if coin_flip == 0:
        return {'temp_tokens':{'Bolter':n}}
    return {'temp_tokens':{'Shield':n}}

def split_temp_tokens(n: int):
    shield = random.randint(0, n)
    bolter = n - shield
    return {'temp_tokens':{'Shield':shield,'Bolter':bolter}}


def check_any_unit(units,unit_name_list = {}, is_routed = False):
    
    if unit_name_list is not {}:
        return  any([unit for unit in units 
                     if unit['unit_name'] in unit_name_list and 
                     unit['is_routed'] == is_routed and
                     not unit['is_killed']])
    return any([unit for unit in units if unit['is_routed'] == is_routed])
    
def unroute_random_unit(units,side='player',unroute_all_units=False):
    # Filter out units that are routed (is_routed = True)
    routed_units = sorted([unit for unit in units if unit['is_routed'] and not unit['is_killed']],
                            key=lambda u: -u['tier']
                            )

    if unroute_all_units:
        units = [{**unit, 'is_routed': False} for unit in units]

    if routed_units:  # Check if there are any routed units
        selected_unit = routed_units[0]
        selected_unit['is_routed'] = False  # Change its status to False

    return {side + '_units' : units}  # Return the modified list

def rout_random_unit(units,side='player', tier = None, n = 1):

    if n == 1 and tier is None:
        # Filter out units that are unrouted (is_routed = False)
        unrouted_units = sorted([unit for unit in units if not unit['is_routed'] and not unit['is_killed']],
                                key=lambda u: u['tier']
                                )

        if unrouted_units:  # Check if there are any routed units
            selected_unit = unrouted_units[0] 
            selected_unit['is_routed'] = True  # Change its status to True

    if isinstance(tier,int):

        target_units = [unit for unit in units if unit['tier'] == tier]

        for u in target_units:
            u['is_routed'] = True


    return {side + '_units' : units}  # Return the modified list

def destory_routed_unit(units,side='player'):
    # Filter out units that are routed (is_routed = True)
    routed_units = sorted([unit for unit in units if unit['is_routed'] and not unit['is_killed']],
                          key=lambda u: u['tier']
                          )

    if routed_units:  # Check if there are any routed units
        selected_unit = routed_units[0]
        selected_unit['is_killed'] = True  # Change its status to True

    return {side + '_units' : units}  # Return the modified list

def destroy_unit(units, side='player', n=1, tier=None):
    # Alive units only
    alive_units = sorted([u for u in units if not u['is_killed']],
                            key=lambda u: (-u['is_routed'], u['tier'])
                        )

    if not alive_units or n <= 0:
        return {side + '_units': units}

    # Filter by tier if provided
    if isinstance(tier, int):
        alive_units = [u for u in alive_units if u['tier'] == tier]

        if not alive_units:
            return {side + '_units': units}

    # Limit n to available units
    n = min(n, len(alive_units))

    # Select units
    selected_units = alive_units[:n]

    # Kill & rout
    for u in selected_units:
        u['is_killed'] = True
        u['is_routed'] = True

    return {side + '_units': units}


def rerolldice(n, dice_set, dice_symbols=('Bolter', 'Shield', 'Morale')):
    # canonical base
    result = dice_set.copy()

    # dice eligible for reroll
    eligible = {k: v for k, v in dice_set.items() if k in dice_symbols}

    total_dice = sum(eligible.values())
    n_fin = min(n, total_dice)

    if n_fin == 0:
        return result

    # build pool
    pool = [k for k, v in eligible.items() for _ in range(v)]
    random.shuffle(pool)

    rerolled = pool[-n_fin:]

    # remove rerolled dice
    for die in rerolled:
        result[die] -= 1

    # roll new dice
    new_dice = game_utils.rollNdice(n_fin)

    # add new dice
    for die, cnt in new_dice.items():
        result[die] += cnt

    return result

def convertdice(n, dice, dice_type=None):

    dice_sum = sum(dice.values()) - dice[dice_type]
    if dice_sum == 0 or n <= 0:
        return dice.copy()

    convert_n = min(n, dice_sum)

    dice_pool = [k for k, v in dice.items() for _ in range(v)]
    random.shuffle(dice_pool)

    remaining = dice_pool[convert_n:]

    if dice_type is not None:
        converted = [dice_type] * convert_n
    else:
        converted = random.choices(
            ['Bolter', 'Shield', 'Morale'],
            k=convert_n
        )

    final = Counter(remaining + converted)

    return {
        k: final.get(k, 0)
        for k in ('Bolter', 'Shield', 'Morale')
    }

def remove_dice(player_dice, dice_set=('Bolter', 'Shield', 'Morale'), n=1):
    if n <= 0:
        return player_dice.copy()

    result = player_dice.copy()

    pool = [
        die
        for die in dice_set
        for _ in range(result.get(die, 0))
    ]

    for _ in range(min(n, len(pool))):
        chosen = random.choice(pool)
        result[chosen] -= 1
        pool.remove(chosen)

    return result

def biased_spend(max_dice, bias):
    options = list(range(max_dice + 1))
    weights = [bias ** k for k in range(max_dice + 1)]
    return random.choices(options, weights=weights, k=1)[0]





combat_cards = {
    'SM': {
        #Initial combat cards
        # Reconnaissance
        0: {'name': 'Reconnaissance',
            'card_icon': {'Bolter': 0, 'Shield': 1, 'Morale': 0, 'card_type':'both'},
            'card_effect': {
                'general' : lambda **kwargs: choose_temp_tokens(2),
                'unit' : lambda **kwargs: {},
            },
            },
        # Faith in the Emperor
        1: {'name' : 'Faith in the Emperor',
            'card_icon' : {'Bolter': 0, 'Shield': 0, 'Morale': 1, 'card_type':'def'},
            'card_effect' : {
                'general': lambda **kwargs: (
                                            new_dice_set := game_utils.rollNdice_after(copy.deepcopy(kwargs['player_dice']),1),
                                            {'player_dice' : {
                                                k: kwargs['player_dice'].get(k, 0) +
                                                   new_dice_set.get('new_dice',{}).get(k, 0)
                                                for k in set(kwargs['player_dice'])
                                                }
                                            }
                                            )[-1],
                'unit': lambda **kwargs: ( # Dice max -> rally
                                        player_dice_sum := sum(copy.deepcopy(kwargs['player_dice']).values()),
                                        new_dice_set := {'new_dice' : {'Morale' : 1}},
                                        player_dice_new := {'player_dice' : {
                                                k: kwargs['player_dice'].get(k, 0) +
                                                   new_dice_set.get('new_dice',{}).get(k, 0)
                                                for k in set(kwargs['player_dice'])
                                                }
                                        },
                                        unroute_random_unit(copy.deepcopy(kwargs['player_units']))
                                        if player_dice_sum == 8 or (any([unit for unit in copy.deepcopy(kwargs['player_units']) if unit['is_routed'] == True]) and random.random()>0.5) 
                                        else
                                        player_dice_new
                                        )[-1] if check_any_unit(kwargs['player_units'],unit_name_list=['Scouts','Space Marines']) else {},
            }
        },
        # Ambush
        2: {'name' : 'Ambush',
            'card_icon' : {'Bolter': 1, 'Shield': 0, 'Morale': 0, 'card_type':'att'},
            'card_effect' : {
                'general' : lambda **kwargs: choose_temp_tokens(2,[1,0]), 
                'unit' : lambda **kwargs: {'logs': {'enemy' : 'destroy_routed_or_spend_morale'} if check_any_unit(kwargs['player_units'],['Scouts']) else {}},
            }
        },
        # Fury of the Ultramar
        3: {'name' : 'Fury of the Ultramar',
            'card_icon' : {'Bolter': 1, 'Shield': 0, 'Morale': 0, 'card_type':'att'},
            'card_effect' : {
                'general': lambda **kwargs: {
                                'enemy_dice': rerolldice(1, copy.deepcopy(kwargs['enemy_dice']), ['Shield']),
                                'player_dice': rerolldice(1, copy.deepcopy(kwargs['player_dice']),['Shield']) if random.choice([True, False]) else kwargs['player_dice']
                            },
                'unit' : lambda **kwargs: {'logs': {'enemy' : 'lose_shield_dice_or_temp_2' } if check_any_unit(kwargs['player_units'],unit_name_list=['Space Marines']) else {}}
            }
        },
        # Blessed Power armour
        4: {'name' : 'Blessed Power armour',
            'card_icon': {'Bolter': 0, 'Shield': 1, 'Morale': 0, 'card_type':'def'},
            'card_effect' : {
                'general' : lambda **kwargs: choose_temp_tokens(2,[0,1]),
                'unit' : lambda **kwargs: {'player_dice' : convertdice(2,copy.deepcopy(kwargs['player_dice']),dice_type='Shield')} if check_any_unit(kwargs['player_units'],unit_name_list=['Space Marines']) else {}
            }
        },
        # Tier 0
        # Hold the line
        5: {'name' : 'Hold the line',
            'card_icon': {'Bolter': 0, 'Shield': 1, 'Morale': 1, 'card_type':'def'},
            'card_effect' : {
                'general' : lambda **kwargs: (temp_tokens := choose_temp_tokens(2,[0,1]),
                                                temp_tokens.update(unroute_random_unit(kwargs['player_units'])) 
                                                if not kwargs['is_attacker'] else {}
                                                )[0],
                'unit' : lambda **kwargs: (dice_face := random.choice(['Shield', 'Morale']),
                                           new_dice := {'new_dice' : {dice_face : 1}},
                                           player_output := {'player_dice' : {
                                                k: copy.deepcopy(kwargs['player_dice']).get(k, 0) +
                                                   new_dice.get('new_dice',{}).get(k, 0)
                                                for k in set(kwargs['player_dice'])
                                                }
                                            }
                                           )[-1]
                                            if sum(copy.deepcopy(kwargs['player_dice']).values()) < 8 and 
                                            check_any_unit(kwargs['player_units'],unit_name_list=['Space Marines']) 
                                            else {}
            }
        },
        # Glory and death
        6: {'name' : 'Glory and death',
            'card_icon': {'Bolter': 1, 'Shield': 0, 'Morale': 1, 'card_type':'att'},
            'card_effect' : {
                'general' : lambda **kwargs: ((temp_tokens := choose_temp_tokens(2,[1,0])),
                                                temp_tokens.update(unroute_random_unit(kwargs['player_units'])) 
                                                if kwargs['is_attacker'] else {}
                                                )[0],
                'unit' : lambda **kwargs: {'enemy_dice':remove_dice(copy.deepcopy(kwargs['enemy_dice']), dice_set=['Shield','Morale'])}
                                            if check_any_unit(kwargs['player_units'],unit_name_list=['Space Marines'])
                                            else {}
            }
        },
        # Veteran scouts
        7: {'name' : 'Veteran scouts',
            'card_icon': {'Bolter': 1, 'Shield': 1, 'Morale': 1, 'card_type':'both'},
            'card_effect' : {
                'general' : lambda **kwargs: split_temp_tokens(copy.deepcopy(kwargs['player_dice'])['Morale']),
                'unit' : lambda **kwargs: {}
            }
        },
        # Drop Pod assault
        8: {'name' : 'Veteran scouts',
            'card_icon': {'Bolter': 1, 'Shield': 1, 'Morale': 0, 'card_type':'both'},
            'card_effect' : {
                'general': lambda **kwargs: (
                                            new_dice_set := game_utils.rollNdice_after(copy.deepcopy(kwargs['player_dice']),1),
                                            {'player_dice' : {
                                                k: kwargs['player_dice'].get(k, 0) +
                                                   new_dice_set.get('new_dice',{}).get(k, 0)
                                                for k in set(kwargs['player_dice'])
                                                }
                                            }
                                            )[-1],
                'unit' : lambda **kwargs: ((unit_selection := [
                                            {'unit_name': 'Scouts',
                                            'tier': 0,
                                            'dice': 0,
                                            'hp': 2,
                                            'morale': 2,
                                            'is_routed': False,
                                            'is_killed': False},
                                            {'unit_name': 'Space Marines',
                                            'tier': 1,
                                            'dice': 0,
                                            'hp': 3,
                                            'morale': 3,
                                            'is_routed': False,
                                            'is_killed': False},
                                            ]),
                                            {'player_units' : copy.deepcopy(kwargs['player_units']) + ([unit_selection[0] if random.random()>0.5 else unit_selection[1]]),
                                                'player_dice' : remove_dice(copy.deepcopy(kwargs['player_dice']), dice_set=['Morale'])}
                                            if check_any_unit(kwargs['player_units'],unit_name_list=['Space Marines'])
                                            and kwargs['player_dice']['Morale'] > 0
                                            else {}
                                            )[-1]
            }
        },
        # Tier 2
        # Show no fear
        9: {'name' : 'Show no fear',
            'card_icon': {'Bolter': 0, 'Shield': 2, 'Morale': 1, 'card_type':'def'},
            'card_effect' : {
                'general' : lambda **kwargs: {'logs': {'player' : 'cannot_rout' }},
                'unit' : lambda **kwargs: (
                                           nr_routed_units := len([unit for unit in copy.deepcopy(kwargs['player_units']) if unit['is_routed']]),
                                           output_dict := unroute_random_unit(copy.deepcopy(kwargs['player_units']),
                                                                              side='player',
                                                                              unroute_all_units=True),
                                           player_dice_new := remove_dice(copy.deepcopy(kwargs['player_dice']), dice_set=['Morale']),
                                           output_dict.update(player_dice_new)
                                           if copy.deepcopy(kwargs['player_dice'])['Morale'] > 0 and nr_routed_units>0
                                           else {},
                                           output_dict
                                           )[-1] if check_any_unit(kwargs['player_units'],unit_name_list=['Space Marines']) else {}
            }
        },
        # Break the line
        10: {'name' : 'Break the line',
            'card_icon': {'Bolter': 1, 'Shield': 2, 'Morale': 0, 'card_type':'both'},
            'card_effect' : {
                'general' : lambda **kwargs: (
                                            nr_morale := min(3,copy.deepcopy(kwargs['player_dice']['Morale'])),
                                            round_id := kwargs.get('round_id'),
                                            bias := {
                                                1: 1,   # uniform
                                                2: 0.45,   # moderate bias to lower
                                                3: 0.35,    # heavy bias to 0–1
                                            }.get(round_id),
                                            nr_spend_morale := biased_spend(nr_morale, bias),
                                            nr_spend_on_bolter := random.choice(range(nr_spend_morale+1)),
                                            new_dice_set := {'new_dice':{'Bolter':nr_spend_on_bolter,
                                                         'Shield':nr_spend_morale-nr_spend_on_bolter,
                                                         'Morale':-nr_spend_morale}},
                                            {'player_dice' : {
                                                k: kwargs['player_dice'].get(k, 0) +
                                                   new_dice_set.get('new_dice',{}).get(k, 0)
                                                for k in set(kwargs['player_dice'])
                                                }
                                            }
                                            )[-1],
                'unit' : lambda **kwargs: {'logs': {'enemy': 'lose_1_faceup_card'}} 
                                            if check_any_unit(kwargs['player_units'],unit_name_list=['Land Raiders']) 
                                            and (
                                                (kwargs['is_attacker'] == True and kwargs['round_id'] > 1)
                                                or
                                                kwargs['is_attacker'] == False
                                            )
                                            else {}
            }
        },
        # Armoured advance
        11: {'name' : 'Armoured advance',
            'card_icon': {'Bolter': 2, 'Shield': 1, 'Morale': 0, 'card_type':'att'},
            'card_effect' : {
                'general' : lambda **kwargs: (
                                            new_dice_set := game_utils.rollNdice_after(copy.deepcopy(kwargs['player_dice']),1),
                                            {'player_dice' : {
                                                k: kwargs['player_dice'].get(k, 0) +
                                                   new_dice_set.get('new_dice',{}).get(k, 0)
                                                for k in set(kwargs['player_dice'])
                                                }
                                            }      
                                            )[-1],
                'unit' : lambda **kwargs: {'logs': {'player': 'additional_damage'}} 
                                            if check_any_unit(kwargs['player_units'],unit_name_list=['Land Raiders']) else {}
            }
        },
        # Tier 3
        # Emperor's glory
        12: {'name' : "Emperor's glory",
            'card_icon': {'Bolter': 0, 'Shield': 2, 'Morale': 2, 'card_type':'def'},
            'card_effect' : {
                'general' : lambda **kwargs: (
                                            new_dice_set := game_utils.rollNdice_after(copy.deepcopy(kwargs['player_dice']),2),
                                            {'player_dice' : {
                                                k: kwargs['player_dice'].get(k, 0) +
                                                   new_dice_set.get('new_dice',{}).get(k, 0)
                                                for k in set(kwargs['player_dice'])
                                                }
                                            }
                                            )[-1],
                'unit' : lambda **kwargs: (output_dict := unroute_random_unit( copy.deepcopy(kwargs['player_units']),side='player',unroute_all_units=True),
                                           
                                           round_id := kwargs.get('round_id'),
                                           bias := {
                                                1: 0.35,   # heavy bias to 0–1
                                                2: 0.65,   # moderate bias
                                                3: 1.0,    # uniform
                                            }.get(round_id),

                                           nr_bolter := min(8,kwargs['player_dice']['Bolter']),
                                           nr_shield := min(8,kwargs['player_dice']['Shield']),

                                           nr_spend_bolter := biased_spend(nr_bolter, bias),
                                           nr_spend_shield := biased_spend(nr_shield, bias),

                                           morale_dice_conversion := {'new_dice':
                                                                      {'Bolter': - nr_spend_bolter,
                                                                        'Shield': - nr_spend_shield,
                                                                        'Morale': nr_spend_bolter + nr_spend_shield
                                                                        }
                                                                    },
                                            player_dice_update := {'player_dice' : {
                                                k: kwargs['player_dice'].get(k, 0) +
                                                   morale_dice_conversion.get('new_dice',{}).get(k, 0)
                                                for k in set(kwargs['player_dice'])
                                                }
                                            },
                                            output_dict.update(player_dice_update),
                                            output_dict
                                            )[-1]
                                        if check_any_unit(kwargs['player_units'],unit_name_list=['Warlord Titans']) else {}
            }
        },
        # Emperor's might
        13: {'name' : "Emperor's might",
            'card_icon': {'Bolter': 3, 'Shield': 0, 'Morale': 0, 'card_type':'att'},
            'card_effect' : {
                'general' : lambda **kwargs: (
                                            new_dice_set := game_utils.rollNdice_after(copy.deepcopy(kwargs['player_dice']),2),
                                            {'player_dice' : {
                                                k: kwargs['player_dice'].get(k, 0) +
                                                   new_dice_set.get('new_dice',{}).get(k, 0)
                                                for k in set(kwargs['player_dice'])
                                                }
                                            }
                                            )[-1],
                'unit' : lambda **kwargs: (
                                            nr_bolter := min(8,copy.deepcopy(kwargs['player_dice'])['Bolter']),
                                            nr_spend_bolter := random.choice(range(nr_bolter+1)),
                                            output_dict := {'new_dice':{'Bolter': - nr_spend_bolter}},
                                            player_output := {'player_dice' : {
                                                k: kwargs['player_dice'].get(k, 0) +
                                                   output_dict.get('new_dice',{}).get(k, 0)
                                                for k in set(kwargs['player_dice'])
                                                }
                                            },
                                            player_output.update(choose_temp_tokens(nr_spend_bolter * 2 , [1,0])),
                                            player_output
                                            )[-1]
                                        if check_any_unit(kwargs['player_units'],unit_name_list=['Warlord Titans']) else {}
            }
        },
    },
    'Orks': {
        #Initial combat cards
        # Slugga Boyz
        0: {'name' : 'Slugga Boyz',
            'card_icon': {'Bolter': 1, 'Shield': 1, 'Morale': 0, 'card_type':'att'},
            'card_effect' : {
                'general' : lambda **kwargs: {'player_dice': rerolldice(8,copy.deepcopy(kwargs['player_dice']),['Morale']),
                                                'enemy_dice': rerolldice(8,copy.deepcopy(kwargs['enemy_dice']),['Morale'])},
                'unit' : lambda **kwargs: unroute_random_unit( copy.deepcopy(kwargs['player_units']))
                                        if check_any_unit(kwargs['player_units'],unit_name_list=['Ork Boyz']) 
                                        and any([unit['is_routed'] for unit in kwargs['player_units'] if not unit['is_killed']])
                                        else {}
            }
        },
        # Shoota Boyz
        1: {'name' : 'Shoota Boyz',
            'card_icon' : {'Bolter': 2, 'Shield': 0, 'Morale': 0, 'card_type':'att'},
            'card_effect' : {
                'general' : lambda **kwargs: {'player_dice': rerolldice(8,copy.deepcopy(kwargs['player_dice']),['Shield'])},
                'unit' : lambda **kwargs: (
                                        ork_units := len([unit for unit in copy.deepcopy(kwargs['player_units'])
                                                           if unit['unit_name']=='Ork Boyz' and 
                                                           not unit['is_routed'] and not unit['is_killed']]),
                                        {'enemy_dice': rerolldice(ork_units, copy.deepcopy(kwargs['enemy_dice']),['Shield'])}
                )[-1] if check_any_unit(kwargs['player_units'],unit_name_list=['Ork Boyz']) else {}
            }
        },
        # Ard Boyz
        2: {'name' : 'Ard Boyz',
            'card_icon' : {'Bolter': 0, 'Shield': 2, 'Morale': 0, 'card_type':'def'},
            'card_effect' : {
                'general' : lambda **kwargs: {'player_dice': rerolldice(8,copy.deepcopy(kwargs['player_dice']),['Bolter'])},
                'unit' : lambda **kwargs: (
                                        ork_units := len([unit for unit in copy.deepcopy(kwargs['player_units'])
                                                          if unit['unit_name']=='Ork Boyz' and 
                                                          not unit['is_routed'] and not unit['is_killed']]),
                                        {'enemy_dice': rerolldice(ork_units, copy.deepcopy(kwargs['enemy_dice']),['Bolter'])}
                )[-1] if check_any_unit(kwargs['player_units'],unit_name_list=['Ork Boyz']) else {}
            }
        },
        # Gretchin
        3: {'name' : 'Gretchin',
            'card_icon' : {'Bolter': 0, 'Shield': 0, 'Morale': 0, 'card_type':'both'},
            'card_effect' : {
                'general' : lambda **kwargs: {'temp_tokens': {'Bolter': 1,'Shield': 1},
                                                'enemy_dice' : rerolldice(1,copy.deepcopy(kwargs['enemy_dice']))
                                                },
                'unit' : lambda **kwargs: {},
            }
        }, 
        # Mek Boyz
        4: {'name' : 'Mek Boyz',
            'card_icon' : {'Bolter': 0, 'Shield': 0, 'Morale': 1, 'card_type':'def'},
            'card_effect' : {
                'general' : lambda **kwargs: (
                                            new_dice_set := game_utils.rollNdice_after(copy.deepcopy(kwargs['player_dice']),1),
                                            player_output := {'player_dice' : {
                                                k: kwargs['player_dice'].get(k, 0) +
                                                   new_dice_set.get('new_dice',{}).get(k, 0)
                                                for k in set(kwargs['player_dice'])
                                                }
                                            }
                                            )[-1],
                'unit' : lambda **kwargs: {'logs': {'player' : 'steal_top_card_icons' }}
                                           if check_any_unit(kwargs['player_units'],unit_name_list=['Ork Boyz']) 
                                           else {}
            }
        },  
        # Tier 0
        # Biker Nobz
        5: {'name' : 'Biker Nobz',
            'card_icon' : {'Bolter': 2, 'Shield': 1, 'Morale': 0, 'card_type':'att'},
            'card_effect' : {
                'general' : lambda **kwargs: {'enemy_dice': rerolldice(8,copy.deepcopy(kwargs['enemy_dice']),['Bolter'])},
                'unit' : lambda **kwargs: choose_temp_tokens(1,[1,0]) if check_any_unit(kwargs['player_units'],unit_name_list=['Nobz']) else {}
            }
        },
        # Sea of green
        6: {'name' : 'Sea of green',
            'card_icon' : {'Bolter': 1, 'Shield': 1, 'Morale': 0, 'card_type':'both'},
            'card_effect' : {
                'general' : lambda **kwargs: (
                                            (player_unrouted_units := len([unit for unit in copy.deepcopy(kwargs['player_units']) 
                                                                           if not unit['is_routed'] and not unit['is_killed']])),
                                            (enemy_unrouted_units := len([unit for unit in copy.deepcopy(kwargs['enemy_units']) 
                                                                          if not unit['is_routed'] and not unit['is_killed']])),
                                            (free_ork := {'unit_name': 'Ork Boyz',
                                            'tier': 0,
                                            'dice': 0,
                                            'hp': 2,
                                            'morale': 1,
                                            'is_routed': False,
                                            'is_killed': False}),
                                            card_effect := {'player_units' :  copy.deepcopy(kwargs['player_units']) + [free_ork]},
                                            enemy_morale := copy.deepcopy(kwargs['enemy_dice'])['Morale'],
                                            enemy_decision := {}
                                                              if player_unrouted_units + 1 <= enemy_unrouted_units
                                                              else { 'enemy_dice' : remove_dice( copy.deepcopy(kwargs['enemy_dice']), dice_set=['Morale'])}
                                                              if (random.random()>0.5 or enemy_unrouted_units == 0) and enemy_morale > 0
                                                              else rout_random_unit( copy.deepcopy(kwargs['enemy_units']),side='enemy'),
                                            card_effect.update(enemy_decision),
                                            card_effect
                                            )[-1],
                'unit' : lambda **kwargs: {}
            }
        },
        # Waaagh!!!!
        7: {'name' : 'Waaagh!!!!',
            'card_icon' : {'Bolter': 0, 'Shield': 0, 'Morale': 3, 'card_type':'both'},
            'card_effect' : {
                'general' : lambda **kwargs: unroute_random_unit(copy.deepcopy(kwargs['player_units']))
                                            if any([unit['is_routed'] for unit in copy.deepcopy(kwargs['player_units']) 
                                                    if not unit['is_killed']]) else {},
                'unit' : lambda **kwargs: (
                                            (ork_units := len([unit for unit in copy.deepcopy(kwargs['player_units'])
                                                               if unit['unit_name']=='Ork Boyz' and 
                                                                  not unit['is_routed'] and
                                                                  not unit['is_killed']])),
                                            choose_temp_tokens(ork_units,[1,0]) if check_any_unit(kwargs['player_units'],unit_name_list=['Ork Boyz']) else {}
                                        )[-1]
            }
        },
        # Mega Nobz
        8: {'name' : 'Mega Nobz',
            'card_icon' : {'Bolter': 1, 'Shield': 2, 'Morale': 0, 'card_type':'def'},
            'card_effect' : {
                'general' : lambda **kwargs: {'enemy_dice': rerolldice(8,copy.deepcopy(kwargs['enemy_dice']),['Shield'])},
                'unit' : lambda **kwargs: choose_temp_tokens(1,[0,1]) if check_any_unit(kwargs['player_units'],unit_name_list=['Nobz']) else {}
            }
        },
        # Tier 2
        # Rokkit Wagon
        9: {'name' : 'Rokkit Wagon',
            'card_icon' : {'Bolter': 3, 'Shield': 0, 'Morale': 0, 'card_type':'att'},
            'card_effect' : {
                'general' : lambda **kwargs: {},
                'unit' : lambda **kwargs: choose_temp_tokens(3,[1,0]) if check_any_unit(kwargs['player_units'],unit_name_list=['Battlewagons']) else {}
            }
        },
        # Weirdboyz
        10: {'name' : 'Weirdboyz',
            'card_icon' : {'Bolter': 1, 'Shield': 1, 'Morale': 1, 'card_type':'both'},
            'card_effect' : {
                'general' : lambda **kwargs: {'player_dice' : rerolldice(8,copy.deepcopy(kwargs['player_dice'])),
                                               'enemy_dice' : rerolldice(8,copy.deepcopy(kwargs['enemy_dice']))
                                              },
                'unit' : lambda **kwargs: {'logs': {'player': 'copy_temp_tokens'}} if check_any_unit(kwargs['player_units'],unit_name_list=['Ork Boyz']) else {}
            }
        },
        # Party wagon
        11: {'name' : 'Party Wagon',
            'card_icon' : {'Bolter': 1, 'Shield': 2, 'Morale': 0, 'card_type':'def'},
            'card_effect' : {
                'general' : lambda **kwargs: (
                                            free_ork := {'unit_name': 'Ork Boyz',
                                                        'tier': 0,
                                                        'dice': 0,
                                                        'hp': 2,
                                                        'morale': 1,
                                                        'is_routed': False,
                                                        'is_killed': False},
                                            {'player_units' : copy.deepcopy(kwargs['player_units']) + [free_ork]}
                                            )[-1],
                'unit' : lambda **kwargs: {
                            'temp_tokens': {
                                'Bolter': 2,
                                'Shield': 2
                            }} if (
                                check_any_unit(kwargs['player_units'],unit_name_list=['Battlewagons']) and
                                len([unit for unit in copy.deepcopy(kwargs['player_units']) 
                                     if not unit['is_routed'] and not unit['is_killed']]) >
                                len([unit for unit in copy.deepcopy(kwargs['enemy_units']) 
                                     if not unit['is_routed'] and not unit['is_killed']])
                            ) else {}
            }
        },
        # Tier 3
        # Snapper Gargant
        12: {'name' : 'Snapper Gargant',
            'card_icon' : {'Bolter': 4, 'Shield': 1, 'Morale': 0, 'card_type':'att'},
            'card_effect' : {
                'general' : lambda **kwargs: {},
                'unit' : lambda **kwargs: {'logs': {'enemy': 'lose_1_faceup_card'}} 
                                        if check_any_unit(kwargs['player_units'],unit_name_list=['Gargants'])
                                        and (
                                                (kwargs['is_attacker'] == True and kwargs['round_id'] > 1)
                                                or
                                                kwargs['is_attacker'] == False
                                            )
                                        else {}
            }
        },
        # Smasher Gargant
        13: {'name' : 'Smasher Gargant',
            'card_icon' : {'Bolter': 2, 'Shield': 3, 'Morale': 0, 'card_type':'def'},
            'card_effect' : {
                'general' : lambda **kwargs: {},
                'unit' : lambda **kwargs: (
                                            copy_enemy_units := copy.deepcopy(kwargs['enemy_units']),
                                            
                                            enemy_units_index := [
                                                (i, unit)
                                                for i, unit in enumerate(copy_enemy_units)
                                                if not unit['is_killed']
                                            ],
                                            target_index := (
                                                None if not enemy_units_index
                                                else sorted(
                                                enemy_units_index,
                                                key=lambda x: (x[1]['is_routed'], -x[1]['tier'])
                                            )[0][0]
                                            ),
                                            {} if target_index is None 
                                                or not check_any_unit(kwargs['player_units'],unit_name_list=['Gargants'])
                                            else (
                                                n_remove_dice := copy_enemy_units[target_index]['tier'],
                                                n_dice := sum(kwargs['enemy_dice'].values()),
                                                n_adjust_remove_dice := min(n_remove_dice, n_dice),
                                                unit := copy_enemy_units[target_index],
                                                unit.update({'is_killed': True, 'is_routed': True}),
                                                new_enemy_dice := remove_dice(copy.deepcopy(kwargs['enemy_dice']),n=n_adjust_remove_dice),
                                                {'enemy_units' : copy_enemy_units}
                                                if random.random() > 0.5 and n_remove_dice > 0
                                                else {'enemy_dice' : new_enemy_dice}
                                            )[-1]
                                        )[-1]
                                        
            }
        }
    },
    'Eldar': {
        # Command of the Autarch
        0: {'name' : 'Command of the Autarch',
            'card_icon' : {'Bolter': 0, 'Shield': 0, 'Morale': 0, 'card_type':'both'},
            'card_effect' : {
                'general' : lambda **kwargs: ( # Dice max -> rally
                                        player_dice_sum := sum(copy.deepcopy(kwargs['player_dice']).values()),
                                        player_unrouted_units := any([unit['is_routed'] for unit in copy.deepcopy(kwargs['player_units'])]),
                                        player_dice := copy.deepcopy(kwargs['player_dice']),
                                        player_dice.__setitem__('Morale', player_dice['Morale'] + 1),
                                        player_output := unroute_random_unit(copy.deepcopy(kwargs['player_units']))
                                                    if player_dice_sum == 8 or (random.random()>0.5 and player_unrouted_units) 
                                                    else {'player_dice' : player_dice},
                                        player_output.update({'logs':{'player': 'get_additional_temp_from_hand'}}),
                                        result := player_output
                                        )[-1],
                'unit' : lambda **kwargs: {}
            }
        },
        # Hit and Run
        1: {'name' : 'Hit and Run',
            'card_icon' : {'Bolter': 1, 'Shield': 0, 'Morale': 0, 'card_type':'att'},
            'card_effect' : {
                'general' : lambda **kwargs: choose_temp_tokens(2,[1,0]),
                'unit' : lambda **kwargs: {}
            }
        },
        # Ranger support
        2: {'name' : 'Ranger Support',
            'card_icon' : {'Bolter': 0, 'Shield': 1, 'Morale': 1, 'card_type':'both'},
            'card_effect' : {
                'general' : lambda **kwargs: {'temp_tokens':{'Shield':1,'Bolter':1}} if kwargs['is_attacker'] == True else {},
                'unit' : lambda **kwargs: {}
            }
        },
        # Howling Banshees
        3: {'name' : 'Howling Banshees',
            'card_icon' : {'Bolter': 1, 'Shield': 0, 'Morale': 0, 'card_type':'att'},
            'card_effect' : {
                'general' : lambda **kwargs: (
                                            new_dice_set := game_utils.rollNdice_after(copy.deepcopy(kwargs['player_dice']),1),
                                            {'player_dice' : {
                                                k: kwargs['player_dice'].get(k, 0) +
                                                   new_dice_set.get('new_dice',{}).get(k, 0)
                                                for k in set(kwargs['player_dice'])
                                                }
                                            }
                                            )[-1],
                'unit' : lambda **kwargs: (player_output := rout_random_unit(copy.deepcopy(kwargs['enemy_units']),side='enemy'),
                                           player_new_dice := remove_dice(copy.deepcopy(kwargs['enemy_dice']), ['Morale']),
                                           player_output.update(player_new_dice),
                                           player_output
                                          )[-1]
                                        if copy.deepcopy(kwargs['player_dice'])['Morale'] > 0 # and random.random() > 0.5
                                          and check_any_unit(kwargs['player_units'],unit_name_list=['Aspect Warriors']) else {}
            }
        },
        # Striking Scorpions
        4: {'name' : 'Striking Scorpions',
            'card_icon' : {'Bolter': 0, 'Shield': 1, 'Morale': 0, 'card_type':'def'},
            'card_effect' : {
                'general' : lambda **kwargs: (
                                            new_dice_set := game_utils.rollNdice_after(copy.deepcopy(kwargs['player_dice']),1),
                                            {'player_dice' : {
                                                k: kwargs['player_dice'].get(k, 0) +
                                                   new_dice_set.get('new_dice',{}).get(k, 0)
                                                for k in set(kwargs['player_dice'])
                                                }
                                            }
                                            )[-1],
                'unit' : lambda **kwargs: {'enemy_dice':remove_dice(copy.deepcopy(kwargs['enemy_dice']))}
                                        if check_any_unit(kwargs['player_units'],unit_name_list=['Aspect Warriors']) else {}
            }
        },
        # Swooping Hawks
        5: {'name' : 'Swooping Hawks',
            'card_icon' : {'Bolter': 0, 'Shield': 2, 'Morale': 0, 'card_type':'def'},
            'card_effect' : {
                'general' : lambda **kwargs: {'logs':{'enemy': 'lose_3_temp_bolter'}} if kwargs['is_attacker'] == False else {},
                'unit' : lambda **kwargs: (player_output := choose_temp_tokens(2, [1,0]),
                                           player_dice := remove_dice(copy.deepcopy(kwargs['player_dice']), dice_set=['Morale']),
                                           player_output.update(player_dice)
                                           )[0]
                                        if check_any_unit(kwargs['player_units'],unit_name_list=['Aspect Warriors']) 
                                         and copy.deepcopy(kwargs['player_dice'])['Morale'] > 0 # and random.random() > 0.5
                                         else {}
            }
        },
        # Wraithguard advance
        6: {'name' : 'Wraithguard advance',
            'card_icon' : {'Bolter': 1, 'Shield': 0, 'Morale': 1, 'card_type':'both'},
            'card_effect' : {
                'general' : lambda **kwargs: (
                                            player_output := game_utils.rollNdice_after(copy.deepcopy(kwargs['player_dice']),1) 
                                                if random.random()>0.5
                                                else {'new_dice' : {'Morale': 1}} if sum(copy.deepcopy(kwargs['player_dice']).values()) < 8 else {},
                                            n_shield := copy.deepcopy(kwargs['player_dice'])['Shield'] + player_output.get('new_dice', {}).get('Shield', 0),
                                            n_convert := min(2,n_shield), #min(random.choice(range(3)),n_shield),
                                            new_dice_set := {'new_dice': {'Bolter':n_convert,'Shield':-n_convert}} if n_convert > 0 else {},
                                            {'player_dice' : {
                                                k: kwargs['player_dice'].get(k, 0) +
                                                   player_output.get('new_dice', {}).get(k, 0) + 
                                                   new_dice_set.get('new_dice',{}).get(k, 0)
                                                for k in set(kwargs['player_dice'])
                                                }
                                            },
                                            )[-1],
                'unit' : lambda **kwargs: {} if not check_any_unit(kwargs['player_units'], ['Wraithguard']) else
                                        (
                                            {'enemy_dice': remove_dice(copy.deepcopy(kwargs['enemy_dice']), ['Morale'])}
                                            if copy.deepcopy(kwargs['enemy_dice'])['Morale'] > 0 or 
                                            #if (kwargs['enemy_dice']['Morale'] > 0 and random.random() > 0.5) or 
                                                all([unit['is_routed'] for unit in copy.deepcopy(kwargs['enemy_units'])])
                                            else rout_random_unit(copy.deepcopy(kwargs['enemy_units']), side='enemy')
                                        )
            }
        },
        # Fire Dragon's vengeance
        7: {'name' : "Fire Dragon's vengeance",
            'card_icon' : {'Bolter': 2, 'Shield': 0, 'Morale': 0, 'card_type':'att'},
            'card_effect' : {
                'general' : lambda **kwargs: {'logs':{'enemy': 'lose_all_temp_shield'}} if kwargs['is_attacker'] else {},
                'unit' : lambda **kwargs: choose_temp_tokens(2, [0,1])
                                        if check_any_unit(kwargs['player_units'],unit_name_list=['Aspect Warriors'])
                                        else {}
            }
        },
        # Wraithguard support
        8: {'name' : 'Wraithguard support',
            'card_icon' : {'Bolter': 0, 'Shield': 1, 'Morale': 1, 'card_type':'both'},
            'card_effect' : {
                'general' : lambda **kwargs:  (
                                            player_output := game_utils.rollNdice_after(copy.deepcopy(kwargs['player_dice']),1) 
                                                if random.random()>0.5
                                                else {'new_dice' : {'Morale': 1}} if sum(copy.deepcopy(kwargs['player_dice']).values()) < 8 else {},
                                            n_bolter := copy.deepcopy(kwargs['player_dice'])['Bolter'] + player_output.get('new_dice', {}).get('Bolter', 0),
                                            n_convert := min(2,n_bolter), #min(random.choice(range(3)),n_bolter),
                                            new_dice_set := {'new_dice': {'Shield':n_convert,'Bolter':-n_convert}},
                                            {'player_dice' : {
                                                k: kwargs['player_dice'].get(k, 0) +
                                                   player_output.get('new_dice', {}).get(k, 0) + 
                                                   new_dice_set.get('new_dice',{}).get(k, 0)
                                                for k in set(kwargs['player_dice'])
                                                }
                                            },
                                            )[-1],
                'unit' : lambda **kwargs: (
                                            all_rally := all(not unit['is_routed'] for unit in copy.deepcopy(kwargs['player_units'])),
                                            (
                                                player_output := unroute_random_unit(copy.deepcopy(kwargs['player_units'])),
                                                player_dice := {'player_dice' : remove_dice(copy.deepcopy(kwargs['player_dice']), dice_set=['Morale'])},
                                                player_output.update(player_dice),
                                                player_output
                                            )[-1]
                                            if check_any_unit(kwargs['player_units'], unit_name_list=['Wraithguard'])
                                            and copy.deepcopy(kwargs['player_dice'])['Morale'] > 0
                                            # and random.random() > 0.5
                                            and not all_rally
                                            else {}
                                        )[-1]
            }
        },
        # Wave Serpent
        9: {'name' : 'Wave Serpent',
            'card_icon' : {'Bolter': 1, 'Shield': 2, 'Morale': 0, 'card_type':'def'},
            'card_effect' : {
                'general' : lambda **kwargs : (
                                            new_dice_set := game_utils.rollNdice_after(copy.deepcopy(kwargs['player_dice']),1),
                                            player_output := {'player_dice' : {
                                                k: kwargs['player_dice'].get(k, 0) +
                                                   new_dice_set.get('new_dice',{}).get(k, 0)
                                                for k in set(kwargs['player_dice'])
                                                }
                                            },
                                            enemy_morale := copy.deepcopy(kwargs['enemy_dice'])['Morale'],
                                            additional_output := { 'enemy_dice' : remove_dice(copy.deepcopy(kwargs['enemy_dice']), dice_set=['Morale'])}
                                                if (random.random()>0.5 and enemy_morale > 0)
                                                else choose_temp_tokens(3, [0,1]),
                                            player_output.update(additional_output),
                                            player_output
                                        )[-1],
                'unit'  : lambda **kwargs: {}
            }
        },
        # Spiritseer's guidance
        10: {'name' : "Spiritseer's guidance",
            'card_icon' : {'Bolter': 1, 'Shield': 1, 'Morale': 1, 'card_type':'both'},
            'card_effect' : {
                'general' : lambda **kwargs : (
                                            new_dice_set := game_utils.rollNdice_after(copy.deepcopy(kwargs['player_dice']),1),
                                            player_output := {'player_dice' : {
                                                k: kwargs['player_dice'].get(k, 0) +
                                                   new_dice_set.get('new_dice',{}).get(k, 0)
                                                for k in set(kwargs['player_dice'])
                                                }
                                            },
                                            additional_output := {'logs':{'player': 'no_damage'},
                                                                  **rout_random_unit(copy.deepcopy(kwargs['player_units']))
                                                                  }
                                                # if (random.random()>0.5 and not all([unit['is_routed'] for unit in kwargs['player_units']]))
                                                if (not all([unit['is_routed'] for unit in copy.deepcopy(kwargs['player_units'])]))
                                                else {},
                                            player_output.update(additional_output),
                                            player_output
                                        )[-1],
                'unit'  : lambda **kwargs: {}
            }
        },
        # Fire Prism
        11: {'name' : "Fire Prism",
            'card_icon' : {'Bolter': 2, 'Shield': 1, 'Morale': 0, 'card_type':'att'},
            'card_effect' : {
                'general' : lambda **kwargs : (
                                            n_morale := copy.deepcopy(kwargs['player_dice'])['Morale'],
                                            n_convert := n_morale, #random.choice(range(n_morale+1)),
                                            new_dice_set := {'new_dice': {'Morale':-n_convert,'Bolter':n_convert}},
                                            player_output := {'player_dice' : {
                                                k: kwargs['player_dice'].get(k, 0) +
                                                   new_dice_set.get('new_dice',{}).get(k, 0)
                                                for k in set(kwargs['player_dice'])
                                                }
                                            }
                                        )[-1],
                'unit'  : lambda **kwargs: {} if not check_any_unit(kwargs['player_units'],unit_name_list=['Falcons'])
                                        else choose_temp_tokens(2, [1,0]) if kwargs['is_attacker']
                                        else {'logs':{'enemy': 'lose_5_tmp_shield'}}
            }
        },
        # Holofield Emitter
        12: {'name' : "Holofield Emitter",
            'card_icon' : {'Bolter': 1, 'Shield': 2, 'Morale': 1, 'card_type':'def'},
            'card_effect' : {
                'general' : lambda **kwargs : (
                                            new_dice_set := game_utils.rollNdice_after(copy.deepcopy(kwargs['player_dice']),1),
                                            player_dice := copy.deepcopy(kwargs['player_dice']),
                                            output := {'player_dice' : {
                                                k: player_dice.get(k, 0) + 
                                                new_dice_set.get('new_dice',{}).get(k, 0)
                                                for k in set(player_dice)
                                                }
                                            },
                                            output.update({'logs':{'player': 'add_combat_card'}}),
                                            output
                                        )[-1],
                'unit'  : lambda **kwargs: {'logs':{'player': 'get_additional_temp_from_hand'}}
                                    if check_any_unit(kwargs['player_units'],unit_name_list=['Warlock Titans'])
                                    else {}
            }
        },
        # Psychic Lance
        13: {'name' : "Psychic Lance",
            'card_icon' : {'Bolter': 2, 'Shield': 1, 'Morale': 0, 'card_type':'att'},
            'card_effect' : {
                'general' : lambda **kwargs : (
                                            new_dice_set := game_utils.rollNdice_after(copy.deepcopy(kwargs['player_dice']),1),
                                            player_dice := copy.deepcopy(kwargs['player_dice']),
                                            output := {'player_dice' : {
                                                k: player_dice.get(k, 0) + 
                                                new_dice_set.get('new_dice',{}).get(k, 0)
                                                for k in set(player_dice)
                                                }
                                            },
                                            output.update({'logs':{'enemy': 'lose_1_card_hand'}}),
                                            output
                                        )[-1],
                'unit'  : lambda **kwargs: (temp_icon := choose_temp_tokens(4, [1,0]),
                                            enemy_log := {'logs':{'enemy': 'lose_1_faceup_card'}},
                                            final_outcome :=  enemy_log  
                                            if (
                                                (kwargs['is_attacker'] == True and kwargs['round_id'] > 1)
                                                or
                                                kwargs['is_attacker'] == False
                                            ) and random.random()>0.5 else temp_icon,
                                            final_outcome
                                            if check_any_unit(kwargs['player_units'],unit_name_list=['Warlock Titans'])
                                            else {}
                                            )[-1]
            }
        },
    },
    'CSM' : {
        # Lure of Chaos
        0: {'name' : 'Lure of Chaos',
            'card_icon' : {'Bolter': 0, 'Shield': 0, 'Morale': 1, 'card_type':'both'},
            'card_effect' : {
                'general' : lambda **kwargs: ( # Dice max -> rally
                                        enemy_routed_units := all([unit['is_routed'] for unit in copy.deepcopy(kwargs['enemy_units'])]),
                                        enemy_no_rout := 'cannot_rout' in kwargs['enemy_logs'],
                                        enemy_dice_sum := game_utils.rollNdice_after(copy.deepcopy(kwargs['enemy_dice']),1,side='enemy')['new_dice_enemy'],
                                        enemy_output := {'enemy_dice' : {
                                                            k: kwargs['enemy_dice'].get(k, 0) + enemy_dice_sum.get(k, 0)
                                                            for k in set(kwargs['enemy_dice'])
                                                            }
                                                        },
                                        enemy_output.update(rout_random_unit(copy.deepcopy(kwargs['enemy_units']), side = 'enemy')
                                                            if not enemy_no_rout else {}),
                                        free_cultist := {'unit_name': 'Cultists',
                                                        'tier': 0,
                                                        'dice': 0,
                                                        'hp': 2,
                                                        'morale': 2,
                                                        'is_routed': False,
                                                        'is_killed': False},
                                        player_output := {'player_units' : copy.deepcopy(kwargs['player_units']) + [free_cultist]},
                                        
                                        end_result := enemy_output
                                                    if (random.random()>0.5 or enemy_routed_units) or enemy_no_rout
                                                    else player_output
                                        )[-1],
                'unit' : lambda **kwargs: choose_temp_tokens(2)
                                    if check_any_unit(kwargs['player_units'],unit_name_list=['Cultists']) else {}
            }
        },
        # Dark Faith
        1: {'name' : 'Dark Faith',
            'card_icon' : {'Bolter': 0, 'Shield': 0, 'Morale': 1, 'card_type':'both'},
            'card_effect' : {
                'general' : lambda **kwargs: (
                                player_dice := copy.deepcopy(kwargs['player_dice']),
                                player_dice.__setitem__('Morale', player_dice['Morale'] + 1),
                                {'player_dice' : player_dice} if sum(player_dice.values()) <= 8 else {}
                )[-1],
                'unit'  : lambda **kwargs: {}
            }
        },
        # Impure Zeal
        2: {'name' : 'Impure Zeal',
            'card_icon' : {'Bolter': 1, 'Shield': 1, 'Morale': 0, 'card_type':'both'},
            'card_effect' : {
                'general' : lambda **kwargs: unroute_random_unit(copy.deepcopy(kwargs['player_units']))
                            if copy.deepcopy(kwargs['player_dice'])['Morale'] > copy.deepcopy(kwargs['enemy_dice'])['Morale']
                            else {},
                'unit' : lambda **kwargs: (
                                    enemy_no_rout := 'cannot_rout' in kwargs['enemy_logs'],
                                    n_cultist := len([unit for unit in copy.deepcopy(kwargs['player_units']) if unit['unit_name']=='Cultists' and unit['is_routed'] == False]) if not enemy_no_rout else 0,
                                    enemy_routed_units := all([unit['is_routed'] == True for unit in copy.deepcopy(kwargs['enemy_units'])]),
                                    unit_ability := check_any_unit(kwargs['player_units'],unit_name_list=['Cultists']),
                                    choose_temp_tokens(n_cultist, [1,0])
                                    if (random.random()>0.5 or enemy_routed_units or enemy_no_rout) and unit_ability
                                    else rout_random_unit(copy.deepcopy(kwargs['enemy_units']),side='enemy') if unit_ability else {}
                                    )[-1]
            }
        },
        # Khorne's Rage
        3: {'name' : "Khorne's Rage",
            'card_icon' : {'Bolter': 1, 'Shield': 0, 'Morale': 0, 'card_type':'att'},
            'card_effect' : {
                'general' : lambda **kwargs: (player_output := choose_temp_tokens(3, [1,0]),
                                              n_bolter := copy.deepcopy(kwargs['player_dice'])['Bolter'],
                                              player_remove_dice := {'player_dice' : remove_dice(copy.deepcopy(kwargs['player_dice']), dice_set=['Bolter'])},
                                              output := {**player_output, **player_remove_dice}
                                              if n_bolter > 0 # and random.random() > 0.5 
                                              else {}
                                            )[-1],
                'unit' : lambda **kwargs: (
                                    enemy_no_rout := not 'cannot_rout' in kwargs['enemy_logs'],
                                    enemy_routed_units := all([unit['is_routed'] for unit in copy.deepcopy(kwargs['enemy_units'])]),
                                    enemy_shield := copy.deepcopy(kwargs['enemy_dice'])['Shield'],
                                    unit_ability := check_any_unit(kwargs['player_units'],unit_name_list=['Chaos Space Marines']),
                                    output := {}
                                    if not enemy_no_rout
                                    else rout_random_unit(copy.deepcopy(kwargs['enemy_units']), side = 'enemy')
                                    if unit_ability
                                       and (enemy_shield < 1 or random.random()>0.5 or enemy_routed_units) 
                                    else {'enemy_dice' : remove_dice(copy.deepcopy(kwargs['enemy_dice']), dice_set=['Shield'])}
                                    if unit_ability else {}
                                    )[-1]
            }
        },
        # Foul Worship
        4: {'name' : "Foul Worship",
            'card_icon' : {'Bolter': 0, 'Shield': 1, 'Morale': 0, 'card_type':'def'},
            'card_effect' : {
                'general' : lambda **kwargs: (
                                player_dice := copy.deepcopy(kwargs['player_dice']),
                                new_dice := game_utils.rollNdice_after(player_dice,1),
                                {'player_dice' : {
                                    k: player_dice.get(k, 0) + new_dice.get('new_dice',{}).get(k, 0)
                                    for k in set(player_dice)
                                    }
                                }
                )[-1],
                'unit' : lambda **kwargs: (
                                    enemy_routed_units := any([unit['is_routed'] for unit in copy.deepcopy(kwargs['enemy_units'])]),
                                    n_cultist := len([unit for unit in copy.deepcopy( kwargs['player_units']) if unit['unit_name']=='Cultists' and unit['is_routed'] == False]),
                                    choose_temp_tokens(n_cultist, [0,1])
                                    if check_any_unit(kwargs['player_units'],unit_name_list=['Cultists'])
                                       and enemy_routed_units
                                    else {}
                                    )[-1]
            }
        },
        # Mark of Tzeentch
        5: {'name' : "Mark of Tzeentch",
            'card_icon' : {'Bolter': 0, 'Shield': 0, 'Morale': 2, 'card_type':'both'},
            'card_effect' : {
                'general' : lambda **kwargs: (
                                            new_die := {'Morale': 1} if sum(copy.deepcopy(kwargs['player_dice']).values()) < 8 else {},
                                            updated_dice := {
                                                            k: kwargs['player_dice'].get(k, 0) + new_die.get(k, 0)
                                                            for k in set(kwargs['player_dice'])
                                                            },
                                            player_output := {'player_dice': updated_dice},
                                            new_unit := {
                                                'unit_name' : 'Chaos Space Marines', 
                                                'tier' : 1, 
                                                'unit_count' : 6, 
                                                'dice' : 0, 
                                                'hp' : 3, 
                                                'morale' : 2,
                                                'is_routed': False,
                                                'is_killed': False
                                            },
                                            player_units := {'player_units' : copy.deepcopy(kwargs['player_units'])},
                                            cultists_with_index := [
                                                (i, unit) 
                                                for i, unit in enumerate(player_units['player_units'])
                                                if unit['unit_name'] == 'Cultists'
                                            ],
                                            target_index := None if not cultists_with_index
                                                            else sorted(cultists_with_index, key=lambda x: -x[1]['is_routed'])[0][0],
                                            replace_unit :=
                                                player_units['player_units'].__setitem__(target_index, new_unit)
                                                if target_index is not None and updated_dice['Morale'] > kwargs['enemy_dice']['Morale']
                                                else None,
                                            final_output := {**player_output,**player_units} if updated_dice['Morale'] > copy.deepcopy(kwargs['enemy_dice'])['Morale'] else player_output
                                            )[-1],
                'unit' : lambda **kwargs: (
                                            nr_morale := min(2,copy.deepcopy(kwargs['player_dice'])['Morale']),
                                            nr_spend_on_bolter := random.choice(range(nr_morale+1)),
                                            new_die := {'new_dice':{'Bolter':nr_spend_on_bolter,
                                                         'Shield':nr_morale-nr_spend_on_bolter,
                                                         'Morale':-nr_morale}},
                                            {'player_dice' : {
                                                            k: kwargs['player_dice'].get(k, 0) + new_die.get('new_dice',{}).get(k, 0)
                                                            for k in set(kwargs['player_dice'])
                                                            }
                                            }
                                            if check_any_unit(kwargs['player_units'],unit_name_list=['Chaos Space Marines'])
                                            and nr_morale > 0
                                            else {}
                                    )[-1]
            }
        },
        # Mark of Slaanesh
        6 : {'name' : "Mark of Slaanesh",
            'card_icon' : {'Bolter': 1, 'Shield': 1, 'Morale': 0, 'card_type':'both'},
            'card_effect' : {
                'general' : lambda **kwargs: (
                                            enemy_no_rout := not 'cannot_rout' in kwargs['enemy_logs'],
                                            new_die := game_utils.rollNdice_after(copy.deepcopy(kwargs['player_dice']),1)['new_dice'],
                                            updated_dice := {
                                                            k: kwargs['player_dice'].get(k, 0) + new_die.get(k, 0)
                                                            for k in set(kwargs['player_dice'])
                                                            },
                                            player_output := {'player_dice': updated_dice},
                                            enemy_output := rout_random_unit(copy.deepcopy((kwargs['enemy_units'])), side = 'enemy')
                                            if player_output['player_dice']['Morale'] > kwargs['enemy_dice']['Morale'] and enemy_no_rout
                                            else {},
                                            final_output := {**player_output,**enemy_output}
                                            )[-1],
                'unit' : lambda **kwargs: (
                                        enemy_routed_units := any([unit['is_routed'] for unit in copy.deepcopy(kwargs['enemy_units'])]),
                                        free_cultist := {'unit_name': 'Cultists',
                                                        'tier': 0,
                                                        'dice': 0,
                                                        'hp': 2,
                                                        'morale': 2,
                                                        'is_routed': False,
                                                        'is_killed': False},
                                        player_output := {'player_units' : copy.deepcopy(kwargs['player_units']) + [free_cultist]}
                                        if check_any_unit(kwargs['player_units'],unit_name_list=['Chaos Space Marines']) and enemy_routed_units else {}
                                    )[-1]
            }
        },
        # Mark of Khrone
        7 : {'name' : "Mark of Khrone",
            'card_icon' : {'Bolter': 2, 'Shield': 0, 'Morale': 0, 'card_type':'att'},
            'card_effect' : {
                'general' : lambda **kwargs: (
                                            p_dice := copy.deepcopy(kwargs['player_dice']),
                                            n_bolter_or_morale := sum(p_dice.values()) - p_dice['Shield'],
                                            temp_bolters := choose_temp_tokens(3, [1,0]) if n_bolter_or_morale > 0 else {},
                                            player_dice := {'player_dice':remove_dice(p_dice, dice_set=['Bolter','Morale'])},
                                            final_output := {**player_dice,**temp_bolters} 
                                            if temp_bolters
                                            #if random.random() > 0.5 
                                            else {}
                                            )[-1],
                'unit' : lambda **kwargs: (
                                        enemy_shield := copy.deepcopy(kwargs['enemy_dice'])['Shield'],
                                        enemy_routed_units := any([unit['is_routed'] for unit in copy.deepcopy(kwargs['enemy_units'])]),
                                        unit_ability := check_any_unit(kwargs['player_units'],unit_name_list=['Chaos Space Marines']),
                                        enemy_output := destory_routed_unit(copy.deepcopy(kwargs['enemy_units']),side='enemy')
                                        if  unit_ability
                                            and enemy_routed_units 
                                            and (enemy_shield == 0 or random.random() > 0.5)
                                            else {'enemy_dice' : remove_dice(copy.deepcopy(kwargs['enemy_dice']), dice_set=['Shield'])}
                                            if unit_ability and enemy_routed_units else {}
                                    )[-1]
            }
        },
        # Mark of Nurgle
        8 : {'name' : "Mark of Nurgle",
            'card_icon' : {'Bolter': 0, 'Shield': 2, 'Morale': 0, 'card_type':'att'},
            'card_effect' : {
                'general' : lambda **kwargs: (
                                            p_dice := copy.deepcopy(kwargs['player_dice']),
                                            n_shield_or_morale := sum(p_dice.values()) - p_dice['Bolter'],
                                            temp_shields := choose_temp_tokens(3, [0,1]) if n_shield_or_morale > 0 else {},
                                            player_dice := {'player_dice':remove_dice(p_dice, dice_set=['Shield','Morale'])},
                                            final_output := {**player_dice,**temp_shields} 
                                            #if random.random() > 0.5 
                                            if temp_shields
                                            else {}
                                            )[-1],
                'unit' : lambda **kwargs: (
                                        temp_shields := choose_temp_tokens(2, [0,1]),
                                        enemy_routed_units := any([unit['is_routed'] for unit in copy.deepcopy(kwargs['enemy_units'])]),
                                        unit_ability := check_any_unit(kwargs['player_units'],unit_name_list=['Chaos Space Marines']),
                                        enemy_output := destory_routed_unit(copy.deepcopy(kwargs['enemy_units']),side='enemy')
                                        if unit_ability
                                            and enemy_routed_units 
                                            and random.random() > 0.5
                                            else temp_shields 
                                                if unit_ability
                                                else {}
                                    )[-1]
            }
        },
        # Chaos United
        9 : {'name' : "Chaos United",
            'card_icon' : {'Bolter': 1, 'Shield': 1, 'Morale': 1, 'card_type':'both'},
            'card_effect' : {
                'general' : lambda **kwargs: (
                                            enemy_routed_units := all([unit['is_routed'] for unit in copy.deepcopy(kwargs['enemy_units'])]),
                                            cur_player_dice := sum(copy.deepcopy(kwargs['player_dice']).values()),
                                            enemy_no_rout := 1 if not 'cannot_rout' in kwargs['enemy_logs'] else 0,
                                            new_dice_set := game_utils.rollNdice_after(copy.deepcopy(kwargs['player_dice']),enemy_no_rout),
                                            player_output := {'player_dice' : {
                                                k: kwargs['player_dice'].get(k, 0) +
                                                   new_dice_set.get('new_dice',{}).get(k, 0)
                                                for k in set(kwargs['player_dice'])
                                                }
                                            },
                                            final_output := player_output
                                            if (cur_player_dice == 8) or (enemy_routed_units) or (not enemy_routed_units and random.random() > 0.5) or enemy_no_rout == 0
                                            else rout_random_unit(copy.deepcopy(kwargs['enemy_units']), side = 'enemy')
                                            )[-1],
                'unit' : lambda **kwargs: (
                                        n_cultist := min(1,len([unit for unit in copy.deepcopy(kwargs['player_units']) if unit['unit_name']=='Cultists'])),
                                        free_unit_list := {
                                            0 : {
                                                'unit_name': 'Cultists',
                                                'tier': 0,
                                                'dice': 0,
                                                'hp': 2,
                                                'morale': 2,
                                                'is_routed': False,
                                                'is_killed': False
                                            },
                                            1 : {
                                                'unit_name' : 'Chaos Space Marines', 
                                                'tier' : 1,  
                                                'dice' : 0, 
                                                'hp' : 3, 
                                                'morale' : 2,
                                                'is_routed': False,
                                                'is_killed': False
                                            },
                                        },
                                        player_output := {'player_units' : copy.deepcopy(kwargs['player_units']) + [free_unit_list[n_cultist]]}
                                        if check_any_unit(kwargs['player_units'],unit_name_list=['Cultists','Chaos Space Marines','Helbrutes']) 
                                        else {}
                                    )[-1]
            }
        },
        # Daemonic Resilience
        10 : {'name' : "Daemonic Resilience",
            'card_icon' :{'Bolter': 0, 'Shield': 2, 'Morale': 1, 'card_type':'def'},
            'card_effect' : {
                'general' : lambda **kwargs: (
                                            player_choice := random.choice(['Shield','Morale']),
                                            new_dice_set := {'new_dice' : {player_choice: 1}} if sum(copy.deepcopy(kwargs['player_dice']).values()) < 8 else {},
                                            {'player_dice' : {
                                                k: kwargs['player_dice'].get(k, 0) +
                                                   new_dice_set.get('new_dice',{}).get(k, 0)
                                                for k in set(kwargs['player_dice'])
                                                }
                                            },
                                            )[-1],
                'unit' : lambda **kwargs: (
                                        temp_shields := choose_temp_tokens(4, [0,1]),
                                        unit_ability := check_any_unit(kwargs['player_units'],unit_name_list=['Helbrutes']),
                                        enemy_output := destroy_unit(copy.deepcopy(kwargs['enemy_units']),side='enemy')
                                        if unit_ability
                                            and random.random() > 0.5
                                            else temp_shields 
                                                if unit_ability
                                                else {}
                                    )[-1]
            }
        },
        # Inhuman Strenght
        11 : {'name' : "Inhuman Strenght",
            'card_icon' :{'Bolter': 2, 'Shield': 0, 'Morale': 1, 'card_type':'att'},
            'card_effect' : {
                'general' : lambda **kwargs: (
                                            player_choice := random.choice(['Bolter','Morale']),
                                            new_dice_set := {'new_dice' : {player_choice: 1}} if sum(copy.deepcopy(kwargs['player_dice']).values()) < 8 else {},
                                            {'player_dice' : {
                                                k: kwargs['player_dice'].get(k, 0) +
                                                   new_dice_set.get('new_dice',{}).get(k, 0)
                                                for k in set(kwargs['player_dice'])
                                                }
                                            },
                                            )[-1],
                'unit' : lambda **kwargs: (
                                            temp_shields := choose_temp_tokens(4, [1, 0]),
                                            player_output := destroy_unit(copy.deepcopy(kwargs['player_units']), side='player'),
                                            (
                                                temp_shields.update(player_output),
                                                temp_shields
                                            )[-1]
                                            if check_any_unit(kwargs['player_units'], unit_name_list=['Helbrutes'])
                                            #and random.random() > 0.5
                                            else {}
                                        )[-1]
            }
        },
        # Chaos Victorious 
        12 : {'name' : "Chaos Victorious ",
            'card_icon' :{'Bolter': 1, 'Shield': 1, 'Morale': 1, 'card_type':'both'},
            'card_effect' : {
                'general' : lambda **kwargs: (
                                            new_die := game_utils.rollNdice_after(copy.deepcopy(kwargs['player_dice']),2)['new_dice'],
                                            updated_dice := {
                                                            k: kwargs['player_dice'].get(k, 0) + new_die.get(k, 0)
                                                            for k in set(kwargs['player_dice'])
                                                            },
                                            n_enemy_0_tier_units := len([unit for unit in copy.deepcopy(kwargs['enemy_units']) if unit['tier']== 0]),
                                            enemy_rout_0_tier := rout_random_unit(copy.deepcopy(kwargs['enemy_units']),side='enemy',tier = 0, n = n_enemy_0_tier_units),
                                            final_output := {**{'player_dice' : updated_dice},**enemy_rout_0_tier}
                                            if updated_dice['Morale'] > copy.deepcopy(kwargs['enemy_dice'])['Morale'] and not 'cannot_rout' in kwargs['enemy_logs']
                                            else {'player_dice' : updated_dice}
                                            )[-1],
                'unit' : lambda **kwargs:  rout_random_unit(copy.deepcopy(kwargs['enemy_units']),side='enemy')
                                           if check_any_unit(kwargs['player_units'],unit_name_list=['Chaos Reaver Titans']) 
                                           and not 'cannot_rout' in kwargs['enemy_logs']
                                           else {}
            }
        },
        #Death and Despair
        13 : {'name' : "Death and Despair",
            'card_icon' :{'Bolter': 2, 'Shield': 0, 'Morale': 1, 'card_type':'att'},
            'card_effect' : {
                'general' : lambda **kwargs: (
                                            n_dice := min(2,8 - sum(copy.deepcopy(kwargs['player_dice']).values())),
                                            player_choice := random.choice(['Bolter','Morale']),
                                            new_die := {player_choice : n_dice},
                                            updated_dice := {
                                                            k: kwargs['player_dice'].get(k, 0) + new_die.get(k, 0)
                                                            for k in set(kwargs['player_dice'])
                                                            },
                                            n_enemy_0_tier_units := len([unit for unit in copy.deepcopy(kwargs['enemy_units']) if unit['tier']== 0]),
                                            n_morale := updated_dice['Morale'],
                                            n_spend_morale := min(n_morale,n_enemy_0_tier_units), #min(random.choice(range(n_morale+1)),n_enemy_0_tier_units),
                                            updated_dice.__setitem__('Morale', updated_dice['Morale'] - n_spend_morale),
                                            enemy_output := destroy_unit(copy.deepcopy(kwargs['enemy_units']),side='enemy', tier = 0, n = n_spend_morale),
                                            final_output := {**{'player_dice' : updated_dice},**enemy_output}
                                            )[-1],
                'unit' : lambda **kwargs: (
                                        n_player_morale := copy.deepcopy(kwargs['player_dice'])['Morale'],
                                        n_enemey_morale := copy.deepcopy(kwargs['enemy_dice'])['Morale'],
                                        final_output := destory_routed_unit(copy.deepcopy(kwargs['enemy_units']),side='enemy')
                                        if check_any_unit(kwargs['player_units'],unit_name_list=['Chaos Reaver Titans']) 
                                            and n_player_morale > n_enemey_morale
                                        else {}
                                    )[-1]
            }
        },
    }
}