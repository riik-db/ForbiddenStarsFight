import pandas as pd
import os
import pickle
from collections import Counter
import psycopg2
import io
import csv
from concurrent.futures import ProcessPoolExecutor,as_completed
from tqdm import tqdm
import numpy as np

# Get DB connection from environment variables (works with docker-compose)
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "mydb")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

"""
Unit composition by stage (relative distribution)

Stage | Swarm      | Core        | Core+       | Heavy       | Elite
--------------------------------------------------------------------
Early | 🔥 dominant | strong      | rare        | negligible  | negligible
Mid   | moderate   | 🔥 dominant | notable     | rare        | rare
Late  | minimal    | moderate    | 🔥 dominant | strong      | notable

Notes:
- Early battles are overwhelmingly Swarm + Core
- Mid stage shifts into Core / Core+ dominance
- Late stage is defined by Core+, Heavy, and Elite presence
"""

def push_to_postgres(rows, schema, table_name, conn):
    """
    Push a list of dicts to Postgres table via COPY (efficient)
    """
    if not rows:
        return
    
    # # Convert NaN / pandas <NA> to None
    # clean_rows = []
    # for r in rows:
    #     clean_r = {k: (None if pd.isna(v) else v) for k, v in r.items()}
    #     clean_rows.append(clean_r)

    # # Get columns from first row
    # columns = clean_rows[0].keys()

    columns = rows[0].keys()

    # Create CSV buffer in memory
    f = io.StringIO()
    writer = csv.DictWriter(f, fieldnames=columns)
    writer.writeheader()  # optional
    writer.writerows(rows)
    f.seek(0)

    cur = conn.cursor()

    try:
        # Use COPY FROM STDIN
        cur.copy_expert(
            sql=f'COPY "{table_name}" ({", ".join(columns)}) FROM STDIN WITH CSV HEADER',
            file=f
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise
    finally:
        cur.close()

def ensure_partition(conn, parent_table, partition_name, partition_condition):
    """
    Ensure a Postgres partition exists. If it does, truncate it.
    If not, create it.
    
    :param conn: psycopg2 connection
    :param parent_table: name of parent partitioned table
    :param partition_name: name of child partition table
    :param partition_condition: SQL condition for partition, e.g. "FOR VALUES IN ('early')"
    """
    cur = conn.cursor()
    try:
        # Check if partition table exists
        cur.execute("""
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = %s
            )
        """, (partition_name,))
        exists = cur.fetchone()[0]

        if exists:
            #(f"Partition {partition_name} exists, truncating...")
            cur.execute(f'TRUNCATE TABLE public."{partition_name}" CASCADE')
        else:
            #print(f"Partition {partition_name} does not exist, creating...")
            cur.execute(f'''
                CREATE TABLE public."{partition_name}" PARTITION OF public.{parent_table}
                {partition_condition}
            ''')
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise
    finally:
        cur.close()

tier_power = [1,2,3,5,7]

def unit_type_bucket(units):
    n_units = len(units)
    n_elite_units = len([unit for unit in units if unit['tier'] >= 2])
    elite_ratio = n_elite_units / n_units if n_units > 0 else 0
    power_score = sum([tier_power[0] if unit['dice'] == 0 else tier_power[unit['tier'] + 1] for unit in units])
    avg_power = power_score / n_units if n_units > 0 else 0

    if elite_ratio > 0.8:
        return '5.elite'
    elif elite_ratio > 0.5 and avg_power > 3.5:
        return '4.heavy'
    elif n_elite_units == 0 and avg_power < 2.5:
        return '1.swarm'
    elif elite_ratio > 0.2 and avg_power > 3:
        return '3.core+'
    return '2.core' 

def unit_size(units):
    n_units = len([unit['unit_name'] for unit in units if unit['dice']>0])
    #refin_units = '_w_refin' if len([unit['unit_name'] for unit in units if unit['dice']==0]) else ''
    if n_units > 3:
        return '3.large' #+ refin_units
    elif n_units > 2:
        return '2.medium' #+ refin_units
    return '1.small' #+ refin_units

def dice_class(d):
    bolter = d.get('Bolter', 0)
    # shield = d.get('Shield', 0)
    morale = d.get('Morale', 0)

    dmg = '1.Low' if bolter <= 2 else '2.Med' if bolter <= 4 else '3.High'
    m = 'M' if morale > 0 else 'NoM'

    return f'{dmg}_{m}'

def morale_class(att_morale, def_morale):
    diff = abs(att_morale - def_morale)
    if diff == 0:
        return f'2.Morale_0'
    if diff == 1:
        return f'3.Morale_1'
    if diff <= 3:
        return f'4.Morale_+3'
    return f'5.Morale_4+'

UNIT_RANK = {
    "1.swarm": 1,
    "2.core": 2,
    "3.core+": 3,
    "4.heavy": 4,
    "5.elite": 5,
}

SIZE_RULES = {
    "early": {
        "1.swarm": {"1.swarm", "2.core"},
        "2.core":  {"1.swarm", "2.core"},
        "3.core+": set(),          
        "4.heavy": set(),
        "5.elite": set(),
    },
    "mid": {
        "1.swarm": {"1.swarm", "2.core"},
        "2.core":  {"1.swarm","2.core", "3.core+"},
        "3.core+": {"2.core", "3.core+"},
        "4.heavy": set(),
        "5.elite": set(),
    },
    "late": {
        "1.swarm": set(),
        "2.core":  {"2.core", "3.core+","4.heavy"},
        "3.core+": {"2.core", "3.core+","4.heavy"},
        "4.heavy": {"2.core", "3.core+","4.heavy"},
        "5.elite": {"2.core", "3.core+","4.heavy"},
    },
}

def size_relation(stage, att_type, def_type):
    if att_type == def_type:
        return "2.Equal"

    allowed = SIZE_RULES.get(stage, {}).get(att_type, set())

    if def_type in allowed:
        # defender is a "valid counter" → treat as Equal-ish
        return "2.Equal"

    # fallback to numeric comparison
    if UNIT_RANK[att_type] > UNIT_RANK[def_type]:
        return "3.AttStronger"
    else:
        return "1.AttWeaker"
    
# Define allowed bins
eff_bins = np.array([-1, -0.5, 0, 0.5, 1])

def snap_efficiency(eff):
    # Find the nearest bin
    return float(eff_bins[np.abs(eff_bins - eff).argmin()])

SIZE_DEF = {
    1: '1.small',
    2: '1.small',
    3: '2.medium',
    4: '3.large',
    5: '3.large',
}

def size_bucket(n_units):
    return SIZE_DEF[n_units]

def compute_round_metrics(attacker_icons_new, attacker_icons_prev,
                          defender_icons_new, defender_icons_prev,
                          epsilon=1e-9):
    """
    Compute round-by-round metrics for a battle.

    attacker_icons_new, attacker_icons_prev,
    defender_icons_new, defender_icons_prev: list of dicts
        Each dict contains {'Bolter', 'Shield', 'Morale'} for prev and new state of each round.
    epsilon: small value to avoid division by zero.
    
    Returns a list of dicts with per-round metrics.
    """
    n_rounds = len(attacker_icons_new)
    rounds = []

    for r in range(n_rounds):

        AttackerDamageBefore = max(0,defender_icons_prev[r]['Bolter'] - attacker_icons_prev[r]['Shield'])
        AttackerDamageAfter = max(0,defender_icons_new[r]['Bolter'] - attacker_icons_new[r]['Shield'])
        ΔAttackerDamage = AttackerDamageAfter - AttackerDamageBefore
        
        DefenderDamageBefore = max(0,attacker_icons_prev[r]['Bolter'] - defender_icons_prev[r]['Shield'])
        DefenderDamageAfter = max(0,attacker_icons_new[r]['Bolter'] - defender_icons_new[r]['Shield'])
        ΔDefenderDamage  = DefenderDamageAfter - DefenderDamageBefore

        damage_swing  = ΔDefenderDamage - ΔAttackerDamage
        damage_eff    = damage_swing / (abs(ΔAttackerDamage) + abs(ΔDefenderDamage) + epsilon)

        ΔAttackerMorale = attacker_icons_new[r]['Morale'] - attacker_icons_prev[r]['Morale']
        ΔDefenderMorale  = defender_icons_new[r]['Morale'] - defender_icons_prev[r]['Morale']

        morale_swing  = ΔAttackerMorale - ΔDefenderMorale
        morale_eff    = morale_swing / (abs(ΔAttackerMorale) + abs(ΔDefenderMorale) + epsilon)

        rounds.append({
            'round': r+1,
            'DamageEfficiency': snap_efficiency(damage_eff),
            'MoraleEfficiency': snap_efficiency(morale_eff),
        })
    return rounds

def process_files_v2(file_paths):

    data1_rows = []

    for file_path in tqdm(file_paths, desc="Processing files"):
        
        with open(file_path, "rb") as f:
            sim_dict = pickle.load(f)

        for sim, s in sim_dict.items():

            round_metrics = compute_round_metrics(s['attacker']['icons_new_state'], s['attacker']['icons_prev_state'],
                                                  s['defender']['icons_new_state'], s['defender']['icons_prev_state'])

            n_rounds = 3 if s["end_state"].endswith("_morale") else int(s["end_state"][-1])

            round_cards_played = [
            {
                "round": r + 1,
                "attacker": s["attacker"]["played_cards"][r],
                "defender": s["defender"]["played_cards"][r],
                **round_metrics[r],
            }
            for r in range(n_rounds)
            ]

            att_size = len([unit['unit_name'] for unit in s['attacker']['units'] if unit['dice']>0])
            att_ref = True if len([unit['unit_name'] for unit in s['attacker']['units'] if unit['dice']==0]) > 0 else False
            def_size = len([unit['unit_name'] for unit in s['defender']['units'] if unit['dice']>0])
            def_ref = True if len([unit['unit_name'] for unit in s['defender']['units'] if unit['dice']==0]) > 0 else False

            att_unit_type = unit_type_bucket(s['attacker']['units'])
            def_unit_type = unit_type_bucket(s['defender']['units'])

            att_dice = dice_class(s['attacker']['rolled_dice'])
            def_dice = dice_class(s['defender']['rolled_dice'])

            # ---------- fights ----------
            data1_rows.append({
                "id": sim,
                "stage": s["state"],
                "is_space": int(s["is_space"]),

                "att_faction": s["attacker"]["faction"],
                "def_faction": s["defender"]["faction"],

                'att_unit_size_bucket': size_bucket(att_size),
                'def_unit_size_bucket': '2.Equal' 
                                        if att_size == def_size
                                        else '1.AttSmaller'
                                        if def_size > att_size  else '3.AttLarger',
                'reinf' : f"{int(att_ref)}-{int(def_ref)}",

                'att_unit_type_bucket' : att_unit_type,
                'size_relation': size_relation(s["state"],att_unit_type,def_unit_type),

                'att_dice_result' : att_dice,
                'def_dice_result' : def_dice,

                'round_cards_played': round_cards_played,
                'win_condition' : morale_class(s["attacker"]["end_morale"],s["defender"]["end_morale"])
                                  if 'morale' in s["end_state"] else '1.Destruction',
                "attacker_win": 1 if s["end_state"].startswith("player_") else 0
            })

    data1_rows_df = pd.DataFrame(data1_rows)

    agg_cols = [
            'is_space',
            'stage',

            'att_faction',
            'def_faction',

            'att_unit_size_bucket',
            'def_unit_size_bucket',
            'reinf',

            'att_unit_type_bucket',
            'size_relation',

            'att_dice_result',
            'def_dice_result',

            'win_condition'
        ]

    data1_agg = (
            data1_rows_df
            .groupby(agg_cols, as_index=False, dropna=False)
            .agg(
                n_battles=("attacker_win", "size"),
                attacker_wins=("attacker_win", "sum"),
            )
        )

    data1_rows_exp_df = data1_rows_df.explode("round_cards_played")

    data1_rows_exp_df["round_id"] = data1_rows_exp_df["round_cards_played"].str.get("round").astype("Int64") 
    data1_rows_exp_df["att_card_id"] = data1_rows_exp_df["round_cards_played"].str.get("attacker").astype("Int64") 
    data1_rows_exp_df["def_card_id"] = data1_rows_exp_df["round_cards_played"].str.get("defender").astype("Int64")
    data1_rows_exp_df["DamageEfficiency"] = data1_rows_exp_df["round_cards_played"].str.get("DamageEfficiency").astype("float")
    data1_rows_exp_df["MoraleEfficiency"] = data1_rows_exp_df["round_cards_played"].str.get("MoraleEfficiency").astype("float")

    card_agg_cols = [
            'is_space',
            'stage',

            'att_faction',
            'def_faction',

            'def_unit_size_bucket',
            'size_relation',

            'round_id',
            'att_card_id',
            'def_card_id',

            'DamageEfficiency',
            'MoraleEfficiency',
        ]

    data1_agg_cards = (
            data1_rows_exp_df
            .groupby(card_agg_cols, as_index=False, dropna=False)
            .agg(
                n_battles=("attacker_win", "size"),
                attacker_wins=("attacker_win", "sum"),
            )
        ) 
 
    return data1_agg,data1_agg_cards

def delete_old_rows(conn, parent_table, att_faction, def_faction, stage):
    """
    Ensure a Postgres partition exists. If it does, truncate it.
    If not, create it.
    
    :param conn: psycopg2 connection
    :param parent_table: name of parent partitioned table
    :param partition_name: name of child partition table
    :param partition_condition: SQL condition for partition, e.g. "FOR VALUES IN ('early')"
    """
    cur = conn.cursor()
    try:
        # Check if partition table exists
        cur.execute(f"""
            SELECT EXISTS (
                SELECT 1 
                FROM {parent_table} 
                WHERE att_faction = '{att_faction}' AND def_faction = '{def_faction}' and stage = '{stage}'
            )
        """)
        exists = cur.fetchone()[0]

        if exists:
            #(f"Partition {partition_name} exists, truncating...")
            print(f"Deleting old rows for att_faction={att_faction} and def_faction={def_faction}...")
            cur.execute(
                f'DELETE FROM public."{parent_table}" WHERE att_faction = %s AND def_faction = %s and stage = %s',
                (att_faction, def_faction, stage)
            )

            conn.commit()
    except Exception as e:
        conn.rollback()
        raise
    finally:
        cur.close()

def process_file_and_push_test_v2(file_path, conn, schema):

    file_paths = [os.path.join(file_path, f)
                  for f in os.listdir(file_path)
                  if f.endswith('.pkl')]

    data1_agg,data1_agg_cards = process_files_v2(file_paths)

    #truncate partions
    for data,table in zip([data1_agg,data1_agg_cards],
                    ["agg_fight_rounds_v3","agg_fight_cards_v3"]):

        if isinstance(data, pd.DataFrame):
            print("Converting DataFrame to dict...")
            data = data.to_dict(orient="records")

        #drop rows if needed
        att_faction, def_faction, stage = data[0]['att_faction'], data[0]['def_faction'], data[0]['stage']

        delete_old_rows(conn, table, att_faction, def_faction, stage)

        print(f"Pushing data to table {table}...")

        push_to_postgres(data, schema, table, conn)

def worker_test_v2(file_path, schema):
    # Each process must create its own DB connection
    conn = psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    process_file_and_push_test_v2(file_path, conn, schema)
    conn.close()

if __name__ == "__main__":
    worker_test_v2('sim_results','public')
