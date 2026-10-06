import unittest

from api.models2 import PreGameData
from divide_agent_type.car_divide import divide_car_kinds, divide_initial_agents


class CarDivideTests(unittest.TestCase):
    def data(self, agents, spots, width=10, cells=None):
        if cells is None:
            cells = [[0] * width for _ in range(max(agents + spots + [0]) // width + 1)]
        return PreGameData({
            "map": {"width": width, "height": len(cells), "cells": cells}, "agents": agents,
            "spots": [{"pos": pos} for pos in spots],
        })

    def test_single_supply_car_for_every_nonempty_fleet(self):
        for count in range(8):
            with self.subTest(count=count):
                kinds = divide_car_kinds(count)
                self.assertEqual(kinds.count(0), max(0, count - 1))
                self.assertEqual(kinds.count(1), min(1, count))

    def test_nearest_agents_selected_without_reordering_ids(self):
        self.assertEqual(divide_initial_agents(
            self.data([9, 1, 8, 2], [0]))['kinds'], [1, 0, 0, 0])
        self.assertEqual(divide_initial_agents(
            self.data([9, 1, 8, 2, 3], [0]))['kinds'], [1, 0, 0, 0, 0])

    def test_nearest_of_all_spots_and_ties_use_agent_id(self):
        self.assertEqual(divide_initial_agents(
            self.data([4, 8, 1, 5], [0, 9]))['kinds'], [0, 0, 0, 1])

    def test_odd_row_hex_distance(self):
        # pos 4 is diagonally adjacent to pos 1, just like pos 0.
        # Their tie is resolved by agent ID rather than rectangular distance.
        self.assertEqual(divide_initial_agents(
            self.data([4, 0], [1], width=3))['kinds'], [0, 1])

    def test_lake_blocks_geometrically_closest_agent(self):
        self.assertEqual(divide_initial_agents(
            self.data([0, 5], [2], width=6,
                      cells=[[0, 3, 0, 0, 0, 0]]))['kinds'], [1, 0])

    def test_road_steps_beat_shorter_hill_route(self):
        # 左の車は2マスでも丘からの移動に6step、右は3マスで3step。
        self.assertEqual(divide_initial_agents(
            self.data([0, 5], [2], width=6,
                      cells=[[2, 2, 0, 1, 1, 1]]))['kinds'], [1, 0])

    def test_unreachable_tie_preserves_required_counts(self):
        self.assertEqual(divide_initial_agents(
            self.data([0, 4, 5], [2], width=6,
                      cells=[[0, 3, 0, 3, 0, 0]]))['kinds'], [0, 0, 1])

    def test_no_spots_falls_back_to_id_order(self):
        self.assertEqual(divide_initial_agents(
            self.data([3, 1, 2], []))['kinds'], [0, 0, 1])


if __name__ == '__main__':
    unittest.main()
