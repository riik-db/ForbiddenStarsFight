'''
Defining all game components
    - units
    - game rounds
    - combat cards
'''

all_units = [{'faction': 'Orks', 
'space_unit': False,
'unit_name' : 'Ork Boyz', 
'tier' :0, 
'unit_count' : 9, 
'dice' :2, 
'hp' : 2, 
'morale' : 1},
{'faction': 'Orks', 
'space_unit': False,
'unit_name' : 'Nobz', 
'tier' :1, 
'unit_count' : 6, 
'dice' :2, 
'hp' : 4, 
'morale' : 2},
{'faction': 'Orks', 
'space_unit': False,
'unit_name' : 'Battlewagons', 
'tier' :2, 
'unit_count' : 3, 
'dice' :3, 
'hp' : 5, 
'morale' : 2},
{'faction': 'Orks', 
'space_unit': False,
'unit_name' : 'Gargants', 
'tier' :3, 
'unit_count' : 3, 
'dice' :3, 
'hp' : 6, 
'morale' : 3},
{'faction': 'SM', 
'space_unit': False,
'unit_name' : 'Scouts', 
'tier' :0, 
'unit_count' : 6, 
'dice' :1, 
'hp' : 2, 
'morale' : 2},
{'faction': 'SM', 
'space_unit': False,
'unit_name' : 'Space Marines', 
'tier' :1, 
'unit_count' : 6, 
'dice' :2, 
'hp' : 3, 
'morale' : 3},
{'faction': 'SM', 
'space_unit': False,
'unit_name' : 'Land Raiders', 
'tier' :2, 
'unit_count' : 6, 
'dice' :3, 
'hp' : 4, 
'morale' : 3},
{'faction': 'SM', 
'space_unit': False,
'unit_name' : 'Warlord Titans', 
'tier' :3, 
'unit_count' : 3, 
'dice' :3, 
'hp' : 5, 
'morale' : 4},
{'faction': 'CSM', 
'space_unit': False,
'unit_name' : 'Cultists', 
'tier' :0, 
'unit_count' : 9, 
'dice' :1, 
'hp' : 2, 
'morale' : 2},
{'faction': 'CSM', 
'space_unit': False,
'unit_name' : 'Chaos Space Marines', 
'tier' :1, 
'unit_count' : 6, 
'dice' :3, 
'hp' : 3, 
'morale' : 2},
{'faction': 'CSM', 
'space_unit': False,
'unit_name' : 'Helbrutes', 
'tier' :2, 
'unit_count' : 3, 
'dice' :3, 
'hp' : 4, 
'morale' : 3},
{'faction': 'CSM', 
'space_unit': False,
'unit_name' : 'Chaos Reaver Titans', 
'tier' :3, 
'unit_count' : 3, 
'dice' :4, 
'hp' : 5, 
'morale' : 3},
{'faction': 'Eldar', 
'space_unit': False,
'unit_name' : 'Aspect Warriors', 
'tier' :0, 
'unit_count' : 6, 
'dice' :2, 
'hp' : 1, 
'morale' : 2},
{'faction': 'Eldar', 
'space_unit': False,
'unit_name' : 'Wraithguard', 
'tier' :1, 
'unit_count' : 3, 
'dice' :2, 
'hp' : 4, 
'morale' : 2},
{'faction': 'Eldar', 
'space_unit': False,
'unit_name' : 'Falcons', 
'tier' :2, 
'unit_count' : 3, 
'dice' :3, 
'hp' : 4, 
'morale' : 3},
{'faction': 'Eldar', 
'space_unit': False,
'unit_name' : 'Warlock Titans', 
'tier' :3, 
'unit_count' : 3, 
'dice' :4, 
'hp' : 5, 
'morale' : 3},
{'faction': 'Necron', 
'space_unit': False,
'unit_name' : 'warriors', 
'tier' :0, 
'unit_count' : 4, 
'dice' :2, 
'hp' : 3, 
'morale' : 0},
{'faction': 'Necron', 
'space_unit': False,
'unit_name' : 'immortals', 
'tier' :1, 
'unit_count' : 3, 
'dice' :3, 
'hp' : 4, 
'morale' : 1},
{'faction': 'Necron', 
'space_unit': False,
'unit_name' : 'monoliths', 
'tier' :2, 
'unit_count' : 2, 
'dice' :3, 
'hp' : 5, 
'morale' : 2},
{'faction': 'Necron', 
'space_unit': False,
'unit_name' : 'ctan', 
'tier' :3, 
'unit_count' : 1, 
'dice' :3, 
'hp' : 6, 
'morale' : 3},
{'faction': 'Tyranid', 
'space_unit': False,
'unit_name' : 'gaunts', 
'tier' :0, 
'unit_count' : 6, 
'dice' :1, 
'hp' : 1, 
'morale' : 3},
{'faction': 'Tyranid', 
'space_unit': False,
'unit_name' : 'warriors', 
'tier' :1, 
'unit_count' : 6, 
'dice' :3, 
'hp' : 2, 
'morale' : 3},
{'faction': 'Tyranid', 
'space_unit': False,
'unit_name' : 'carnifexes', 
'tier' :2, 
'unit_count' : 3, 
'dice' :4, 
'hp' : 3, 
'morale' : 3},
{'faction': 'Tyranid', 
'space_unit': False,
'unit_name' : 'bio titans', 
'tier' :3, 
'unit_count' : 3, 
'dice' :5, 
'hp' : 4, 
'morale' : 3},
{'faction': 'Sisters', # outdated
'space_unit': False,
'unit_name' : 'guardsmen', 
'tier' :0, 
'unit_count' : 12, 
'dice' :1, 
'hp' : 1, 
'morale' : 2},
{'faction': 'Sisters', 
'space_unit': False,
'unit_name' : 'ogryns', 
'tier' :1, 
'unit_count' : 6, 
'dice' :2, 
'hp' : 4, 
'morale' : 2},
{'faction': 'Sisters', 
'space_unit': False,
'unit_name' : 'leman russ tanks', 
'tier' :2, 
'unit_count' : 6, 
'dice' :3, 
'hp' : 4, 
'morale' : 3},
{'faction': 'Sisters', 
'space_unit': False,
'unit_name' : 'warhound titans', 
'tier' :3, 
'unit_count' : 3, 
'dice' :3, 
'hp' : 5, 
'morale' : 3},
{'faction': 'Tau', 
'space_unit': False,
'unit_name' : 'fire warriors', 
'tier' :0, 
'unit_count' : 6, 
'dice' :2, 
'hp' : 1, 
'morale' : 2},
{'faction': 'Tau', 
'space_unit': False,
'unit_name' : 'battle suits', 
'tier' :1, 
'unit_count' : 6, 
'dice' :3, 
'hp' : 3, 
'morale' : 2},
{'faction': 'Tau', 
'space_unit': False,
'unit_name' : 'custodians', 
'tier' :2, 
'unit_count' : 2, 
'dice' :4, 
'hp' : 4, 
'morale' : 2},
{'faction': 'Tau', 
'space_unit': False,
'unit_name' : 'supremacy titans', 
'tier' :3, 
'unit_count' : 3, 
'dice' :4, 
'hp' : 5, 
'morale' : 4},
]

'''
### Realistic Assumptions for Rounds  ###
-   early game (1-3 rounds):
    -   total 26material
        - round1: 6material
        - round2: 8material + 1cahce
        - round3: 8material + 1cahce
    -   2-3 units (8material)
    -   max 1 tier2 unit (4material) 
    -   3 tier0 combat cards (6material) 
    -   2 city + 1 bastion (8material)
-   mid game (4-6 rounds):
    -   have 2 tier0 combat cards at the start
    -   total 30material (8material + 1cahce per round)
    -   1-2 tier2 combat cards (4-8material)
    -   1 city + 1-2 bastion + 0-1 factory (5-9material)
    -   shift unit distribution more towards tier2 (13-21material)
-   late game (7-8 rounds):
    -   have 2 tier0 and 2 tier1 combat cards at the start
    -   total 20material (8material + 1cahce per round)
    -   1-2 tier3 card (6-12material)
    -   allow 1 tier3 unit (5material)

Definitions:
    - unit_selection    |   restricting tier unit amount
    - unit_prob         |   probability of choosing given tier unit.
    - unit_prob_more    |   if attacker size > defender size
    - combat_upgrades
        - beginning     |   pre, how many combat card upgrades
    - take
        - upgrades      |   how many combat card upgrades allowing
        - odds          |   odds of taking N combat card upgrades

Below are generic odds, which can be overwritten for specific faction, if needed. E.g Necron units participating in battle
'''
rounds = {
    'early':{
        'rounds':'1-3',
        'unit_selection':[None,None,1,0],
        'unit_prob':[0.7,0.25,0.05,0],
        'unit_prob_more':[0.75,0.25,0.05,0],
        'combat_upgrades':{
            #'upgrades':[0,0,0],
            #'odds':[[0],[0],[0]]
            'upgrades':[3,0,0],
            'odds':[[0.3,0.5,0.2],[0],[0]]
        }
    },
    'mid':{
        'rounds':'4-6',
        'unit_selection':[None,None,2,0],
        'unit_prob':[0.4,0.4,0.2,0],
        'unit_prob_more':[0.3,0.5,0.2,0],
        'combat_upgrades':{
            'upgrades':[2,2,0],
            'odds':[[0,1],[0.5,0.5],[0]]
        }
    },
    'late':{
        'rounds':'7-8',
        'unit_selection':[2,None,2,1],
        'unit_prob':[0.1,0.35,0.45,0.1],
        'unit_prob_more':[0.1,0.3,0.4,0.2],
        'combat_upgrades':{
            'upgrades':[1,2,2],
            'odds':[[1],[0,1],[0.8,0.2]]
        }
    }
}

#we want to target more realistic battles, where the area is important to both side, thus the balance of power is equal
a_unit_prob = [0.1,0.2,0.4,0.2,0.1] #probability of having N units in battle


'''
Combat cards per faction

    - card_type     |   when interpreting playstyle, then this helps
'''
combat_cards = {
        'SM': {
            'start':{
                # Reconnaissance
                0: {'Bolter': 0, 'Shield': 1, 'Morale': 0, 'card_type':'both'},
                # Faith in the Emperor
                1: {'Bolter': 0, 'Shield': 0, 'Morale': 1, 'card_type':'def'},
                # Ambush
                2: {'Bolter': 1, 'Shield': 0, 'Morale': 0, 'card_type':'att'},
                # Fury of the Ultramar
                3: {'Bolter': 1, 'Shield': 0, 'Morale': 0, 'card_type':'att'},
                # Blessed Power armour
                4: {'Bolter': 0, 'Shield': 1, 'Morale': 0, 'card_type':'def'},
            },
            'tier_0':{
                # Hold the line
                5: {'Bolter': 0, 'Shield': 1, 'Morale': 1, 'card_type':'def'},
                # Glory and death
                6: {'Bolter': 1, 'Shield': 0, 'Morale': 1, 'card_type':'att'},
                # Veteran scouts
                7: {'Bolter': 1, 'Shield': 1, 'Morale': 1, 'card_type':'both'},
                # Drop Pod assault
                8: {'Bolter': 1, 'Shield': 1, 'Morale': 0, 'card_type':'both'},
            },
            'tier_2':{
                # Show no fear
                9: {'tier': 2, 'Bolter': 0, 'Shield': 2, 'Morale': 1, 'card_type':'def'},
                # Break the line
                10: {'tier': 2, 'Bolter': 1, 'Shield': 2, 'Morale': 0, 'card_type':'both'},
                # Armoured advance
                11: {'tier': 2, 'Bolter': 2, 'Shield': 1, 'Morale': 0, 'card_type':'att'},
            },
            'tier_3':{
                # Emperor's glory
                12: {'Bolter': 0, 'Shield': 2, 'Morale': 2, 'card_type':'def'},
                # Emperor's might
                13: {'Bolter': 3, 'Shield': 0, 'Morale': 0, 'card_type':'att'}
            }
        },
        'Orks': {
            'start':{
                # Slugga Boyz
                0: {'Bolter': 1, 'Shield': 1, 'Morale': 0, 'card_type':'att'},
                # Shoota Boyz
                1: {'Bolter': 2, 'Shield': 0, 'Morale': 0, 'card_type':'att'},
                # 'Ard Boyz
                2: {'Bolter': 0, 'Shield': 2, 'Morale': 0, 'card_type':'def'},
                # Gretchin
                3: {'Bolter': 0, 'Shield': 0, 'Morale': 0, 'card_type':'both'},
                # Mek Boyz
                4: {'Bolter': 0, 'Shield': 0, 'Morale': 1, 'card_type':'def'},
            },
            'tier_0':{
                # Biker Nobz
                5: {'Bolter': 2, 'Shield': 1, 'Morale': 0, 'card_type':'att'},
                # Sea of green
                6: {'Bolter': 1, 'Shield': 1, 'Morale': 0, 'card_type':'both'},
                # Waaagh!!!!
                7: {'Bolter': 0, 'Shield': 0, 'Morale': 3, 'card_type':'both'},
                # Mega Nobz
                8: {'Bolter': 1, 'Shield': 2, 'Morale': 0, 'card_type':'def'},
            },
            'tier_2':{
                # Rokkit wagon
                9: {'Bolter': 3, 'Shield': 0, 'Morale': 0, 'card_type':'att'},
                # Weirdboyz
                10: {'Bolter': 1, 'Shield': 1, 'Morale': 1, 'card_type':'both'},
                # Party wagon
                11: {'Bolter': 1, 'Shield': 2, 'Morale': 0, 'card_type':'def'},
            },
            'tier_3':{
                # Snapper Gargant
                12: {'Bolter': 4, 'Shield': 1, 'Morale': 0, 'card_type':'att'},
                # Smasher Gargant
                13: {'Bolter': 2, 'Shield': 3, 'Morale': 0, 'card_type':'def'}
            }
        },
        'Eldar': {
            'start':{
                # Command of the Autarch
                0: {'Bolter': 0, 'Shield': 0, 'Morale': 0, 'card_type':'both'},
                # Hit and run
                1: {'Bolter': 1, 'Shield': 0, 'Morale': 0, 'card_type':'att'},
                # Ranger support
                2: {'Bolter': 0, 'Shield': 1, 'Morale': 1, 'card_type':'both'},
                # Howling Banshees
                3: {'Bolter': 1, 'Shield': 0, 'Morale': 0, 'card_type':'att'},
                # Striking Scorpions
                4: {'Bolter': 0, 'Shield': 1, 'Morale': 0, 'card_type':'def'},
            },
            'tier_0':{
                # Swooping Hawks
                5: {'Bolter': 0, 'Shield': 2, 'Morale': 0, 'card_type':'def'},
                # Wraithguard advance
                6: {'Bolter': 1, 'Shield': 0, 'Morale': 1, 'card_type':'both'},
                # Fire Dragon's vengeance
                7: {'Bolter': 2, 'Shield': 0, 'Morale': 0, 'card_type':'att'},
                # Wraithguard support
                8: {'Bolter': 0, 'Shield': 1, 'Morale': 1, 'card_type':'both'},
            },
            'tier_2':{
                # Wave Serpent
                9: {'Bolter': 1, 'Shield': 2, 'Morale': 0, 'card_type':'def'},
                # Spiritseer's guidance
                10: {'Bolter': 1, 'Shield': 1, 'Morale': 1, 'card_type':'both'},
                # Fire Prism
                11: {'Bolter': 2, 'Shield': 1, 'Morale': 0, 'card_type':'att'},
            },
            'tier_3':{
                # Holofield emitter
                12: {'Bolter': 1, 'Shield': 2, 'Morale': 1, 'card_type':'def'},
                # Psychic lance
                13: {'Bolter': 2, 'Shield': 1, 'Morale': 0, 'card_type':'att'}
            }
        },
        'CSM': {
            'start':{
                # Lure of Chaos
                0: {'Bolter': 0, 'Shield': 0, 'Morale': 1, 'card_type':'both'},
                # Dark Faith
                1: {'Bolter': 0, 'Shield': 0, 'Morale': 1, 'card_type':'both'},
                # Impure Zeal
                2: {'Bolter': 1, 'Shield': 1, 'Morale': 0, 'card_type':'both'},
                # Khorne's Rage
                3: {'Bolter': 1, 'Shield': 0, 'Morale': 0, 'card_type':'att'},
                # Foul Worship
                4: {'Bolter': 0, 'Shield': 1, 'Morale': 0, 'card_type':'def'},
            },
            'tier_0':{
                # Mark of Tzeentch
                5: {'Bolter': 0, 'Shield': 0, 'Morale': 2, 'card_type':'both'},
                # Mark of Slaanesh
                6: {'Bolter': 1, 'Shield': 1, 'Morale': 0, 'card_type':'both'},
                # Mark of Khrone
                7: {'Bolter': 2, 'Shield': 0, 'Morale': 0, 'card_type':'att'},
                # Mark of Nurgle
                8: {'Bolter': 0, 'Shield': 2, 'Morale': 0, 'card_type':'def'},
            },
            'tier_2':{
                # Chaos United
                9: {'Bolter': 1, 'Shield': 1, 'Morale': 1, 'card_type':'both'},
                # Daemonic Resilience
                10: {'Bolter': 0, 'Shield': 2, 'Morale': 1, 'card_type':'def'},
                # Inhuman Strenght
                11: {'Bolter': 2, 'Shield': 0, 'Morale': 1, 'card_type':'att'},
            },
            'tier_3':{
                # Death and Despair
                12: {'Bolter': 2, 'Shield': 0, 'Morale': 1, 'card_type':'att'},
                # Chaos Victorious
                13: {'Bolter': 1, 'Shield': 1, 'Morale': 1, 'card_type':'both'},
            }
        },
        'Sisters': { # outdated
            'start':{
                # Sanctified Charge
                0: {'Bolter': 0, 'Shield': 0, 'Morale': 0, 'card_type':'both'},
                # Holy Trinity
                1: {'Bolter': 0, 'Shield': 0, 'Morale': 0, 'card_type':'both'},
                # Guided Retribution
                2: {'Bolter': 0, 'Shield': 0, 'Morale': 0, 'card_type':'both'},
                # Beacon of Faith
                3: {'Bolter': 0, 'Shield': 0, 'Morale': 1, 'card_type':'att'},
                # Driven Onwards
                4: {'Bolter': 0, 'Shield': 2, 'Morale': 0, 'card_type':'def'},
            },
            'tier_0':{
                # Zealots Passion
                5: {'Bolter': 1, 'Shield': 1, 'Morale': 0, 'card_type':'both'},
                # Martyrdom
                6: {'Bolter': 0, 'Shield': 1, 'Morale': 1, 'card_type':'both'},
                # Spiritual Fortitude
                7: {'Bolter': 0, 'Shield': 1, 'Morale': 0, 'card_type':'att'},
                # Litany of Preservation
                8: {'Bolter': 2, 'Shield': 0, 'Morale': 0, 'card_type':'def'},
            },
            'tier_2':{
                # Furious Recital
                9: {'Bolter': 1, 'Shield': 2, 'Morale': 0, 'card_type':'both'},
                # Martyr's Immolation
                10: {'Bolter': 2, 'Shield': 0, 'Morale': 1, 'card_type':'def'},
                # Devastating Refrain
                11: {'Bolter': 1, 'Shield': 1, 'Morale': 1, 'card_type':'att'},
            },
            'tier_3':{
                # Divine Smiting
                12: {'Bolter': 0, 'Shield': 1, 'Morale': 2, 'card_type':'both'},
                # Divine Blessing
                13: {'Bolter': 1, 'Shield': 1, 'Morale': 2, 'card_type':'att'}
            }
        }
    }

