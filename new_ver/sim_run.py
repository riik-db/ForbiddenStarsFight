#libraies 

import game_set_up as gsu 

import utils as game_utils

import card_abilities as card_abi

import random

import copy

from collections import Counter

import os
import pickle
from concurrent.futures import ProcessPoolExecutor, as_completed
import argparse
import shutil

import math

from tqdm import tqdm

def with_fallback_updates(func):
    def wrapper(**kwargs):
        original = copy.deepcopy(kwargs)
        updates = func(**kwargs) or {}
        original.update(updates)
        return original
    return wrapper

def sumdicesets(dice_dict_array):

    target_dice = ['Bolter','Shield','Morale']

    filtered_dice_dict_array = [
        {key: value for key, value in dice_set.items() if key in target_dice}
        for dice_set in dice_dict_array
    ]

    sum_dice_sets = dict(sum(map(Counter, filtered_dice_dict_array), Counter()))

    return {key: sum_dice_sets.get(key, 0) for key in target_dice}

def preferred_tier(dmg):
    if dmg <= 2:
        return 0.5
    elif dmg <= 4:
        return 1.5
    return 2.5


def damage_weight(u, state, incoming_damage):
    """
    Returns a relative weight for selecting this unit as a damage target.
    Higher weight = more likely to be selected.

    Design principles:
    - Weights express intent, not exact probabilities
    - Early game prioritizes immediate combat impact
    - Mid/Late game prioritizes morale outcomes and damage efficiency
    - HP is used to soak or convert damage efficiently
    """

    # Base weight (all eligible units start equally likely)
    w = 1.0

    # In last resort, when all units are routed. We still need to have some priority list.
    if u['is_routed']:
        w *= 1 + u['hp'] * 0.3

    pt = preferred_tier(incoming_damage)
    tier_dist = abs(u['tier'] - pt)

    w *= math.exp(-tier_dist)

    # # Early game:
    # # hier tier units act as a shield for lower tier units.
    # if state == 'early':
    #     w *= 1 + u['tier'] * 0.3

    # else:
    #     if incoming_damage >= u['hp']:
    #         # When damage can kill:
    #         # Prefer units whose removal preserves morale advantage.
    #         # Low-morale units are less valuable to keep alive.
    #         w *= 1 + (4 - u['morale']) * 0.35
    #     else:
    #         # When damage cannot kill:
    #         # Prefer soaking damage on high-HP units to minimize
    #         # morale loss and preserve higher-value units
    #         w *= 1 + (5 - u['hp'] + incoming_damage) * 0.25

    return w

def select_damage_target(units, state, incoming_damage):
    # Build candidate indices (respect unrouted-first rule)
    alive_unrouted = [
        i for i, u in enumerate(units)
        if not u['is_killed'] and not u['is_routed']
    ]

    if alive_unrouted:
        candidates = alive_unrouted
    else:
        # Only routed units left
        candidates = [
            i for i, u in enumerate(units)
            if not u['is_killed']
        ]

    # 2. Compute weights only for candidates
    weights = [
        damage_weight(units[i], state, incoming_damage)
        for i in candidates
    ]

    # 3. Safety fallback
    if sum(weights) == 0:
        return random.choice(candidates)

    return random.choices(candidates, weights=weights, k=1)[0]

def take_damage(state,
                player_units,
                player_dice,player_icon,
                enemy_dice,enemy_icon,
                side_effects,additional_damage = False):
    player_shiled = copy.deepcopy(player_icon['Shield'])
    enemy_damage = copy.deepcopy(enemy_icon['Bolter'])
    unblocked_damage_before = enemy_damage - player_shiled

    player_units_after_damage = copy.deepcopy(player_units)

    i = 1 

    if additional_damage:
        i += 1

    damage_round = 0

    while damage_round < i:

        unblocked_damage = copy.deepcopy(unblocked_damage_before)

        while unblocked_damage > 0:

            if all([unit['is_killed'] for unit in player_units_after_damage]):
                break #player_units_after_damage,player_dice

            idx = select_damage_target(player_units_after_damage, state, unblocked_damage)
            target_unit = player_units_after_damage[idx]

            #SM: Show no fear
            if 'cannot_rout' in side_effects and unblocked_damage < target_unit['hp']:
                break

            target_unit['is_routed'] = True 

            if unblocked_damage >= target_unit['hp']:
                target_unit['is_killed'] = True

            #SM: Ambush
            if 'destroy_routed_or_spend_morale' in side_effects and not target_unit['is_killed']:
                if player_dice['Morale'] == 0 or random.random() > 0.5:
                    target_unit['is_killed'] = True
                else:
                    player_dice['Morale'] -= 1

            player_units_after_damage[idx] = target_unit

            unblocked_damage -= target_unit['hp']
            
        damage_round += 1

    player_units_after_damage_remove_killed = [unit for unit in player_units_after_damage if not unit['is_killed']]
    
    return player_units_after_damage_remove_killed,player_dice

#simulate battle first five cards
#adjust end results via logs


#Configuration

def generate_simulation(attacker_faction,defender_faction,state,is_space=False):

    attacker_units = game_utils.unit_selection(attacker_faction,
                                                random.choices(range(len(gsu.a_unit_prob)), gsu.a_unit_prob, k=1)[0] + 1,
                                                copy.deepcopy(gsu.rounds[state]['unit_prob']),
                                                copy.deepcopy(gsu.rounds[state]['unit_selection']))
    attacker_dice = game_utils.rollNdice(sum(unit['dice'] for unit in copy.deepcopy(attacker_units)))
    attacker_deck = game_utils.battle_cards(state,
                                            [4,3,2],
                                            copy.deepcopy(gsu.rounds[state]['combat_upgrades']['odds']),
                                            copy.deepcopy(gsu.rounds[state]['combat_upgrades']['upgrades']))
    
    defender_units = game_utils.unit_selection(defender_faction,
                                                len([unit['dice'] for unit in copy.deepcopy(attacker_units) if unit['dice'] > 0]) + random.choices([-1,0,1],[0.3,0.6,0.1],k=1)[0],
                                                copy.deepcopy(gsu.rounds[state]['unit_prob']),
                                                copy.deepcopy(gsu.rounds[state]['unit_selection']))
    defender_dice = game_utils.rollNdice(sum(unit['dice'] for unit in copy.deepcopy(defender_units)))
    defender_deck = game_utils.battle_cards(state,
                                            [4,3,2],
                                            copy.deepcopy(gsu.rounds[state]['combat_upgrades']['odds']),
                                            copy.deepcopy(gsu.rounds[state]['combat_upgrades']['upgrades']))
    
    battle_log = {}

    prev_attacker_units = copy.deepcopy(attacker_units)
    prev_attacker_dice = copy.deepcopy(attacker_dice)
    prev_attacker_deck = copy.deepcopy(attacker_deck) + ([],)
    prev_attacker_faceup = []
    attacker_continuous_effect = []
    prev_defender_units = copy.deepcopy(defender_units)
    prev_defender_dice = copy.deepcopy(defender_dice)
    prev_defender_deck = copy.deepcopy(defender_deck) + ([],)
    prev_defender_faceup = []
    defender_continuous_effect = []

    attacker_icons_prev = []
    attacker_icons_new = []
    attacker_icons_prev += [
        {
            **copy.deepcopy(attacker_dice),
            'Morale': copy.deepcopy(attacker_dice).get('Morale', 0) + sum(
                unit['morale'] for unit in copy.deepcopy(attacker_units) if not unit['is_routed']
            )
        }
    ]
    attacker_played_cards = []
    defender_icons_prev = []
    defender_icons_new = []
    defender_icons_prev += [
        {
            **copy.deepcopy(defender_dice),
            'Morale': copy.deepcopy(defender_dice).get('Morale', 0) + sum(
                unit['morale'] for unit in copy.deepcopy(defender_units) if not unit['is_routed']
            )
        }
    ]
    defender_played_cards = []

    end_state = ''


    for r in range(1,4):
        round_key = f'round_{r}'

        attacker_effects = []
        defender_effects = []

        attacker_copy_temp_token = {'Bolter':0,'Shield':0}
        defender_copy_temp_token = {'Bolter':0,'Shield':0}

        #attacker side
        attacker_card = copy.deepcopy(prev_attacker_deck[0][0])
        attacker_played_cards += [attacker_card]
        attacker_card_face_up_icons = copy.deepcopy(prev_attacker_faceup) + [card_abi.combat_cards[attacker_faction][attacker_card]['card_icon']]
        attacker_card_general_ability = with_fallback_updates(
                card_abi.combat_cards[attacker_faction][attacker_card]['card_effect']['general']
                )(
                    player_units = copy.deepcopy(prev_attacker_units),
                    player_dice = copy.deepcopy(prev_attacker_dice),
                    enemy_units = copy.deepcopy(prev_defender_units),
                    enemy_dice = copy.deepcopy(prev_defender_dice),
                    is_attacker = True,
                    enemy_logs = [],
                    round_id = r
                )

        attacker_card_unit_ability = with_fallback_updates(
                card_abi.combat_cards[attacker_faction][attacker_card]['card_effect']['unit']
                )(
                    **copy.deepcopy({key: value
                                     for key, value in attacker_card_general_ability.items()
                                     if key in ['player_units', 'player_dice', 'enemy_dice', 'enemy_units','is_attacker','enemy_logs','round_id']})
                )
        
        #Orks: Weirdboyz
        if attacker_faction == 'Orks' and 'copy_temp_tokens' in attacker_card_unit_ability.get('logs',{}).get('player',{}):
            attacker_continuous_effect.append('copy_temp_tokens')

        if defender_faction == 'Orks' and 'copy_temp_tokens' in defender_continuous_effect \
            and any([attacker_card_general_ability.get('temp_tokens',{}),
                    attacker_card_unit_ability.get('temp_tokens',{})
                    ]):
            defender_copy_temp_token = sumdicesets(
                                                [copy.deepcopy(attacker_card_general_ability.get('temp_tokens', {})),
                                                 copy.deepcopy(attacker_card_unit_ability.get('temp_tokens', {}))
                                                ])
        #SM: Break the line or Orks: Snapper Gargant
        if attacker_faction in ['SM', 'Orks', 'Eldar'] and \
           'lose_1_faceup_card' in attacker_card_unit_ability.get("logs", {}).get("enemy", {}) and \
           len(prev_defender_faceup) > 0:
            random_card_chosen = random.choice(range(len(prev_defender_faceup)))
            prev_defender_faceup.pop(random_card_chosen)
            prev_defender_deck[2].pop(random_card_chosen)

            # Removing on-going effect
            if defender_faction == 'Orks' and defender_continuous_effect and not 8 in prev_defender_deck[2]:
                defender_continuous_effect = []

        #Eldar: Psychic Lance
        if (attacker_faction == 'Eldar' 
            and 'lose_1_card_hand' in attacker_card_general_ability.get('logs',{}).get('enemy',{})
            and len(prev_defender_deck[0]) > 1 
         ) :
            prev_defender_deck = (
                prev_defender_deck[0][:1] + prev_defender_deck[0][2:],                      # Unplayed cards in hand
                prev_defender_deck[1],                                                      # Undrawn cards
                prev_defender_deck[2]                                                       # Played cards icons
            )

        #Eldar: Holofield Emitter
        if (attacker_faction == 'Eldar' 
            and 'add_combat_card' in attacker_card_general_ability.get('logs',{}).get('player',{})
            and len(prev_attacker_deck[1]) > 0
         ) :
            prev_attacker_deck = (
                prev_attacker_deck[0]+ [prev_attacker_deck[1][0]],                          # Unplayed cards in hand
                prev_attacker_deck[1][1:],                                                  # Undrawn cards
                prev_attacker_deck[2]                                                       # Played cards icons
            )

        #Eldar: Command of the Autarch & Holofield Emitter
        if (attacker_faction == 'Eldar' 
            and 'get_additional_temp_from_hand' in [attacker_card_general_ability.get('logs',{}).get('player',{}),
                                                    attacker_card_unit_ability.get('logs',{}).get('player',{})]
            and len(prev_attacker_deck[0]) > 1
         ) :
            next_card = prev_attacker_deck[0][1]
            attacker_card_face_up_icons.append(
                card_abi.combat_cards[attacker_faction][next_card]['card_icon']
            )

            prev_attacker_deck = (
                prev_attacker_deck[0][:1] + prev_attacker_deck[0][2:],                      # Unplayed cards in hand
                prev_attacker_deck[1],                                                      # Undrawn cards
                prev_attacker_deck[2] + [next_card]                                         # Played cards icons
            )

        #defender side
        defender_card = copy.deepcopy(prev_defender_deck[0][0])
        defender_played_cards += [defender_card]
        defender_card_face_up_icons = copy.deepcopy(prev_defender_faceup) + [card_abi.combat_cards[defender_faction][defender_card]['card_icon']]

        attacker_dice_after_card = sumdicesets([copy.deepcopy(attacker_card_unit_ability.get('player_dice', {})),
                                                copy.deepcopy(attacker_card_general_ability.get('new_dice',{})),
                                                copy.deepcopy(attacker_card_unit_ability.get('new_dice',{}))
                                                ]
                                              )

        defender_card_general_ability = with_fallback_updates(
                card_abi.combat_cards[defender_faction][defender_card]['card_effect']['general']
                )(
                    player_units = copy.deepcopy(attacker_card_unit_ability['enemy_units']),
                    player_dice = copy.deepcopy(attacker_card_unit_ability['enemy_dice']),
                    enemy_units = copy.deepcopy(attacker_card_unit_ability['player_units']),
                    enemy_dice = copy.deepcopy(attacker_dice_after_card),
                    is_attacker = False,
                    enemy_logs = [attacker_card_general_ability.get('logs',{}).get('player',{})] + [attacker_card_unit_ability.get('logs',{}).get('player',{})],
                    round_id = r
                )

        defender_card_unit_ability = with_fallback_updates(
                card_abi.combat_cards[defender_faction][defender_card]['card_effect']['unit']
                )(
                    **copy.deepcopy({key: value
                                    for key, value in defender_card_general_ability.items()
                                    if key in ['player_units', 'player_dice', 'enemy_dice', 'enemy_units','is_attacker','enemy_logs','round_id']})
                )
        
        #Orks: Weirdboyz
        if defender_faction == 'Orks' and 'copy_temp_tokens' in defender_card_unit_ability.get('logs',{}).get('player',{}):
            defender_continuous_effect.append('copy_temp_tokens')

        if attacker_faction == 'Orks' and 'copy_temp_tokens' in attacker_continuous_effect \
            and any([defender_card_general_ability.get('temp_tokens',{}),
                    defender_card_unit_ability.get('temp_tokens',{})
                    ]):
            attacker_copy_temp_token = sumdicesets(
                                                [copy.deepcopy(defender_card_general_ability.get('temp_tokens', {'Bolter':0,'Shield':0})),
                                                 copy.deepcopy(defender_card_unit_ability.get('temp_tokens', {'Bolter':0,'Shield':0}))
                                                ])
        #SM: Break the line or Orks: Snapper Gargant
        if defender_faction in ['SM', 'Orks', 'Eldar'] and \
           'lose_1_faceup_card' in defender_card_unit_ability.get("logs", {}).get("enemy", {}) and \
           len(attacker_card_face_up_icons) > 0:
            random_card_chosen = random.choice(range(len(attacker_card_face_up_icons)))
            attacker_card_face_up_icons.pop(random_card_chosen)
            if random_card_chosen + 1 <= len(prev_attacker_deck[2]):
                prev_attacker_deck[2].pop(random_card_chosen)
            else:
                #replacing card nr with None and removig it at the end of the round
                prev_attacker_deck[0][0] = None

            # Removing on-going effect
            if attacker_faction == 'Orks' and attacker_continuous_effect and \
                not 8 in prev_attacker_deck[2] + [attacker_card]:
                attacker_continuous_effect = [] 

        #Eldar: Holofield Emitter
        if (defender_faction == 'Eldar' 
            and 'add_combat_card' in defender_card_general_ability.get('logs',{}).get('player',{})
            and len(prev_defender_deck[1]) > 0
         ) :
            prev_defender_deck = (
                prev_defender_deck[0]+ [prev_defender_deck[1][0]],                          # Unplayed cards in hand
                prev_defender_deck[1][1:],                                                  # Undrawn cards
                prev_defender_deck[2]                                                       # Played cards icons
            )

        #Eldar: Psychic Lance
        if (defender_faction == 'Eldar' 
            and 'lose_1_card_hand' in defender_card_general_ability.get('logs',{}).get('enemy',{})
            and len(prev_attacker_deck[0]) > 1
         ) :
            prev_attacker_deck = (
                prev_attacker_deck[0][:1] + prev_attacker_deck[0][2:],                      # Unplayed cards in hand
                prev_attacker_deck[1],                                                      # Undrawn cards
                prev_attacker_deck[2]                                                       # Played cards icons
            )

        #Eldar: Command of the Autarch & Holofield Emitter
        if (defender_faction == 'Eldar' 
            and 'get_additional_temp_from_hand' in [defender_card_general_ability.get('logs',{}).get('player',{}),
                                                    defender_card_unit_ability.get('logs',{}).get('player',{})]
            and len(prev_defender_deck[0]) > 1
         ) :
            next_card = prev_defender_deck[0][1]
            defender_card_face_up_icons += [card_abi.combat_cards[defender_faction][next_card]['card_icon']]

            prev_defender_deck = (
                prev_defender_deck[0][:1] + prev_defender_deck[0][2:],                      # Unplayed cards in hand
                prev_defender_deck[1],                                                      # Undrawn cards
                prev_defender_deck[2] + [next_card]                                         # Played cards icons
            ) 
        
        defender_dice_after_card = sumdicesets([copy.deepcopy(defender_card_unit_ability.get('player_dice', {})),
                                                copy.deepcopy(defender_card_general_ability.get('new_dice',{})),
                                                copy.deepcopy(defender_card_unit_ability.get('new_dice',{}))
                                                ]
                                              )
        
        #summary
        for carry_over_effects,sides in zip([attacker_card_general_ability,
                                            attacker_card_unit_ability,
                                            defender_card_general_ability,
                                            defender_card_unit_ability],
                                            [['player','enemy'],
                                             ['player','enemy'],
                                             ['enemy','player'],
                                             ['enemy','player'],
                                             ]):
            attacker_effects.append(carry_over_effects.get('logs',{}).get(sides[0]))
            defender_effects.append(carry_over_effects.get('logs',{}).get(sides[1]))

        attacker_dice_end = copy.deepcopy(defender_card_unit_ability.get('enemy_dice'))
        attacker_temp_end = sumdicesets([
                                        copy.deepcopy(attacker_card_general_ability.get('temp_tokens',{})),
                                        copy.deepcopy(attacker_card_unit_ability.get('temp_tokens',{})),
                                        copy.deepcopy(attacker_copy_temp_token)
                                        ])
        #Eldar, Swooping Hawks
        if defender_faction == 'Eldar' and 'lose_3_temp_bolter' in attacker_effects:

            bolter_n = copy.deepcopy(attacker_temp_end['Bolter'])
            attacker_temp_end['Bolter'] = bolter_n - min(3,bolter_n)

        #Eldar, Fire Prism
        if defender_faction == 'Eldar' and 'lose_5_tmp_shield' in attacker_effects:

            shield_n = copy.deepcopy(attacker_temp_end['Shield'])
            attacker_temp_end['Shield'] = shield_n - min(5,shield_n)

        #SM: Fury of the Ultramar
        if defender_faction == 'SM' and 'lose_shield_dice_or_temp_2' in attacker_effects:
            if attacker_temp_end['Shield'] > 0 and random.random() > 0.5:
                new_min = max(0,attacker_temp_end['Shield'] - 2)
                attacker_temp_end['Shield'] = new_min
            elif  attacker_dice_end['Shield'] > 0:
                new_min = max(0,attacker_dice_end['Shield'] - 1)
                attacker_dice_end['Shield'] = new_min

        #Orks: Mek boyz
        if 'steal_top_card_icons' in attacker_effects:
            chosen_card = prev_defender_deck[1][0]
            prev_defender_deck = (prev_defender_deck[0], prev_defender_deck[1][1:],prev_defender_deck[2])

            additional_temp_icon = card_abi.combat_cards[defender_faction][chosen_card]['card_icon']
            attacker_temp_end = sumdicesets([
                                        attacker_temp_end,
                                        additional_temp_icon
                                        ])

        attacker_icon_sum = sumdicesets([copy.deepcopy(attacker_dice_end),
                                        attacker_temp_end] +
                                        copy.deepcopy(attacker_card_face_up_icons)
                                        )
             
        defender_dice_end = defender_dice_after_card
        defender_temp_end = sumdicesets([
                                        copy.deepcopy(defender_card_general_ability.get('temp_tokens',{})),
                                        copy.deepcopy(defender_card_unit_ability.get('temp_tokens',{})),
                                        copy.deepcopy(defender_copy_temp_token)
                                        ])
        #Eldar, Fire Dragon's Vengeance
        if attacker_faction == 'Eldar' and 'lose_all_temp_shield' in defender_effects:

            defender_temp_end['Shield'] = 0

        #SM: Fury of the Ultramar
        if attacker_faction == 'SM' \
            and 'lose_shield_dice_or_temp_2' in defender_effects:
            if defender_temp_end['Shield'] > 0 and random.random() > 0.5:
                new_min = max(0,defender_temp_end['Shield'] - 2)
                defender_temp_end['Shield'] = new_min
            elif  defender_dice_end['Shield'] > 0:
                new_min = max(0,defender_dice_end['Shield'] - 1)
                defender_dice_end['Shield'] = new_min

        #Orks: Mek boyz
        if 'steal_top_card_icons' in defender_effects:
            chosen_card = prev_attacker_deck[1][0]
            prev_attacker_deck = (prev_attacker_deck[0], prev_attacker_deck[1][1:],prev_attacker_deck[2])

            additional_temp_icon = card_abi.combat_cards[attacker_faction][chosen_card]['card_icon']
            defender_temp_end = sumdicesets([
                                        defender_temp_end,
                                        additional_temp_icon
                                        ])

        defender_icon_sum = sumdicesets([copy.deepcopy(defender_dice_end),
                                        defender_temp_end] +
                                        copy.deepcopy(defender_card_face_up_icons)
                                        )
        
        #Eldar: Spiritseer's guidance
        if not ('no_damage' in attacker_effects or 'no_damage' in defender_effects):
            attacker_units_after_damage,attacker_dice_end = take_damage(state,
                                                    copy.deepcopy(defender_card_unit_ability.get('enemy_units')),
                                                    attacker_dice_end,
                                                    attacker_icon_sum,
                                                    defender_dice_end,
                                                    defender_icon_sum,
                                                    attacker_effects,
                                                    #SM: Armoured advance
                                                    additional_damage = any('additional_damage' in sublist for sublist in [attacker_effects, defender_effects])
                                                    )
            defender_units_after_damage,defender_dice_end = take_damage(state, 
                                                    copy.deepcopy(defender_card_unit_ability.get('player_units')),
                                                    defender_dice_end,
                                                    defender_icon_sum,
                                                    attacker_dice_end,
                                                    attacker_icon_sum,
                                                    defender_effects,
                                                    #SM: Armoured advance
                                                    additional_damage = any('additional_damage' in sublist for sublist in [attacker_effects, defender_effects]))
        else:
            attacker_units_after_damage = [unit for unit in copy.deepcopy(defender_card_unit_ability.get('enemy_units')) if not unit['is_killed']]
            defender_units_after_damage = [unit for unit in copy.deepcopy(defender_card_unit_ability.get('player_units')) if not unit['is_killed']]
        
        
        battle_log[round_key] = {
            'attacker': {
                'units': copy.deepcopy(prev_attacker_units),
                'played_card': attacker_card,
                'faceup_cards_icon': attacker_card_face_up_icons,
                'card_general_ability': attacker_card_general_ability,
                'card_unit_ability': attacker_card_unit_ability,
                'combat_deck_end': (prev_attacker_deck[0][1:], #unplayed cards in hand
                                    prev_attacker_deck[1], #undrawn cards
                                    prev_attacker_deck[2] + ([] if prev_attacker_deck[0][0] is None else [prev_attacker_deck[0][0]]) #played cards
                                    )
            },
            'defender': {
                'units': copy.deepcopy(prev_defender_units),
                'played_card': defender_card,
                'faceup_cards_icon': defender_card_face_up_icons,
                'card_general_ability': defender_card_general_ability,
                'card_unit_ability': defender_card_unit_ability,
                'combat_deck_end': (prev_defender_deck[0][1:], #unplayed cards in hand
                                    prev_defender_deck[1], #undrawn cards
                                    prev_defender_deck[2] + ([] if prev_defender_deck[0][0] is None else [prev_defender_deck[0][0]]) #played cards
                                    )
            },
            'round_end': {
                'attacker' : {
                        'dice': copy.deepcopy(attacker_dice_end),
                        'temp': attacker_temp_end,
                        'icon': attacker_icon_sum,
                        'units': copy.deepcopy(attacker_units_after_damage),
                        'face_up_cards_icon': copy.deepcopy(attacker_card_face_up_icons)
                },
                'defender' : {
                        'dice': copy.deepcopy(defender_dice_end),
                        'temp': defender_temp_end,
                        'icon': defender_icon_sum,
                        'units': copy.deepcopy(defender_units_after_damage)
                }
            }
        }

        attacker_icons_prev += [
            {
                **copy.deepcopy(attacker_icon_sum),
                'Shield': copy.deepcopy(attacker_icon_sum).get('Shield', 0) - copy.deepcopy(attacker_temp_end).get('Shield', 0),
                'Bolter': copy.deepcopy(attacker_icon_sum).get('Bolter', 0) - copy.deepcopy(attacker_temp_end).get('Bolter', 0),
            }
        ]

        attacker_icons_new += [
            {
                **copy.deepcopy(attacker_icon_sum),
                'Morale': copy.deepcopy(attacker_icon_sum).get('Morale', 0) + sum(
                    unit['morale'] for unit in copy.deepcopy(attacker_units_after_damage) if not unit['is_routed']
                )
            }
        ]

        defender_icons_prev += [
            {
                **copy.deepcopy(defender_icon_sum),
                'Shield': copy.deepcopy(defender_icon_sum).get('Shield', 0) - copy.deepcopy(defender_temp_end).get('Shield', 0),
                'Bolter': copy.deepcopy(defender_icon_sum).get('Bolter', 0) - copy.deepcopy(defender_temp_end).get('Bolter', 0),
            }
        ]

        defender_icons_new += [
            {
                **copy.deepcopy(defender_icon_sum),
                'Morale': copy.deepcopy(defender_icon_sum).get('Morale', 0) + sum(
                    unit['morale'] for unit in copy.deepcopy(defender_units_after_damage) if not unit['is_routed']
                )
            }
        ]

        #check if combat is over
        if not attacker_units_after_damage or not defender_units_after_damage:

            if not attacker_units_after_damage and not defender_units_after_damage:
                end_state = f'tie_{r}'
                break
            elif not attacker_units_after_damage:
                end_state = f'enemy_round_{r}'
                break
            end_state = f'player_round_{r}'
            break

        if r == 3:

            player_morale = sum([unit['morale'] for unit in attacker_units_after_damage if unit['is_routed']==False]) + attacker_icon_sum['Morale']
            enemy_morale = sum([unit['morale'] for unit in defender_units_after_damage if unit['is_routed']==False]) + defender_icon_sum['Morale']

            if player_morale > enemy_morale:
                end_state = f'player_morale'
                break 

            end_state = f'enemy_morale'
            break

        #update units
        prev_attacker_units = copy.deepcopy(attacker_units_after_damage)
        prev_attacker_faceup = copy.deepcopy(attacker_card_face_up_icons)
        prev_attacker_dice = attacker_dice_end
        prev_attacker_deck = copy.deepcopy(battle_log[round_key]['attacker']['combat_deck_end'])


        prev_defender_units = copy.deepcopy(defender_units_after_damage)
        prev_defender_faceup = copy.deepcopy(defender_card_face_up_icons)
        prev_defender_dice = defender_dice_end
        prev_defender_deck = copy.deepcopy(battle_log[round_key]['defender']['combat_deck_end']) 

    return {
        'is_space' : is_space,
        'state' : state,
        'attacker': {
            'faction': attacker_faction,
            'units': attacker_units,
            'rolled_dice': attacker_dice,
            #'combat_deck': attacker_deck,
            'played_cards' : attacker_played_cards,
            'icons_prev_state' : attacker_icons_prev,
            'icons_new_state' : attacker_icons_new,
            'end_morale' : player_morale if 'morale' in end_state else None
        },
        'defender': {
            'faction' : defender_faction,
            'units': defender_units,
            'rolled_dice': defender_dice,
            #'combat_deck': defender_deck,
            'played_cards' : defender_played_cards,
            'icons_prev_state' : defender_icons_prev,
            'icons_new_state' : defender_icons_new,
            'end_morale' : enemy_morale if 'morale' in end_state else None
        },
        #'battle_log' : battle_log, #uncomment, if you want to see logs
        'end_state' : end_state
    }

def run_one_batch(i, simulations_per_batch, output_dir,attacker_faction,defender_faction,state, is_space):
    sim_dict = {(i * 1000 + j) : generate_simulation(attacker_faction,defender_faction,state, is_space) for j in range(simulations_per_batch)}
    file_path = os.path.join(output_dir, f"sim_batch_test_{i}.pkl")
    with open(file_path, 'wb') as f:
        pickle.dump(sim_dict, f)

def run_simulations(attacker_faction, defender_faction, state, is_space, n, simulations_per_batch, output_dir="sim_results", workers=1):
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = [
            executor.submit(run_one_batch, i, simulations_per_batch, output_dir, attacker_faction, defender_faction, state, is_space)
            for i in range(n)
        ]
        for _ in tqdm(as_completed(futures), total=len(futures), desc="Simulations"):
            pass

        # Optional: wait for completion + catch errors
        for future in as_completed(futures):
            future.result()   # raises exception if worker failed

if __name__ == "__main__":
    run_simulations(
        n=10,
        simulations_per_batch=100,
        output_dir = 'test',
        workers=20,
        attacker_faction = 'Eldar',
        defender_faction = 'Orks',
        state = 'late',
        is_space = False
    )