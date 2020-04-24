from enum import Enum
import numpy as np
from random import randint, choice as random_choice
import math
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

MAP_X_BOUND = 8
MAP_Y_BOUND = 8
CRIT_KEYS_LOWER_BOUND = int(0.75*MAP_X_BOUND)
CRIT_KEYS_UPPER_BOUND = MAP_X_BOUND
BON_KEYS_LOWER_BOUND = 8
BON_KEYS_UPPER_BOUND = 14
CRIT_PATH_LEN_LOWER_BOUND = CRIT_KEYS_LOWER_BOUND * 3 + 1
CRIT_PATH_LEN_UPPER_BOUND = CRIT_KEYS_LOWER_BOUND * 3 - 1
ROOMCOUNT_LOWER_BOUND = MAP_X_BOUND * (MAP_X_BOUND - 1) - 6
ROOMCOUNT_UPPER_BOUND = MAP_X_BOUND ** 2


def manhattan_dist(u, v):
    a, b = u
    c, d = v
    return int(math.fabs(a-c) + math.fabs(b-d))


def valid_neighbours(coord):
    x, y = coord
    return [
        (x, y) for x, y in [
            (x+1, y),
            (x-1, y),
            (x, y+1),
            (x, y-1)
        ]
        if (x >= 0 and x < MAP_X_BOUND) and (y >= 0 and y < MAP_Y_BOUND)
    ]


def empty_map():
    map = []
    for _ in range(MAP_X_BOUND):
        row = []
        for _ in range(MAP_Y_BOUND):
            row.append(Room(empty=True))
        map.append(row)
    return map


class Room:
    def __init__(self, crit=False, empty=False, base=False, boss=False):
        self.crit = crit
        self.empty = empty
        self.base = base
        self.boss = boss


class Map:
    def __init__(self):
        self._map = empty_map()
        self._crit_edges = []
        self._bon_edges = []
        self.count = 0

    def get(self, *coords):
        x, y = coords
        return self._map[x][y]

    def set(self, x, y, room):
        if room.empty == False:
            self.count += 1
        self._map[x][y] = room

    def _render(self):
        lc_crit = LineCollection(self._crit_edges, color='r')
        lc_bon = LineCollection(self._bon_edges, color='b')
        _, ax = plt.subplots()
        ax.add_collection(lc_crit)
        ax.add_collection(lc_bon)
        ax.autoscale()
        ax.set_xlim([-1, MAP_X_BOUND])
        ax.set_ylim([-1, MAP_Y_BOUND])
        for x in range(len(self._map)):
            for y in range(len(self._map[x])):
                if self._map[x][y].empty == False:
                    color = None
                    if self._map[x][y].base == True:
                        color = 'g'
                    elif self._map[x][y].boss == True:
                        color = 'r'
                    elif self._map[x][y].crit == True:
                        color = 'y'
                    else:
                        color = 'b'
                    circ = plt.Circle((x, y), radius=0.1,
                                      color=color, fill=True)
                    ax.add_patch(circ)

    def show(self):
        self._render()
        plt.show()

    def branchable(self):
        l = []
        for i in range(len(self._map)):
            for j in range(len(self._map[i])):
                if self._map[i][j].empty == False and self._map[i][j].boss == False:
                    l.append((i, j))
        return l

    def connect(self, a, b, crit):
        cur = a
        while cur != b:
            neighbourhood = valid_neighbours(cur)
            min_mh_dist = min(manhattan_dist(b, neighbour)
                              for neighbour in neighbourhood)
            prev = cur
            cur = random_choice([neighbour for neighbour in neighbourhood if manhattan_dist(
                b, neighbour) == min_mh_dist])
            if crit:
                self._crit_edges.append([prev, cur])
            else:
                self._bon_edges.append([prev, cur])
            if cur == b:
                break
            x, y = cur
            if self.get(x, y).empty == True:
                self.set(x, y, Room(crit=crit))
        return self


def random_coord():
    return (randint(0, MAP_X_BOUND-1), randint(0, MAP_Y_BOUND-1))


def mst(map, crit, coords, connected=[]):
    if len(coords) == 0:
        return
    if len(connected) == 0:
        connected = [coords.pop()]
    min_coords = None
    min_coord_dist = float("inf")
    for u in connected:
        for v in coords:
            d = manhattan_dist(u, v)
            if d < min_coord_dist:
                min_coords = (u, v)
                min_coord_dist = d
    a, b = min_coords
    map.connect(a, b, crit)
    connected.append(b)
    coords.remove(b)
    mst(map, crit, coords, connected)


def generate_crit_path(map):
    base_coord = random_coord()
    crit_key_coords = [random_coord() for _ in range(
        randint(CRIT_KEYS_LOWER_BOUND, CRIT_KEYS_UPPER_BOUND))]
    base_x, base_y = base_coord
    map.set(base_x, base_y, Room(crit=True, base=True))
    for x, y in crit_key_coords:
        map.set(x, y, Room(crit=True))
    mst(map, True, [base_coord] + crit_key_coords)
    boss_coord = None
    non_empty = map.branchable()
    while True:
        boss_coord = random_coord()
        if boss_coord not in non_empty:
            break
    boss_x, boss_y = boss_coord
    map.set(boss_x, boss_y, Room(boss=True))
    mst(map, True, [boss_coord], non_empty)
    return map


def generate_rest(map):
    rc = randint(ROOMCOUNT_LOWER_BOUND, ROOMCOUNT_UPPER_BOUND)
    while map.count < rc:
        non_empty = map.branchable()
        x, y = random_coord()
        if (x, y) in non_empty:
            continue
        if map.get(x, y).empty == False:
            continue
        map.set(x, y, Room())
        mst(map, False, [(x, y)], non_empty)
    return map


def generate_map():
    map = Map()
    map = generate_crit_path(map)
    if map is None or map.count < CRIT_PATH_LEN_LOWER_BOUND and map.count > CRIT_PATH_LEN_UPPER_BOUND:
        return generate_map()
    map = generate_rest(map)
    return map


generated_map = generate_map()
print(generated_map.count)
generated_map.show()
