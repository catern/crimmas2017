from functools import wraps

#===================

def make_owned_thing_helpers(name):
    def register(owner, thing):
        if not hasattr(owner, name):
            setattr(owner, name, {})
        getattr(owner, name)[thing.hotkey] = thing
        thing.parents += [owner]
    def deregister(owner, thing):
        if hasattr(owner, name) and thing.hotkey in getattr(owner, name):
            del getattr(owner, name)[thing.hotkey]
    def delete(thing):
        for parent in thing.parents:
            deregister(parent, thing)
    return register, deregister, delete

#===================

def Action(name, hotkey):
    def decorator(func):
        func.name = name
        func.hotkey = hotkey
        func.parents = []
        func.desc = "{}: {}".format(hotkey, name)
        return func
    return decorator

register_action, \
deregister_action, \
delete_action = make_owned_thing_helpers("actions")

#===================

class Thingy(object):
    def __init__(self, name, hotkey, desc, room_actions=[], player_actions=[]):
        self.name = name
        self.hotkey = hotkey
        self.desc = desc
        self.room_actions = room_actions
        self.player_actions = player_actions

        grab_name = "grab {}".format(self.name)
        grab_hotkey = "g {}".format(self.hotkey)
        drop_name = "drop {}".format(self.name)
        drop_hotkey = "d {}".format(self.hotkey)

        @Action(grab_name, grab_hotkey)
        def grab(player, room):
            register_action(player, drop)
            for action in player_actions:
                register_action(player, action)
            deregister_action(room, grab)
            for action in room_actions:
                register_action(room, action)
        self.grab = grab

        @Action(drop_name, drop_hotkey)
        def drop(player, room):
            register_action(player, grab)
            for action in room_actions:
                register_action(room, action)
            deregister_action(player, drop)
            for action in player_actions:
                register_action(player, action)
        self.drop = drop

        def delete():
            delete_action(grab)
            delete_action(drop)
            for action in room_actions + player_actions:
                delete_action(action)
        self.delete = delete

#===================

class World(object):
    def __init__(self, initial_room, world_action):
        self.initial_room = initial_room
        self.world_action = world_action
        # you can always quit :')
        @Action("Quit", "q")
        def quit(player, room):
            player.victory = True
        register_action(self, quit)
    def act(self, player):
        self.world_action(player)

#===================

def noop(player):
    pass

def seq(functions):
    def new_fun(*args):
        for fun in functions:
            fun(*args)
    return new_fun

def onetime(fun):
    used=False
    def onetime_fun(*args):
        nonlocal used
        if used == False:
            fun(*args)
            used=True
    return onetime_fun

#===================

class Room(object):
    def __init__(self, name, desc, short_desc, room_action):
        self.name = name
        self.desc = desc
        self.short_desc = short_desc
        self.room_action = room_action
        self.thingies = {}
    def __str__(self):
        desc = ""
        desc += self.desc + "\n"
        for thingy in self.thingies.values():
            desc += thingy.desc + "\n"
        return self.desc
    def act(self, player):
        self.room_action(player)

def link_rooms(room1, room2, passage_phrase, hotkey_pair, action_phrase):
    def make_action(newRoom, hotkey):
        @Action("{}, {}".format(passage_phrase, newRoom.short_desc), hotkey)
        def action(player, room):
            print("""
        """ + action_phrase)
            player.room = newRoom
        return action
    a, b = hotkey_pair
    register_action(room1, make_action(room2, a))
    register_action(room2, make_action(room1, b))

#===================

def increment_stat(player, stat, value):
    if not stat in player.stats:
        player.stats[stat] = 0
    player.stats[stat] += value
    sign = "+" if value >= 0 else ""
    print("""        {}{} {}""".format(sign, value, stat))
def set_stat(player, stat, value):
    player.stats[stat] = value
def get_stat(player, stat):
    if stat in player.stats:
        return player.stats[stat]
    else:
        return 0

def make_stat_incrementer(stat, value):
    @onetime
    def fun(player):
        increment_stat(player, stat, value)
    return fun

#===================

class Player(object):
    def __init__(self):
        self.name = "player"
        self.stats = {}
        self.victory = False #for now (growth mindset)
        self.appearance ="""
        You are wearing a festive sweater, sparkling with tinsel.
        You feel real cozy!!!
        """
        @Action("Look at self", "ls")
        def look_at_self(player, room):
            print(self.appearance)
            increment_stat(player, "coziness", 1)

        register_action(self, look_at_self)

    def __str__(self):
        print("""~~ PLAYER STATS ~~""")
        stat_strings = ["{} = {}".format(key, value) 
                        for key, value in self.stats.items()]
        return "\n".join(stat_strings)

