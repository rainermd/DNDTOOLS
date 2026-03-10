import random
import numpy as np

CRIT = 20
DEATH_SAVE_DC = 10
AUTOHIT = True
RANDOM_TARGET = False
ATTACKMODE = "dice"
FINISH = False
AUTOSUCC = True

def roll_dice(n, d):
    return sum(random.randint(1,d) for _ in range(n))

def adv(ad):
    roll1 = random.randint(1,20)
    roll2 = random.randint(1,20)

    if ad == 1:
        return max(roll1, roll2)

    if ad == 2:
        return min(roll1, roll2)

    return roll1

def skill_check(mod, ad, dc, autosuccess=AUTOSUCC):

    p = (21 - (dc - mod)) / 20

    if autosuccess:
        p = min(max(p, 1/20), 19/20)
    else:
        p = min(max(p, 0), 1)

    if ad == 1:           # advantage
        return 1 - (1 - p)**2

    if ad == 2:           # disadvantage
        return p**2

    return p              # normal roll
    
class Creature:

    def __init__(self, hp, ac, attack_bonus, n, dice, mod, attacks, init, is_player=False):
        self.max_hp = hp
        self.hp = hp
        self.ac = ac
        self.attack_bonus = attack_bonus
        self.n = n
        self.dice = dice
        self.mod = mod
        self.attacks = attacks
        self.is_player = is_player
        self.init = init

        self.death_saves_success = 0
        self.death_saves_fail = 0
        self.dead = False
        self.stable = False

    def alive(self):
        return self.hp > 0 and not self.dead

def roll_damage(n, dice, mod, mode, crit):

    if mode == "average":
        if crit:
            return max(0,2*int(n*(dice+1)/2 + mod))
        return max(0,int(n*(dice+1)/2 + mod))
    if crit:
        return max(0, roll_dice(2*n,dice) + mod)
    return max(0, roll_dice(n,dice) + mod)


def attack_roll(attacker, defender, autohit=AUTOHIT):
    if defender.hp<=0:
        defender.death_saves_fail += 2
        return False, False
    roll = random.randint(1,20)

    if roll == 1:
        return False, False

    crit = (roll == CRIT)
    hit = roll + attacker.attack_bonus >= defender.ac
    if crit:
        if autohit:
            return True, True
        return hit, True
    return hit, False

def roll_initiative(creatures):

    order = []

    for c in creatures:

        roll = random.randint(1,20)
        total = roll + c.init

        order.append((total, c.init, random.random(), c))

    order.sort(reverse=True)

    return [c for _,_,_,c in order]
    
def perform_attacks(attacker, enemies, random_target=RANDOM_TARGET, finish=FINISH):

    for _ in range(attacker.attacks):
        if finish:
            living = [e for e in enemies if not e.dead]
        else:
            living = [e for e in enemies if e.alive()]
        if not living:
            return
        if random_target:
            target = random.choice(living)
        else:
            target = min(living, key=lambda e: e.hp)

        
        hit, crit = attack_roll(attacker, target)

        if hit:

            dmg = roll_damage(attacker.n, attacker.dice, attacker.mod, ATTACKMODE, crit)

            target.hp -= dmg


def death_save(creature):

    roll = random.randint(1,20)

    if roll == 1:
        creature.death_saves_fail += 2

    elif roll == 20:
        creature.hp = 1
        creature.death_saves_fail = 0
        creature.death_saves_success = 0
        return

    elif roll >= DEATH_SAVE_DC:
        creature.death_saves_success += 1

    else:
        creature.death_saves_fail += 1

    if creature.death_saves_success >= 3:
        creature.stable = True

    if creature.death_saves_fail >= 3:
        creature.dead = True


def simulate_combat(party, monsters, max_rounds=1000):

    combatants = party + monsters

    initiative = roll_initiative(combatants)

    rounds = 0

    while rounds < max_rounds:

        rounds += 1

        for creature in initiative:

            if creature.dead:
                continue

            if creature.stable:
                continue

            if creature.hp <= 0 and creature.is_player:
                death_save(creature)
                continue

            if not creature.alive():
                continue

            enemies = monsters if creature.is_player else party

            perform_attacks(creature, enemies)

        party_alive = any(p.alive() for p in party)
        monsters_alive = any(m.alive() for m in monsters)

        if not party_alive or not monsters_alive:
            break

    party_win = not any(m.alive() for m in monsters)
    tpk = all((not p.alive()) for p in party)
    if tpk:
        deaths = sum((not p.alive()) for p in party)
    else:
        deaths = sum(p.dead for p in party)

    return party_win, tpk, deaths, rounds

def run_simulations(party_template, monster_template, N=10000):

    wins = 0
    tpks = 0
    total_rounds = []
    player_deaths = []

    for _ in range(N):

        party = [Creature(**p) for p in party_template]
        monsters = [Creature(**m) for m in monster_template]

        win, tpk, deaths, r = simulate_combat(party, monsters)

        total_rounds.append(r)
        player_deaths.append(deaths)

        if win:
            wins += 1

        if tpk:
            tpks += 1

    return {

        "party_win_probability": wins/N,
        "tpk_probability": tpks/N,
        "avg_rounds": np.mean(total_rounds),
        "avg_player_deaths": np.mean(player_deaths),
        "any_death" : sum(d > 0 for d in player_deaths)/N
    }

def classify_difficulty(win_prob):

    if win_prob > 0.9:
        return "Easy"

    if win_prob > 0.7:
        return "Medium"

    if win_prob > 0.4:
        return "Hard"

    return "Deadly"

party_template = [

    {"hp":38,"ac":16,"attack_bonus":7,"n":1,"dice":8,"mod":3,"attacks":2,"init":2,"is_player":True},
    {"hp":38,"ac":16,"attack_bonus":7,"n":1,"dice":8,"mod":3,"attacks":2,"init":2,"is_player":True},
    {"hp":38,"ac":16,"attack_bonus":7,"n":1,"dice":8,"mod":3,"attacks":2,"init":2,"is_player":True},
    {"hp":38,"ac":16,"attack_bonus":7,"n":1,"dice":8,"mod":3,"attacks":2,"init":2,"is_player":True},
]

monster_template = [

    {"hp":50,"ac":16,"attack_bonus":7,"n":2,"dice":8,"mod":3,"attacks":2,"init":2},
    {"hp":50,"ac":16,"attack_bonus":7,"n":2,"dice":8,"mod":3,"attacks":2,"init":2},
]

result = run_simulations(party_template, monster_template, 20000)

print(result)

def hp_difficulty_curve(party_template, monster_template,
                        hp_values, N=5000):

    results = []

    for hp in hp_values:

        modified_monsters = []

        for m in monster_template:

            new_m = dict(m)
            new_m["hp"] = hp
            modified_monsters.append(new_m)

        r = run_simulations(party_template, modified_monsters, N)

        results.append((hp, r["party_win_probability"]))

    return results

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List
import os

app = FastAPI()

# Base folder of this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.get("/")
def home():
    # Serve index.html from the script's folder
    return FileResponse(os.path.join(BASE_DIR, "index.html"))

from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

class CreatureModel(BaseModel):
    hp: int
    ac: int
    attack_bonus: int
    n: int
    dice: int
    mod: int
    attacks: int
    init: int
    is_player: bool

class CombatRequest(BaseModel):
    party: List[CreatureModel]
    monsters: List[CreatureModel]
    auto_hit: bool = True
    random_target: bool = False
    monsters_finish: bool = False

@app.post("/combat_simulate")
def combat_simulate(req: CombatRequest):
    global AUTOHIT, RANDOM_TARGET, FINISH
    AUTOHIT = req.auto_hit
    RANDOM_TARGET = req.random_target
    FINISH = req.monsters_finish

    # Run your existing simulation
    result = run_simulations([c.dict() for c in req.party],
                             [c.dict() for c in req.monsters],
                             N=10000)
    return result

from fastapi.responses import HTMLResponse

@app.get("/combat")
def combat_page():
    return FileResponse("combat.html")  # We'll make this page next

@app.get("/skillcheck")
def skillcheck_page():
    return FileResponse("skillcheck.html")  # We'll make this page next

from pydantic import BaseModel

class SkillCheckRequest(BaseModel):
    mod: int
    dc: int
    adv: int = 0  # 0: normal, 1: advantage, 2: disadvantage
    autosucc: bool = True

@app.post("/skillcheck_simulate")
def skillcheck_simulate(req: SkillCheckRequest):
    # Use the existing skill_check function
    probability = skill_check(req.mod, req.adv, req.dc, req.autosucc)
    return {"probability": probability}

from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict

VALID_DICE = [2, 3, 4, 6, 8, 10, 12, 20, 100]

class DiceRoll(BaseModel):
    n: int   # number of dice
    d: int   # dice type
    mod: int = 0  # modifier

class DiceRollRequest(BaseModel):
    rolls: List[DiceRoll]

@app.post("/dice_roll")
def dice_roll(req: DiceRollRequest):
    results = []
    for r in req.rolls:
        if r.d not in VALID_DICE or r.n < 1:
            continue  # skip invalid dice
        roll_results = [random.randint(1, r.d) for _ in range(r.n)]
        total = sum(roll_results) + r.mod
        results.append({
            "dice": f"{r.n}d{r.d}{'+'+str(r.mod) if r.mod else ''}",
            "rolls": roll_results,
            "modifier": r.mod,
            "total": total
        })
    overall_total = sum(r["total"] for r in results)
    return {"results": results, "overall_total": overall_total}

@app.get("/dice")
def dice_page():
    return FileResponse(os.path.join(BASE_DIR, "dice.html"))

@app.get("/initiative_tracker")
def initiative_tracker():
    return FileResponse("initiative_tracker.html")  # We'll make this page next

@app.get("/FAQ")
def FAQ():
    return FileResponse("FAQ.html")  # We'll make this page next