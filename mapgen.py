from enum import Enum
import numpy as np
from random import randint, choice as random_choice
import math
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import statistics

MAP_X_BOUND = 8
MAP_Y_BOUND = 8
CRIT_KEYS_LOWER_BOUND = int(0.75*MAP_X_BOUND)
CRIT_KEYS_UPPER_BOUND = MAP_X_BOUND
CRIT_PATH_LEN_LOWER_BOUND = CRIT_KEYS_LOWER_BOUND * 3 + 1
CRIT_PATH_LEN_UPPER_BOUND = CRIT_KEYS_UPPER_BOUND * 3 - 1
ROOMCOUNT_LOWER_BOUND = MAP_X_BOUND * (MAP_X_BOUND - 1) - 6
ROOMCOUNT_UPPER_BOUND = MAP_X_BOUND ** 2

NUM_ITERATIONS = 5000


def manhattan_dist(u, v):
    a, b = u
    c, d = v
    return int(math.fabs(a-c) + math.fabs(b-d))


def empty_map():
    map = []
    for _ in range(MAP_X_BOUND):
        row = []
        for _ in range(MAP_Y_BOUND):
            row.append(Room(empty=True))
        map.append(row)
    return map


def random_coord():
    return (randint(0, MAP_X_BOUND-1), randint(0, MAP_Y_BOUND-1))


class Room:
    def __init__(self, crit=False, empty=False, base=False, boss=False):
        self.crit = crit
        self.empty = empty
        self.base = base
        self.boss = boss


class Map:
    def __init__(self):
        self._map = empty_map()
        self.crit_edges = []
        self.bon_edges = []
        self.base = None
        self.boss = None

    def count(self):
        count = 0
        for row in self._map:
            for room in row:
                if room.empty == False:
                    count += 1
        return count

    def crit_coords(self):
        crit = []
        for x in range(len(self._map)):
            for y in range(len(self._map[x])):
                if self._map[x][y].crit == True:
                    crit.append((x, y))
        return crit

    def get(self, *coords):
        x, y = coords
        return self._map[x][y]

    def set(self, x, y, room):
        if room.base:
            self.base = (x, y)
        if room.boss:
            self.boss = (x, y)
        self._map[x][y] = room

    def _render(self):
        lc_crit = LineCollection(self.crit_edges, color='r')
        lc_bon = LineCollection(self.bon_edges, color='b')
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
                    circ = plt.Circle((x, y), radius=0.17,
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

    def neighbours(self, x, y):
        return [
            (x, y) for x, y in [
                (x+1, y),
                (x-1, y),
                (x, y+1),
                (x, y-1)
            ]
            if (x >= 0 and x < MAP_X_BOUND) and (y >= 0 and y < MAP_Y_BOUND)]

    # walk using mh distance as a heuristic
    # will not backtrack, so could throw an exception
    def walk(self, a, b, neighbour_test, cb=None):
        cur = a
        while cur != b:
            neighbourhood = [(x, y) for x, y in self.neighbours(
                *cur) if neighbour_test(x, y)]
            min_mh_dist = min(manhattan_dist(b, neighbour)
                              for neighbour in neighbourhood)
            prev = cur
            cur = random_choice([neighbour for neighbour in neighbourhood if manhattan_dist(
                b, neighbour) == min_mh_dist])
            if cb:
                cb(prev, cur)

    def connect(self, a, b, crit):
        def cb(prev, cur):
            if crit:
                self.crit_edges.append((prev, cur))
            else:
                self.bon_edges.append((prev, cur))
            x, y = cur
            if self.get(x, y).empty == True:
                self.set(x, y, Room(crit=crit))
        self.walk(a, b, lambda x, y: self.get(x, y).empty == True, cb)

    # assumes the map is connected
    def span(self, not_yet_connected=[], connected=None, crit=False):
        if connected is None:
            connected = self.branchable()
        if len(not_yet_connected) == 0:
            return
        if len(connected) == 0:
            connected = [not_yet_connected.pop(randint(0, len(connected)-1))]
        min_coords = None
        min_coord_dist = float("inf")
        for u in connected:
            for v in not_yet_connected:
                d = manhattan_dist(u, v)
                if d < min_coord_dist:
                    min_coords = (u, v)
                    min_coord_dist = d
        a, b = min_coords
        self.connect(a, b, crit)
        connected.append(b)
        not_yet_connected.remove(b)
        self.span(not_yet_connected, connected, crit)


def generate_map():
    try:
        map = Map()
        bossx, bossy = random_coord()
        map.set(bossx, bossy, Room(crit=True, boss=True))
        crit_rc = randint(CRIT_PATH_LEN_LOWER_BOUND,
                          CRIT_PATH_LEN_UPPER_BOUND)
        map.connect((bossx, bossy), random_coord(), crit=True)
        while map.count() < crit_rc:
            x, y = random_coord()
            if map.get(x, y).empty == True:
                map.span([(x, y)], crit=True)
        if map.count() > CRIT_PATH_LEN_UPPER_BOUND:
            return generate_map()
        rc = randint(ROOMCOUNT_LOWER_BOUND, ROOMCOUNT_UPPER_BOUND)
        while map.count() < rc:
            x, y = random_coord()
            if map.get(x, y).empty == True:
                map.span([(x, y)], crit=False)
        if map.count() > rc:
            return generate_map()
        basex, basey = random_choice(map.crit_coords())
        map.set(basex, basey, Room(crit=True, base=True))
        return map
    except:
        return generate_map()


def average_rc(maps):
    return statistics.mean(map.count() for map in maps)


def average_mh_dist_base_to_boss(maps):
    return statistics.mean(manhattan_dist(map.base, map.boss) for map in maps)


def base_matrix(maps):
    matrix = np.zeros((MAP_X_BOUND, MAP_Y_BOUND))
    for map in maps:
        x, y = map.base
        matrix[x][y] += 1
    for n, row in enumerate(matrix):
        for m, _ in enumerate(row):
            matrix[n][m] /= NUM_ITERATIONS
    return matrix


def boss_matrix(maps):
    matrix = np.zeros((MAP_X_BOUND, MAP_Y_BOUND))
    for map in maps:
        x, y = map.boss
        matrix[x][y] += 1
    for n, row in enumerate(matrix):
        for m, _ in enumerate(row):
            matrix[n][m] /= NUM_ITERATIONS
    return matrix


# generate_map().show()
print("generating maps...")
maps = [generate_map() for _ in range(NUM_ITERATIONS)]
print("calculating average rc...")
print("average roomcount=", average_rc(maps))
print("calculating base -> boss distance...")
print("average manhattan base -> boss distance=",
      average_mh_dist_base_to_boss(maps))
print("calculating base matrix...")
print("base matrix=")
print(base_matrix(maps))
print("calculating boss matrix...")
print("boss matrix=")
print(boss_matrix(maps))
