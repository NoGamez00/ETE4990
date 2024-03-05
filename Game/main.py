# %%
# Imports here
import random
import json
import math
from __future__ import annotations

# %%
class Game:
    # 
    def __init__(self, room_cycle: int = 6):
        self._room_cycle = room_cycle
        self._room_counter = 0
        self._rooms: list[Room] = []
        self._state = "Begin"
        self._roomstate = "Unexplored"

    @property
    def _player(self) -> Player:
        return Player(level=0)
    
    @_player.setter
    def _player(self, value: Player) -> None:
        self._player = value

    @property
    def _current_room(self) -> Room:
        return self._rooms[-1]

    def generate_room(self) -> None:
        self._room_counter += 1
        room_check = self._room_counter % self._room_cycle
        room_type = 0 if room_check == 3 else ( 2 if room_check == 0 else 1)# TODO: random.randint(0, 1) )
        room = Room(room_type=room_type, player=self._player)
        room.generate_encounter()
        if enemy := room._encounter:
            enemy.restore_hp(full_restore=True)
        self._rooms.append(room)
        self._room_state = "Waiting"

    def begin(self) -> None:
        self._player = Player(level=1)
        self.generate_room()

    @classmethod
    def start_game(cls, rounds_cycle: int = 6) -> 'Game':
        # TODO: Welcome text + explain rules here
        print("Game Start!")
        # input()
        return cls(rounds_cycle)

    def enter_room(self) -> None:
        # TODO: input("Press 'Enter' to enter the room")
        print(f"You entered room #{len(self._rooms)}.")
        self._state = "Exploring"

    def commence_battle(self) -> None:
        enemy = self._current_room._encounter
        if not enemy: return
        self._state = "Battle"
        # TODO: Add text here
        print(
            f"Oh no! You entered a room with a shadow!",
            f"You are up against {enemy._spirit_name} (lvl: {enemy._level}).",
            "Prepare for a fight!", sep='\n')
        
    def battle_end(self, player: Player, room: Room) -> None:
        player.level_up(levels=10)
        # TODO: player.get_new_spirit(room=room)
        for spirit in player._available_spirits:
            spirit.level_up_to(spirit._level + 10)
            spirit._level += 10
            # TODO: spirit.get_new_skill()
        # TODO: self._player.get_new_items(drops=room._item_drop)
        # TODO: self._player.get_new_melee(drop=room._melee_drop)
        # TODO: self._player.get_new_ranged(drop=room._ranged_drop)        

    def safe_room(self) -> None:
        self._player._ranged_weapon._rounds_current = self._player._ranged_weapon._rounds_max

    def safe_actions(self):
        self._state = "Safe"
        print("Whew! You are safe... for now!")

    def end_game(self) -> None:
        print("Game END")
        

# %%
class Room:
    # Class that respresents the room that the player would enter
    # The room contains all entities (i.e. Player, Enemy Shadow, Items)
    # TODO: Add buff/debuffs countdown (3 rounds)
    def __init__(self, room_type, player: Player) -> None:
        self._room_type = {0: "Safe Room", 1: "Spirit Battle", 2: "Boss Room"}[room_type]
        self._melee_drop = MeleeWeapon.get_random_melee_weapon() if self._room_type == "Boss Room" else None
        self._ranged_drop = RangedWeapon.get_random_ranged_weapon() if self._room_type == "Boss Room" else None
        self._stat_afflictions: list[dict] = []
        self._player = player
        self._state = "Unexplored"
        self._encounter: RogueSpirit|None = None

    @property
    def _item_drop(self) -> list['Item']:
        items = [Item.get_random_item(), Item.get_random_item(), Item.get_random_item()]
        if self._room_type == "Boss Room":
            items.append(Item.get_random_item())
            items.append(Item.get_random_item())
        return items

    def generate_encounter(self) -> None:
        boss = True if self._room_type == "Boss Room" else False
        self._encounter = RogueSpirit.random_spirit(level=self._player._level, boss=boss) if self._room_type != "Safe Room" else None
        self._state = "Danger" if self._encounter else "Safe"

    @property
    def result(self) -> str:
        if self._encounter:
            result = "Victory" if self._encounter._hp == 0 else "Defeat"
        else:
            result = "Safe"
        return result
    
    def stat_affliction_timer_countdown(self) -> None:
        for affliction in self._stat_afflictions:
            affliction["rounds"] -= 1
            if affliction["rounds"] == 0:
                self.remove_stat_affliction_timer(affliction['stat'], affliction['buff'], affliction['target'])        

    def add_stat_affliction_timer(self, stat: str, buff: bool, target) -> None:
        self._stat_afflictions.append( {"stat": stat,  "buff": buff, "target": target, "rounds": 3} )

    def remove_stat_affliction_timer(self, stat: str, buff: bool, target) -> None:
        for i in range(len(self._stat_afflictions)):
            affliction = self._stat_afflictions[i]
            if affliction['stat'] == stat and affliction['buff'] == buff and affliction['target'] == target:
                removed = self._stat_afflictions[i].pop(i)
        removed['target'].apply_stat_affliction(derived_stat=removed['stat'], buff=not removed['buff'])


# %%
class Item:
    # Holds general information on items that can be collected and used
    # TODO: Incorporate a backpack; Incoporate item usage both inside and outside of combat; Incoporate item drops
    __items_json = "items.json"

    def __init__(self, item_name: str) -> None:
        self._item_name = item_name
        self._description = self.__item_dict['description']

    @staticmethod
    def get_items_from_json() -> list[dict]:
        with open(Item.__items_json, 'r') as items_file:
            items = json.load(items_file)
        return items

    @property
    def __item_dict(self) -> dict:
        items = Item.get_items_from_json()
        for item in items:
            if item['name'] == self._item_name:
                return_item = item
                break
        return return_item

    @property
    def _effects(self) -> list:
        effects: list = []
        for effect in self.__item_dict['effects']:
            if effect['type'] == "Recovery":
                effects.append( RecoveryItemEffect.new_effect(effect) )
            elif effect['type'] == "Support":
                effects.append( SupportItemEffect.new_effect(effect) )
        return effects

    @classmethod
    def get_random_item(cls) -> 'Item':
        item_names = []
        items = Item.get_items_from_json()

        for item in items:
            item_names.append(item['name'])

        random_item_name = item_names[random.randint(0, len(item_names)-1)]
        return cls(random_item_name)


# %%
class RecoveryItemEffect:
    # Subclass of item that holds the healing items
    def __init__(self, affected_stat: str, points: int, percent: float) -> None:
        self._type = "Recovery"
        self._affected_stat = affected_stat
        self._points = points
        self._percent = percent

    @classmethod
    def new_effect(cls, effect: dict) -> 'RecoveryItemEffect':
        return cls(affected_stat=effect['stat'], points=effect['points'], percent=effect['percent'] )


# %%
class SupportItemEffect:
    # Subclass of item that holds the buff and debuff items
    # Since the buff/debuff can be applied to anyone (i.e. the player or enemy shadow), this was made into one class
    def __init__(self, affected_stat: str, multiplier: float) -> None:
        self._type = "Support"
        self._affected_stat = affected_stat
        self._multiplier = multiplier

    @classmethod
    def new_effect(cls, effect: dict) -> 'SupportItemEffect':
        return cls( affected_stat=effect['stat'], multiplier=effect['multiplier'] )

# %%``
class Spirit:
    # This class is the template for all spirits (enemy or captured)
    __base_stats = { "STR": 10, "MAG": 10, "END": 10, "AGI": 10, "LUC": 10}
    __spirits_json = "spirits.json"

    def __init__(self, level: int, spirit_name: str) -> None:
        # super().__init__(level, health_points, skill_points, xp)
        self._level = level
        self._spirit_name = spirit_name
        self._stats = self.__base_stats

    @staticmethod
    def get_spirits_from_json() -> list[dict]:
        with open(Spirit.__spirits_json, 'r') as spirits_file:
            spirits = json.load(spirits_file)
        return spirits

    def get_spirit_from_json(self) -> dict:
        for spirit in self.get_spirits_from_json():
            if spirit['name'] == self._spirit_name: break
        return spirit

    def get_resistance_types(self) -> dict:
        return self.get_spirit_from_json()['resistances']

    @property
    def _resistances(self) -> dict:
        resistances_dict = {}
        spirit_resistances: dict = self.get_resistance_types()
        for spirit_resistance_type in spirit_resistances:
            multiplier = {"weak": 1.25, "resist": 0.5, "null": 0, "drain": -1}
            resistance_multiplier = multiplier.get(spirit_resistance_type, 1)
            resistance_type = spirit_resistances[spirit_resistance_type]
            for resistance in resistance_type:
                resistances_dict[resistance] = resistance_multiplier
        return resistances_dict

    def get_resistance(self, affinity: str) -> float:
        return self._resistances.get(affinity, 1.0)

    @property
    def _derived_stats(self) -> dict:
        # TODO: Incorporate _derived_stats into combat
        return {
            "Magic Attack Multiplier": self._stats['MAG'],
            "Physical Attack Multiplier": math.sqrt(self._stats['STR']),
            "Defense": self._stats['END'] * 8,
            "Evasion": self._stats['AGI'] + ( self._stats['LUC'] / 4 ) + ( self._level / 5 ),
            # "Hit": self._stats['AGI'] * modifiers['Hit'] + 100
        }
    
    def apply_stat_affliction(self, derived_stat: str, buff: bool = True) -> None:
        multiplier = 1.25 if buff else 0.8
        self._derived_stats[derived_stat] *= multiplier

    def level_up_to(self, level_up_to: int) -> None:
        level_ups = level_up_to - self._level
        index_map = {0: "STR", 1: "MAG", 2: "END", 3: "AGI", 4: "LUC"}

        for level_up in range(level_ups):
            for bonus in range(3):
                stat_index = random.randint(0, 4)
                self._stats[ index_map[ stat_index ] ] += 1
        print(f"{self._spirit_name} leveled up {level_ups} times to {level_up_to}.",
              "Theses are its new stats",
              "{:5}{:5}{:5}{:5}{:5}".format("STR", "MAG", "END", "AGI", "LUC"),
              "{:5}{:5}{:5}{:5}{:5}".format(self._stats["STR"], self._stats["MAG"], self._stats["END"], self._stats["AGI"], self._stats["LUC"]), sep='\n')
        

# %%
class RogueSpirit(Spirit):
    # A subclass of Spirit that holds all the information of an enemy spirit
    def __init__(self, level, spirit_name, boss: bool = False) -> None:
        super().__init__(level, spirit_name)
        self._boss = boss
        self._skills = [Skill.get_random_skill() for i in range (0, 8)]
        self._hp = 0
        self._level = ( self._level + 5 ) if self._boss else self._level

    @property
    def _max_hp(self) -> int:
        return int( min( (self._level + self._stats['END']) * 6, 999 ) )

    def restore_hp(self, full_restore: bool = True, amount: int = 0) -> None:
        if full_restore:
            self._hp = self._max_hp
        else:
            self._hp += amount
            self._hp = min(self._hp, self._max_hp)

    @property
    def _stat_afflictions(self) -> dict:
        return {"ATK": 1, "Defense": 1, "Evasion": 1, "Hit": 1}

    def choose_random_action(self, player: Player, room: Room) -> None:
        random_skill_index = random.randint(0, len(self._skills) - 1)
        skill = self._skills[random_skill_index]
        skill.use_skill(user=self, target=player)

        if self._hp <= 0:
            self._hp = 0
            room._state = "Victory"
        elif player._hp <= 0:
            player._hp = 0
            room._state = "Defeat"
        else:
            room._state = "Dangerous"

    @classmethod
    def random_spirit(cls, level, boss=False) -> RogueSpirit:
        spirit_names = []
        spirits = RogueSpirit.get_spirits_from_json()
        for spirit in spirits:
            spirit_names.append(spirit['name'])
        random_spirit_name = spirit_names[random.randint(0, len(spirit_names)-1)]
        return cls( level=level, spirit_name=random_spirit_name, boss=boss )
        
    
# %%
class ObtainedSpirit(Spirit):
    # A subclass of Spirit that holds all the information of a spirit that has been captured
    def __init__(self, level, spirit_name, skills: list = []) -> None:
        super().__init__(level, spirit_name)
        self._skills = skills

    @classmethod
    def convert_from_rogue(cls, spirit: RogueSpirit) -> ObtainedSpirit:
        return cls(
            level=spirit._level,
            spirit_name=spirit._spirit_name,
            skills=spirit._skills
        )


# %%
class Skill:
    # The Skill class is the template for all skills that can be used by a spirit (enemy or captured)
    __skill_json = "skills.json"
    def __init__(self, skill_name) -> None:
        self._skill_name = skill_name

    @staticmethod
    def get_skills_list() -> list[dict]:
        with open(Skill.__skill_json, 'r') as skills_json:
            skills = json.load(skills_json)
        return skills

    @staticmethod
    def get_skill_dict(skill_name: str) -> dict:
        skills = Skill.get_skills_list()
        for skill in skills:
            if skill['name'] == skill_name:
                return_skill = skill
        return return_skill

    @staticmethod
    def get_skill(skill_name: str) -> AttackSkill | SupportSkill:
        skill = Skill.get_skill_dict(skill_name)
        if skill['affinity'] not in ['Support', 'Recovery']:
            return AttackSkill.create_attack(skill)
        else:
            return SupportSkill.create_support(skill)

    @staticmethod
    def get_random_skill() -> Skill:
        skills = Skill.get_skills_list()
        random_skill = skills[random.randint(0, len(skills)-1)]
        return Skill.get_skill(random_skill['name'])
    
    def use_skill(self, user: Player|RogueSpirit, target: RogueSpirit|Player) -> None:
        pass


# %%
class AttackSkill(Skill):
    # A class that holds the general information for the potential attack effect of the Skill class
    def __init__(self, skill_name, power: int, accuracy: int, affinity: str) -> None:
        super().__init__(skill_name)
        self._power = power
        self._accuracy = accuracy
        self._affinity= affinity

    @property
    def _display_power(self) -> str:
        power_display_limits = {50: "Miniscule", 130: "Miniscule", 180: "Medium", 240: "Heavy", 330: "Severe", 10000: "Colossal"}
        for limit in power_display_limits:
            if self._power <= limit:
                display = power_display_limits[limit]
                break
        return display

    @staticmethod
    def create_attack(skill_dict: dict) -> MagicAttackSkill | PhysicalAttackSkill:
        if skill_dict['affinity'] not in ['Phys', 'Gun']:
            return MagicAttackSkill.create_magic_attack(skill_dict)
        else:
            return PhysicalAttackSkill.create_phys_attack(skill_dict)

# %%
class MagicAttackSkill(AttackSkill):
    # A subclass of AttactEffect for Skill that holds the information of a skill that deals magic damage
    def __init__(self, skill_name, power, accuracy, affinity, sp_cost: int) -> None:
        super().__init__(skill_name, power, accuracy, affinity)
        self._sp_cost = sp_cost

    @classmethod
    def create_magic_attack(cls, skill_dict: dict) -> MagicAttackSkill:
        return cls(
            skill_name=skill_dict['name'],
            power=skill_dict['power'],
            accuracy=skill_dict['accuracy'],
            affinity=skill_dict['affinity'],
            sp_cost=skill_dict['cost']
        )

    def display_skill(self, player: Player, template: str) -> str:
        return template.format(
            self._skill_name, f'{self._sp_cost} SP', f'Deal {self._display_power} {self._affinity} damage.'
        )

    def use_skill(self, user: Player|RogueSpirit, target: RogueSpirit|Player) -> None:
        if type(user) == Player and type(target) == RogueSpirit:
            user._sp -= self._sp_cost
            damage = self.calculate_damage(user._current_spirit, target)
            target._hp -= damage
            print(f"You used {self._skill_name} on {target._spirit_name} and hit for {damage} HP.")
        elif type(user) == RogueSpirit and type(target) == Player:
            damage = self.calculate_damage(user, target._current_spirit)
            target._hp -= damage
            print(f"{user._spirit_name} used {self._skill_name} on you and hit for {damage} HP.")
 
    def calculate_damage(self, spirit: ObtainedSpirit|RogueSpirit, target: RogueSpirit|ObtainedSpirit) -> int:
        magic_multiplier = spirit._derived_stats['Magic Attack Multiplier']
        target_defense = target._derived_stats['Defense']
        return int( math.sqrt( self._power * magic_multiplier / target_defense ) )


# %%
class PhysicalAttackSkill(AttackSkill):
    # A subclass of AttackEffect for Skill that holds the information of a skill that deals physical damage
    def __init__(self, skill_name, power, accuracy, affinity, hp_cost: int) -> None:
        super().__init__(skill_name, power, accuracy, affinity)
        self._hp_cost = hp_cost # HP Cost is the percent of total HP

    @classmethod
    def create_phys_attack(cls, skill_dict: dict) -> 'PhysicalAttackSkill':
        return cls(
            skill_name=skill_dict['name'],
            power=skill_dict['power'],
            accuracy=skill_dict['accuracy'],
            affinity=skill_dict['affinity'],
            hp_cost=skill_dict['cost'],
        )

    def calculate_damage(self, spirit: ObtainedSpirit|RogueSpirit, target: ObtainedSpirit|RogueSpirit) -> int:
        physical_multiplier = spirit._derived_stats['Physical Attack Multiplier']
        target_defense = target._derived_stats['Defense']
        return int(self._power * physical_multiplier / target_defense)

    def calculate_hp_cost(self, max_hp: int) -> int:
        return int(max_hp * self._hp_cost / 100)

    def use_skill(self, user: Player|RogueSpirit, target: RogueSpirit|Player) -> None:
        if type(user) == Player and type(target) == RogueSpirit:
            user._hp -= self.calculate_hp_cost(user._max_hp)
            damage = self.calculate_damage(spirit=user._current_spirit, target=target)
            target._hp -= damage
            print(f"You used {self._skill_name} on {target._spirit_name} and dealt {damage} HP.")
        elif type(user) == RogueSpirit and type(target) == Player:
            damage = self.calculate_damage(spirit=user, target=target._current_spirit)
            target._hp -= damage
            print(f"{user._spirit_name} used {self._skill_name} ({self._affinity}) on you and dealt {damage} HP")

    def display_skill(self, player: Player, template: str) -> str:
        hp_cost = int(player._max_hp * self._hp_cost / 100)
        return template.format(
            self._skill_name, f'{hp_cost} HP', f'Deal {self._display_power} {self._affinity} damage.'
        )

# %%
class SupportSkill(Skill):
    # A subclass of Skill that holds the information of a skill that buffs or debuffs a character
    def __init__( self, skill_name, sp_cost: int, affinity: str, recovery_display: str, buffs: list[str], debuffs: list[str] ) -> None:
        super().__init__(skill_name)
        self._sp_cost = sp_cost
        self._affinity = affinity
        self._recovery_display = recovery_display
        self._recovery_amount = {"Slight": 60, "Moderate": 140,"Full": 10000}.get(self._recovery_display, 0)
        self._buffs = buffs
        self._debuffs = debuffs

    @classmethod
    def create_support(cls, skill_dict: dict) -> 'SupportSkill':
        return cls(
            skill_name=skill_dict['name'],
            sp_cost=skill_dict['cost'],
            affinity=skill_dict['affinity'],
            recovery_display=skill_dict.get('amount', 0),
            buffs=skill_dict.get('buffs', []),
            debuffs=skill_dict.get('debuffs', [])
        )

    def use_skill(self, user: Player|RogueSpirit, target: Player|RogueSpirit) -> None:
        #TODO: Create function to use support skills
        if self._affinity == "Recovery":
            user._hp += self._recovery_amount
            user._hp = min(user._hp, user._max_hp)
        for buff in self._buffs:
            user._stat_afflictions[buff] = 1.25
        for debuff in self._debuffs:
            target._stat_afflictions[debuff] = 0.75

        if type(user) == Player and type(target) == RogueSpirit:
            user._sp -= self._sp_cost
            heal_text = f"You healed for {self._recovery_amount} HP. " if self._affinity == "Recover" else ""
            buffs_text = f"You applied {'/'.join(self._buffs)} to yourself. " if self._buffs else ""
            debuffs_text = f"You applied {'/'.join(self._debuffs)} to your opponent." if self._debuffs else ""
            print(f"You used {self._skill_name}. {heal_text + buffs_text + debuffs_text} ")
        elif type(user) == RogueSpirit and type(target) == Player:
            spirit_name = user._spirit_name
            heal_text = f"{spirit_name} healed for {self._recovery_amount} HP. " if self._affinity == "Recover" else ""
            buffs_text = f"{spirit_name} applied {'/'.join(self._buffs)} to themself. " if self._buffs else ""
            debuffs_text = f"{spirit_name} applied {'/'.join(self._debuffs)} to you." if self._debuffs else ""
            print(f"{spirit_name} used {self._skill_name}. {heal_text + buffs_text + debuffs_text} ")
    
    def display_skill(self, player: Player, template: str) -> str:
        buffs = f"Raise {'/'.join(self._buffs)}. " if self._buffs else ""
        debuffs = f"Lower {'/'.join(self._debuffs)}. " if self._debuffs else ""
        recover = f"Heal a {self._recovery_display} amount of HP. " if self._recovery_display else ""
        return template.format(self._skill_name, f'{self._sp_cost} SP', buffs + debuffs + recover)


# %%
class Player:
    # Holds information and commands that are relevant to the player
    def __init__(self, level: int) -> None:
        self._level = level
        self._hp: int = 84
        self._sp: int = 26
        self._available_spirits: list[ObtainedSpirit] = [
            ObtainedSpirit(
                level=self._level,
                spirit_name="Arsene",
                skills=[Skill.get_random_skill() for i in range (0, 8)]
        )]
        self._current_spirit: ObtainedSpirit= self._available_spirits[0]
        self._melee_weapon: MeleeWeapon = MeleeWeapon.get_random_melee_weapon()
        self._ranged_weapon: RangedWeapon = RangedWeapon.get_random_ranged_weapon()
        self._items: list[Item] = []

    
    hp_limits = (84, 572)
    hp_per_level = ( hp_limits[1] - hp_limits[0] ) / 99

    @property
    def _max_hp(self) -> int:
        return int( self.hp_per_level * self._level ) + self.hp_limits[0]
    
    def restore_hp(self, full_restore: bool = False, amount: int = 0) -> None:
        if full_restore:
            self._hp = self._max_hp
        else:
            self._hp += amount
            self._hp = min(self._hp, self._max_hp)

    sp_limits = (26, 308)
    sp_per_level = ( sp_limits[1] - sp_limits[0] ) / 99

    @property
    def _max_sp(self) -> int:
        return int( ( self.sp_per_level * self._level ) + self.sp_limits[0] )
    
    def restore_sp(self, full_restore: bool = False, amount: int = 0) -> None:
        if full_restore:
            self._sp = self._max_sp
        else:
            self._sp += amount
            self._sp = min(self._sp, self._max_sp)

    def level_up(self, levels: int) -> None:
        self._level += levels
        self.restore_hp(amount=int(levels * self.hp_per_level))
        self.restore_sp(amount=int(levels * self.sp_per_level))

    @property
    def _stat_afflictions(self) -> dict:
        return {"ATK": 1, "Defense": 1, "Evasion": 1, "Hit": 1}

    @property
    def _possible_skill_actions(self) -> list[str]:
        return [skill._skill_name for skill in self._current_spirit._skills]

    @property
    def _possible_spirit_actions(self) -> list[str]:
        return [spirit._spirit_name for spirit in self._available_spirits]

    def get_spirit_from_name(self, spirit_name: str) -> ObtainedSpirit:
        for spirit in self._available_spirits:
            if spirit._spirit_name == spirit_name:
                return spirit
        return self._current_spirit

    def display_battle_options(self) -> str:
        print("Here are the options available to you:",
            "(Hit 'Escape' to see your options as a list.)", sep='\n\t')
        
        print(f"Use a Skill of {self._current_spirit._spirit_name} (type the name of the skill to use it).")
        self.view_skills(template="\t{:25}{:10}{:30}", stat_filter=True)
        
        print("Switch Spirits (type the name of the spirit to view its skills).")
        self.view_spirits(template="\t{:25}{:45}")
        
        print("Use Melee Weapon (type 'Melee' to use your melee weapon):")
        self.view_melee_weapon(template="\t{:25}{:10}{:10}")

        print("Use Ranged Weapon (type 'Ranged' to use your ranged weapon):")
        self.view_ranged_weapon(template="\t{:25}{:10}{:10}{:10}")

        possible_actions = self._possible_skill_actions + self._possible_spirit_actions + ["Melee", "Ranged"]
        player_action = self.wait_on_player_action(possible_actions)

        while player_action in self._possible_spirit_actions:
            player_action = self.switch_spirits(previous_action=player_action, options=possible_actions)

        return player_action
    
    def skills_list_stat_filter(self) -> list:
        skills_list = []
        for skill in self._current_spirit._skills:
            if type(skill) == PhysicalAttackSkill:
                if skill._hp_cost <= self._hp:
                    skills_list.append(skill)
            elif skill._sp_cost <= self._sp:
                skills_list.append(skill)
        return skills_list

    def view_skills(self, template: str, stat_filter: bool = False, **kargs) -> list[Skill]:
        print(template.format('Skill Name', 'Cost', 'Description'))
        if spirit_name := kargs.get('spirit_name', None):
            spirit = self.get_spirit_from_name(spirit_name)
        else:
            spirit = self._current_spirit
        
        if stat_filter:
            skills_list = self.skills_list_stat_filter()
        else:
            skills_list = spirit._skills

        for skill in skills_list:
            print(f"{skill.display_skill(self, template)}")

        return skills_list

    def view_spirits(self, template: str) -> None:
        if len(self._available_spirits) > 1:
            print(template.format('Spirit Name', "Resistances"))
            for spirit in self._available_spirits:
                resistance_text_list = []
                for resistance_type in spirit.get_resistance_types():
                    if resistances := spirit.get_resistance_types()[resistance_type]:
                        resistance_text_list.append(f'{resistance_type.title()}: {', '.join(resistances)}')
                print(template.format(spirit._spirit_name, '; '.join(resistance_text_list)))
        else:
            print("\tLooks like you have do no have any other spirits yet.")

    def view_melee_weapon(self, template) -> None:
        print(template.format( "Melee Weapon Name", "Power", "Accuracy" ))
        print(template.format( self._melee_weapon._weapon_name, str(self._melee_weapon._attack), str(self._melee_weapon._accuracy)))

    def view_ranged_weapon(self, template) -> None:
        print(template.format( "Ranged Weapon Name", "Power", "Accuracy", "Rounds" ))
        print(template.format( self._ranged_weapon._weapon_name, str(self._ranged_weapon._attack), str(self._ranged_weapon._accuracy), f'{self._ranged_weapon._rounds_current}/{self._ranged_weapon._rounds_max}'))

    def wait_on_player_action(self, options: list) -> str:
        player_action = input()
        while player_action not in options:
            player_action = input(f"Please enter a valid action: {options}")
        return player_action

    def switch_spirits(self, previous_action: str, options: list[str]) -> str:
        print("\nEnter the spirit's name again to switch to this spirit or enter a differnt option.",
            "\t(Hit 'Escape' to see your options in a list.)\n",
            f"Skills of {previous_action}:", sep='\n')
        new_skills_options = self.view_skills(template="\t{:25}{:10}{:30}", spirit_name=previous_action)    
        player_action = self.wait_on_player_action(options=options)
        if player_action == previous_action:
            self._current_spirit = self.get_spirit_from_name(player_action)
            print("Your current spirit has been switched.",
                "Please enter your new action. Hit 'Escape' to see your options.")
            player_action = self.wait_on_player_action(options=new_skills_options + ['Melee', "Ranged"])
        
        return player_action
    
    def perform_action(self, action: str, enemy: RogueSpirit, room=Room) -> None:
        enemy = room._encounter
        if action in self._possible_skill_actions:
            skill = Skill.get_skill(skill_name=action)
            # TODO: Fix Support and Magical
            skill.use_skill(user=self, target=enemy)
        elif action == "Melee":
            self.use_melee(target=enemy)
        elif action == "Ranged":
            self.use_ranged(target=enemy)

        if enemy._hp <= 0:
            enemy._hp = 0
            room.state = "Victory"
        elif self._hp <= 0:
            self._hp = 0
            room.state = "Defeat"
        else:
            room.state = "Dangerous"

    def use_melee(self, target: RogueSpirit) -> None:
        if random.randint(0, 100) <= self._melee_weapon._accuracy:
            melee_damage = int(math.sqrt(self._melee_weapon._attack))
            target._hp -= melee_damage
            print(f"You hit {target._spirit_name} with {self._melee_weapon._weapon_name} for {melee_damage} HP.")
        else:
            print("You missed!")

    def use_ranged(self, target: RogueSpirit) -> None:
        if random.randint(0, 100) <= self._ranged_weapon._accuracy:
            ranged_damage = int(math.sqrt(self._ranged_weapon._attack))
            target._hp -= ranged_damage
            self._ranged_weapon._rounds_current -= 1
            print(f"You shot {target._spirit_name} with {self._ranged_weapon._weapon_name} for {ranged_damage} HP.")
            print(f"You now have {self._ranged_weapon._rounds_current}/{self._ranged_weapon._rounds_max} rounds left.")
        else:
            print("You missed!")


# %%
class MeleeWeapon:
    # The class that holds the information for the weapon that the player holds
    # TODO: Incorporate melee weapon drops in boss rooms
    __melee_json = "melee_weapons.json"
    
    def __init__(self, weapon_name) -> None:
        self._weapon_name = weapon_name
        self._attack = MeleeWeapon.get_weapon_dict(self._weapon_name)['attack']
        self._accuracy = MeleeWeapon.get_weapon_dict(self._weapon_name)['accuracy']

    @staticmethod
    def get_melee_list() -> list[dict]:
        with open(MeleeWeapon.__melee_json, 'r') as melee_json:
            weapons = json.load(melee_json)
            return weapons

    @staticmethod
    def get_weapon_dict(name: str) -> dict:
        weapons = MeleeWeapon.get_melee_list()
        for weapon in weapons:
            if weapon['name'] == name:
                return_weapon = weapon
        return return_weapon

    @classmethod
    def get_random_melee_weapon(cls) -> 'MeleeWeapon':
        weapons = MeleeWeapon.get_melee_list()
        random_melee_weapon = weapons[ random.randint( 0, len(weapons)-1 ) ]
        return cls(random_melee_weapon['name'])


# %%
class RangedWeapon:
    # The class that holds the information for the gun that the player holds
    # TODO: Incorpoarte ranghed weapon drops in boss rooms
    __ranged_json = "ranged_weapons.json"
    
    def __init__(self, weapon_name) -> None:
        self._weapon_name = weapon_name
        self._attack = RangedWeapon.get_weapon_dict(self._weapon_name)['attack']
        self._accuracy = RangedWeapon.get_weapon_dict(self._weapon_name)['accuracy']
        self._rounds_max = RangedWeapon.get_weapon_dict(self._weapon_name)['rounds_max']
        self._rounds_current = self._rounds_max

    @staticmethod
    def get_melee_list() -> list[dict]:
        with open(RangedWeapon.__ranged_json, 'r') as ranged_json:
            weapons = json.load(ranged_json)
            return weapons

    @staticmethod
    def get_weapon_dict(name: str) -> dict:
        weapons = RangedWeapon.get_melee_list()
        for weapon in weapons:
            if weapon['name'] == name:
                return_weapon = weapon
                break
        return return_weapon

    @classmethod
    def get_random_ranged_weapon(cls) -> 'RangedWeapon':
        weapons = RangedWeapon.get_melee_list()
        random_melee_weapon = weapons[ random.randint( 0, len(weapons)-1 ) ]
        return cls(random_melee_weapon['name'])


# %%
def main() -> None:
    game = Game.start_game() # Welcome text + explain rules of this rogue-like using Persona5 entities
    player = game._player
    player._available_spirits.append(ObtainedSpirit.convert_from_rogue(RogueSpirit.random_spirit(1)))

    while game._state != "Game Over":
        game.generate_room()
        game.enter_room()
        room = game._current_room
        if enemy := room._encounter:
            game.commence_battle()
            while room._state not in ["Victory", "Defeat"]:
                print('=' * 100)
                player_action = player.display_battle_options()
                print('=' * 100)
                player.perform_action(action=player_action, enemy=enemy, room=room)
                print(f"Player (LVL: {player._level}; HP: {player._hp}/{player._max_hp}; SP: {player._sp}/{player._max_sp})",
                      f"Enemy (LVL: {enemy._level}; HP: {enemy._hp}/{enemy._max_hp})", sep='\t')
                if room._state in ["Victory", "Defeat"]: break
                print('-' * 100)
                enemy.choose_random_action(player=player, room=room)
                print(f"Player (LVL: {player._level}; HP: {player._hp}/{player._max_hp}; SP: {player._sp}/{player._max_sp})",
                      f"Enemy (LVL: {enemy._level}; HP: {enemy._hp}/{enemy._max_hp})", sep='\t')
            print("=" * 100)
            game.battle_end(player=player, room=room)
            game.safe_actions()
        else:
            game.safe_room()
        input("Press 'Enter' to continues.")
        game._state = "Game Over" if player._hp == 0 else "Continue"
    game.end_game()

if __name__ == "__main__":
    main()
# %%