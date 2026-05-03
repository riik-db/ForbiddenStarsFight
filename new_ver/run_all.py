#outdated https://dbdiagram.io/d/6948fd2ffec0014ad6279f7d

import game_set_up as gsu 

from sim_run import run_simulations

from analyse_run_test import worker_test_v2

from tqdm import tqdm

states = ['early','mid','late']

# Run simulations for all combinations of states, attacker factions, and defender factions
factions = ['CSM','SM','Eldar','Orks']

# or have specfic combinations of factions to run
# att_faction = ['Necron']
# def_faction = ['CSM','SM','Eldar','Orks']


n_sim = 1000
n_sim_per_batch = 1000
n_workers = 10

sim_dir = 'sim_results'
schema = 'public'

for state in tqdm(states, desc="States"):

    #if specfic change to: factions -> att_faction
    for att_faction in tqdm(factions, desc=f"###### Running state {state}."):

        # if specfic change to: factions -> def_faction
        for def_faction in tqdm([f for f in factions if f != att_faction], desc=f"###### Running state = {state} and att={att_faction}"):
            print(f"###### Running simulation for state: {state}, Attacker: {att_faction}, Defender: {def_faction}")
            run_simulations(
                n=n_sim,
                simulations_per_batch=n_sim_per_batch,
                output_dir = sim_dir,
                workers=n_workers,
                attacker_faction = att_faction,
                defender_faction = def_faction,
                state = state,
                is_space = False
            )

            #analyse data
            print("Running analysis and pushing to DB...")
            worker_test_v2(
                file_path=sim_dir,
                schema=schema
            )