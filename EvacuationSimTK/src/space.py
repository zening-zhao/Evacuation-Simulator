import random
import math

import numpy as np
import pandas as pd
from PIL import Image

from pedestrian_evacuation.pedestrian import Pedestrian


class BaseSpace:
    def __init__(self, xlsx_path, pedestrian_number=100, configs={}):
        self.xlsx_path = xlsx_path
        self.pedestrian_number = pedestrian_number
        self.configs = configs

        self.waiting_locations = []
        self.measure_locations = []
        self.exit_locations = []
        self.exit_ids = []
        self.exit_id_locations = {}
        self.inject_locations = []
        self.inject_ids = []
        self.inject_id_locations = {}
        self.pedestrians = []
        self.in_space_pedestrian_number = 0
        self.already_inject_pedestrian_number = 0
        self.evacuated_pedestrian_number = 0
        self.color_map = {
            "obstacle": [61, 61, 61],
            "waiting": [211, 211, 211],
            "empty": [240, 240, 240],
            "measure": [240, 222, 173],
            "pedestrian": [51, 153, 255],
            "exit": [51, 204, 0],
            "inject": [220, 0, 0],
            "background": [255, 255, 255],
        }
        self.step_number = 0
        self.density_speeds = {}

        self.layout_pdframe = pd.read_excel(xlsx_path, header=None, index_col=None, dtype=float)
        self.layout_shape = self.layout_pdframe.shape
        self.layout = self.layout_pdframe.values.tolist()
        self.layout_backup = self.layout_pdframe.values.tolist()

        self.parse_locations()

    def parse_locations(self):
        for i in range(self.layout_shape[0]):
            for j in range(self.layout_shape[1]):
                data = self.layout[i][j]
                if data == 0:
                    self.waiting_locations.append((i, j))
                if data == 2:
                    self.measure_locations.append((i, j))
                elif  data >= 100 and data <= 199:
                    self.exit_locations.append((i, j))
                    self.exit_ids.append(data)
                    if data not in self.exit_id_locations:
                        self.exit_id_locations[data] = []
                    self.exit_id_locations[data].append((i,j))
                elif  data >= 200:
                    self.inject_locations.append((i, j))
                    self.inject_ids.append(data)
                    if data not in self.inject_id_locations:
                        self.inject_id_locations[data] = []
                    self.inject_id_locations[data].append((i,j))
                
        self.exit_ids = list(set(self.exit_ids))

    def init_pedestrian(self):
        if self.pedestrian_number > len(self.waiting_locations):
            raise ValueError(f"Max pedestrian number is {len(self.waiting_locations)}")

        pedestrian_locations = random.sample(
            self.waiting_locations, k=self.pedestrian_number
        )

        for i, loc in enumerate(pedestrian_locations):
            p = Pedestrian(str(i), 1.5, loc)
            self.pedestrians.append(p)
            self.layout[loc[0]][loc[1]] = p
            self.in_space_pedestrian_number += 1

    def step(self):
        raise NotImplementedError("the step() method needs to be implemented.")

    def location_is_avaiable(self, location):
        try:
            layout_data = self.layout[location[0]][location[1]]
        except IndexError:
            return False

        if isinstance(layout_data, float) and layout_data >= 0 and layout_data <= 199:
            return True
        else:
            return False

    def is_all_evacuated(self):
        if self.in_space_pedestrian_number <= 0:
            return True
        else:
            return False

    def get_current_layout_as_image(self):
        # convert data to pixel directly
        row, col = self.layout_shape
        image_data = np.zeros((row, col, 3), np.uint8)
        for i in range(self.layout_shape[0]):
            for j in range(self.layout_shape[1]):
                data = self.layout[i][j]
                color_type = self.get_data_color_type(data)
                image_data[i][j] = self.color_map[color_type]

        img = Image.fromarray(image_data)
        return img

    def get_data_color_type(self, data):
        if isinstance(data, float) and math.isnan(data):
            color_type = "background"
        elif isinstance(data, Pedestrian):
            color_type = "pedestrian"
        elif data == -1:
            color_type = "obstacle"
        elif data == 1:
            color_type = "empty"
        elif data == 0:
            color_type = "waiting"
        elif data == 2:
            color_type = "measure"
        elif data >= 100 and data <= 199:
            color_type = "exit"
        elif data >= 200:
            color_type = "inject"


        return color_type

    def get_current_layout_as_image_beautify(self):
        # add border around pedestrians
        img = self.get_current_layout_as_image()

        ratio = 8
        new_size = (img.size[0] * ratio, img.size[1] * ratio)
        img = img.resize(new_size, Image.Resampling.NEAREST)
        image_data = np.array(img)

        for p in self.pedestrians:
            if not p.in_space:
                continue
            row, col = p.current_location
            orig_data = self.layout_backup[row][col]
            color_type = self.get_data_color_type(orig_data)
            for i in range(ratio):
                image_data[row * ratio][col * ratio + i] = self.color_map[color_type]
                image_data[row * ratio + ratio - 1][col * ratio + i] = self.color_map[
                    color_type
                ]

            for i in range(ratio):
                image_data[row * ratio + i][col * ratio] = self.color_map[color_type]
                image_data[row * ratio + i][col * ratio + ratio - 1] = self.color_map[
                    color_type
                ]

        img = Image.fromarray(image_data)
        return img

    def save_data(self):
        with open("data/density_speed.csv", mode="a") as f:
            f.write(f"\n")
            for des, speeds in self.density_speeds.items():
                avg_speed = sum(speeds) / len(speeds)
                f.write(f"{des}, {avg_speed}\n")
            f.write(f"\n")


class RandomSpace(BaseSpace):
    def __init__(self, xlsx_path, pedestrian_number=100, configs={}):
        super().__init__(xlsx_path, pedestrian_number, configs)
        self.neighbor_type = self.configs["neighbor_type"]

    def step(self):
        area_ped_num = 0
        area_speed_total = 0

        if not self.is_all_evacuated():
            self.step_number += 1

        # move all pedestrians one by one
        for p in self.pedestrians:
            if p.in_space:
                row, col = p.current_location
                new_row, new_col = self.move_strategy((row, col), self.neighbor_type)
                p.move((new_row, new_col))

                if (row, col) != (new_row, new_col):
                    self.layout[row][col] = self.layout_backup[row][col]
                    data = self.layout[new_row][new_col]
                    if data >= 100 and data <= 199:
                        p.in_space = False
                        self.in_space_pedestrian_number -= 1
                        self.evacuated_pedestrian_number += 1
                    else:
                        self.layout[new_row][new_col] = p

                # density_speed
                if (new_row, new_col) in self.measure_locations:
                    area_ped_num += 1
                    distance = new_col - col
                    speed = distance
                    area_speed_total += speed

        if area_ped_num > 0:
            area_des = area_ped_num / 6
            area_speed = area_speed_total / area_ped_num

            ### collect density and speed
            if area_des not in self.density_speeds:
                self.density_speeds[area_des] = [area_speed]
            else:
                self.density_speeds[area_des].append(area_speed)

    def move_strategy(self, location, neighbor="moore"):
        if neighbor == "moore":
            op_choices = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        elif neighbor == "extended_moore":
            op_choices = [
                (-1, -1),
                (-1, 0),
                (-1, 1),
                (0, 1),
                (0, -1),
                (1, -1),
                (1, 0),
                (1, 1),
            ]
        else:
            raise ValueError(f"neighbor type {neighbor} not recognized")

        row, col = location
        op = random.choice(op_choices)
        new_location = (row + op[0], col + op[1])
        if self.location_is_avaiable(new_location):
            return new_location
        else:
            return location


class ShortestExitSpace(RandomSpace):
    """Try to move to the location which has the shortest distance to any exit in each step.
    """
    def move_strategy(self, location, neighbor="moore"):
        if neighbor == "moore":
            op_choices = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        elif neighbor == "extended_moore":
            op_choices = [
                (-1, -1),
                (-1, 0),
                (-1, 1),
                (0, 1),
                (0, -1),
                (1, -1),
                (1, 0),
                (1, 1),
            ]
        else:
            raise ValueError(f"neighbor type {neighbor} not recognized")

        # get min distance of current location to exit
        current_min_distance_to_exit = np.inf
        for exit_loc in self.exit_locations:
            row_diff = exit_loc[0] - location[0]
            col_diff = exit_loc[1] - location[1]
            # distance = np.linalg.norm((x_diff, y_diff))
            distance = row_diff**2 + col_diff**2
            if distance < current_min_distance_to_exit:
                current_min_distance_to_exit = distance

        # find if there is a new location which has smaller distance
        new_location = location
        for op in op_choices:
            for exit_loc in self.exit_locations:
                ped_loc = (location[0] + op[0], location[1] + op[1])
                if self.location_is_avaiable(ped_loc):
                    row_diff = exit_loc[0] - ped_loc[0]
                    col_diff = exit_loc[1] - ped_loc[1]
                    # distance = np.linalg.norm((x_diff, y_diff))
                    distance = row_diff**2 + col_diff**2
                    if distance < current_min_distance_to_exit:
                        current_min_distance_to_exit = distance
                        new_location = ped_loc

        return new_location


class ExpSpace(BaseSpace):
    def __init__(self, xlsx_path, pedestrian_number=100, configs={}):
        super().__init__(xlsx_path, pedestrian_number, configs)
        # use exit choice model every r time steps
        self.r = self.configs["r"]
        # subarea side length
        self.L = self.configs["L"]
        # params for exit choice model
        self.alpha = self.configs["alpha"]
        self.beta = self.configs["beta"]
        self.gamma = self.configs["gamma"]
        self.theta = self.configs["theta"]
        # params for pedestrian movement model
        self.epsilon = self.configs["epsilon"]
        self.delta = self.configs["delta"]
        self.phi = self.configs["phi"]

        self.selected_inject_id = self.configs["inject_id"]
        self.inject_prob_param = self.configs["inject_prob_param"]

    def step(self):
        if self.step_number == 0:
            self.initialize()

        if self.step_number % self.r == 0:
            self.exit_choice()
            # print(f"Exit choice [timestep {self.step_number}]: ")
            # for s_row in self.S:
            #     for s_col in self.S[s_row]:
            #         print(self.S[s_row][s_col]["optimal_exit"], end=" ")
            #     print()
            # print()

        self.pedestrian_movement()

        self.inject_pedestrian()
        
        if not self.is_all_evacuated():
            self.step_number += 1

    def initialize(self):
        # subarea dict, which include F_se, optimal_exit, locations ...
        self.S = {}
        # static potential
        self.l = {}

        self.init_subarea()
        self.compute_static_potential()

    def init_subarea(self):
        # divide the layout to coarse subarea
        for row in range(self.layout_shape[0]):
            for col in range(self.layout_shape[1]):
                S_row_idx = row // self.L
                S_col_idx = col // self.L
                if S_row_idx not in self.S:
                    self.S[S_row_idx] = {}
                if S_col_idx not in self.S[S_row_idx]:
                    self.S[S_row_idx][S_col_idx] = {"locations": []}
                self.S[S_row_idx][S_col_idx]["locations"].append((row, col))


    def compute_static_potential(self):
        # compute static potential
        for exit_id in self.exit_ids:
            ordered_sequence = []
            # step 1 and step 2
            for row in range(self.layout_shape[0]):
                for col in range(self.layout_shape[1]):
                    if row not in self.l:
                        self.l[row] = {}
                    if col not in self.l[row]:
                        self.l[row][col] = {}

                    element = self.layout[row][col]
                    if element == -1:
                        self.l[row][col][exit_id] = -1
                    elif isinstance(element, float) and math.isnan(element):
                        self.l[row][col][exit_id] = -1
                    elif isinstance(element, float) and element == exit_id:
                        self.l[row][col][exit_id] = 0
                        ordered_sequence.append([row, col])

            # step 3
            while not self.check_all_static_potential_calculated(exit_id):
                l_e_ij_seq = []
                for lattice in ordered_sequence:
                    l_e_ij_seq.append(self.l[lattice[0]][lattice[1]][exit_id])
                if len(ordered_sequence) == 0:
                    print(ordered_sequence)
                l_e_i0j0 = min(l_e_ij_seq)
                lattice_i0_j0 = ordered_sequence[l_e_ij_seq.index(l_e_i0j0)]
                ordered_sequence.remove(lattice_i0_j0)

                # step 3.1
                for direction in [[0, -1], [0, 1], [-1, 0], [1, 0]]:
                    lattice_i = lattice_i0_j0[0] + direction[0]
                    lattice_j = lattice_i0_j0[1] + direction[1]

                    if lattice_i in self.l and lattice_j in self.l[lattice_i]:
                        if exit_id not in self.l[lattice_i][lattice_j]:
                            l_e_ij = l_e_i0j0 + 1
                            self.l[lattice_i][lattice_j][exit_id] = l_e_ij
                            # step 4
                            ordered_sequence.append([lattice_i, lattice_j])

                # step 3.2
                for direction in [[-1, -1], [-1, 1], [1, -1], [1, 1]]:
                    lattice_i = lattice_i0_j0[0] + direction[0]
                    lattice_j = lattice_i0_j0[1] + direction[1]

                    if lattice_i in self.l and lattice_j in self.l[lattice_i]:
                        if exit_id not in self.l[lattice_i][lattice_j]:
                            l_e_ij = l_e_i0j0 + math.sqrt(2)
                            self.l[lattice_i][lattice_j][exit_id] = l_e_ij
                            # step 4
                            ordered_sequence.append([lattice_i, lattice_j])


    def check_all_static_potential_calculated(self, exit_id):
        for i in self.l:
            for j in self.l[i]:
                if exit_id not in self.l[i][j]:
                    return False
        return True


    def exit_choice(self):
        # K_s denotes pedestrian density of subarea s.
        # V_s denotes the average movement speed of the pedestrians of subarea s.
        for s_row in self.S:
            for s_col in self.S[s_row]:
                ped_number_in_subarea = 0
                for loc in self.S[s_row][s_col]["locations"]:
                    if isinstance(self.layout[loc[0]][loc[1]], Pedestrian):
                        ped_number_in_subarea += 1
                # compute K_s
                K_s = ped_number_in_subarea / (self.L * self.L)
                self.S[s_row][s_col]["K_s"] = K_s
                # Set V_s = 1.0
                V_s = 1.0
                self.S[s_row][s_col]["V_s"] = V_s
                self.S[s_row][s_col]["F_se"] = {}

        # compute F_se
        X_e = {}
        # step 1
        for s_row in self.S:
            for s_col in self.S[s_row]:
                K_s = self.S[s_row][s_col]["K_s"]
                V_s = self.S[s_row][s_col]["V_s"]
                for loc in self.S[s_row][s_col]["locations"]:
                    if (
                        isinstance(self.layout[loc[0]][loc[1]], float)
                        and self.layout[loc[0]][loc[1]] in self.exit_ids
                    ):
                        exit_id = self.layout[loc[0]][loc[1]]
                        F_se = (1 + self.beta * K_s) * (1 + self.gamma / V_s)
                        self.S[s_row][s_col]["F_se"][exit_id] = F_se
                        if exit_id not in X_e:
                            X_e[exit_id] = []
                        X_e[exit_id].append([s_row, s_col])
                        break

        # step_4
        while self.check_all_subarea_potential_calculated() == False:
            # step_2 and step_3
            for exit_id in X_e:
                # find smallest potential
                s_row_col_seq = X_e[exit_id]
                potentials = []
                for row_col in s_row_col_seq:
                    s_row, s_col = row_col
                    pot = self.S[s_row][s_col]["F_se"][exit_id]
                    potentials.append(pot)
                F_s0_e = min(potentials)
                s0_row_col = s_row_col_seq[potentials.index(F_s0_e)]
                X_e[exit_id].remove(s0_row_col)
                # step 2 (1)
                for direction in [[-1, -1], [-1, 1], [1, -1], [1, 1]]:
                    s_row = s0_row_col[0] + direction[0]
                    s_col = s0_row_col[1] + direction[1]

                    if s_row in self.S and s_col in self.S[s_row]:
                        if exit_id not in self.S[s_row][s_col]["F_se"]:
                            F_se = F_s0_e + (1 + self.alpha) * (1 + self.beta * K_s) * (1 + self.gamma / V_s)
                            self.S[s_row][s_col]["F_se"][exit_id] = F_se
                            # step 3
                            X_e[exit_id].append([s_row, s_col])

                # step 2 (2)
                for direction in [[0, -1], [0, 1], [-1, 0], [1, 0]]:
                    s_row = s0_row_col[0] + direction[0]
                    s_col = s0_row_col[1] + direction[1]

                    if s_row in self.S and s_col in self.S[s_row]:
                        if exit_id not in self.S[s_row][s_col]["F_se"]:
                            F_se = F_s0_e + (1 + self.beta * K_s) * (1 + self.gamma / V_s)
                            self.S[s_row][s_col]["F_se"][exit_id] = F_se
                            # step 3
                            X_e[exit_id].append([s_row, s_col])

        # step 5
        for s_row in self.S:
            for s_col in self.S[s_row]:
                potential_dict = self.S[s_row][s_col]["F_se"]
                exit_id = min(potential_dict, key=potential_dict.get)
                self.S[s_row][s_col]["temporary_exit"] = exit_id
                if "optimal_exit" not in self.S[s_row][s_col]:
                    self.S[s_row][s_col]["optimal_exit"] = exit_id
                else:
                    temporary_exit_id = self.S[s_row][s_col]["temporary_exit"]
                    F_s_e =  self.S[s_row][s_col]["F_se"][temporary_exit_id]
                    optimal_exit_id = self.S[s_row][s_col]["optimal_exit"]
                    F_s_e0 = self.S[s_row][s_col]["F_se"][optimal_exit_id]
                    if F_s_e0 - F_s_e > self.theta:
                        self.S[s_row][s_col]["optimal_exit"] = temporary_exit_id

    def check_all_subarea_potential_calculated(self):
        for s_row in self.S:
            for s_col in self.S[s_row]:
                if "F_se" not in self.S[s_row][s_col]:
                    return False
                F_se_exits = set(self.S[s_row][s_col]["F_se"].keys())
                if F_se_exits != set(self.exit_ids):
                    return False
        return True

    def pedestrian_movement(self):
        area_ped_num = 0
        area_speed_total = 0
    
        for p in self.pedestrians:
            if p.in_space:
                i0, j0 = p.current_location
                s_row = i0 // self.L
                s_col = j0 // self.L
                exit_id = self.S[s_row][s_col]["optimal_exit"]
                l_e_i0j0 = self.l[i0][j0][exit_id]
                a_ij_seq = []
                f_e_ij_seq = []
                
                for direction in [[0, -1], [0, 1], [-1, 0], [1, 0]]:
                    i = i0 + direction[0]
                    j = j0 + direction[1]
                    if self.location_is_avaiable([i,j]):
                        a_ij_seq.append(1)
                    else:
                        a_ij_seq.append(0)
                    l_e_ij = self.l[i][j][exit_id]        
                    o_ij = self.compute_o_ij([i,j])
                    n_ij = 4
                    # equation (5)
                    f_e_ij = self.delta*o_ij/n_ij + self.phi*(l_e_ij-l_e_i0j0)
                    f_e_ij_seq.append(f_e_ij)
                
                # equation (4)
                probs = []
                for i in range(len(a_ij_seq)):
                    a_ij = a_ij_seq[i]
                    f_e_ij = f_e_ij_seq[i]
                    prob = math.exp(-1*self.epsilon*f_e_ij)*a_ij
                    probs.append(prob)

                prob_sum = sum(probs)
                if prob_sum != 0:
                    probs = np.array(probs)
                    probs = probs / prob_sum

                    direction = random.choices([[0, -1], [0, 1], [-1, 0], [1, 0]], probs)[0]
                    row, col = p.current_location
                    new_row = row + direction[0]
                    new_col = col + direction[1]
                    
                    if self.location_is_avaiable([new_row, new_col]):
                        p.move([new_row, new_col])
                        self.layout[row][col] = self.layout_backup[row][col]
                        data = self.layout[new_row][new_col]
                        if data >= 100 and data <= 199:
                            p.in_space = False
                            self.in_space_pedestrian_number -= 1
                            self.evacuated_pedestrian_number += 1
                        else:
                            self.layout[new_row][new_col] = p
                
                    # density_speed
                    if (new_row, new_col) in self.measure_locations:
                        area_ped_num += 1
                        distance = new_col - col
                        speed = distance
                        area_speed_total += speed
        
        if area_ped_num > 0:
            area_des = area_ped_num / 6
            area_speed = area_speed_total / area_ped_num

            ### collect density and speed
            if area_des not in self.density_speeds:
                self.density_speeds[area_des] = [area_speed]
            else:
                self.density_speeds[area_des].append(area_speed)

                
    def compute_o_ij(self, location):
        o_ij = 0
        for direction in [[0, -1], [0, 1], [-1, 0], [1, 0]]:
            i = location[0] + direction[0]
            j = location[1] + direction[1]
            if not self.location_is_avaiable([i,j]):
                o_ij += 1
        return o_ij

    def inject_pedestrian(self):
        if self.selected_inject_id == None:
            self.selected_inject_id = random.choice(self.inject_ids)
        if self.already_inject_pedestrian_number < self.configs["inject_number"]:
            inject_locations = self.inject_id_locations[self.selected_inject_id]
            for loc in inject_locations:
                if random.uniform(0, 1) > self.inject_prob_param and self.already_inject_pedestrian_number < self.configs["inject_number"]:
                    inject_pedestrian = Pedestrian(f"{self.selected_inject_id}", 1.5, loc)
                    self.pedestrians.append(inject_pedestrian)
                    self.already_inject_pedestrian_number += 1
                    self.in_space_pedestrian_number += 1


class RandomExitSpace(BaseSpace):
    """Select an exit at start, then try to move to it.
    """
    def __init__(self, xlsx_path, pedestrian_number=100, configs={}):
        super().__init__(xlsx_path, pedestrian_number, configs)
        self.neighbor_type = self.configs["neighbor_type"]

    def step(self):

        if not self.is_all_evacuated():
            self.step_number += 1

        # move all pedestrians one by one
        for p in self.pedestrians:
            if p.in_space:
                row, col = p.current_location
                if not hasattr(p, "target_exit"):
                    p.target_exit = random.choice(self.exit_ids)
                new_row, new_col = self.move_strategy(p, self.neighbor_type)
                p.move((new_row, new_col))

                if (row, col) != (new_row, new_col):
                    self.layout[row][col] = self.layout_backup[row][col]
                    data = self.layout[new_row][new_col]
                    if data >= 100 and data <= 199:
                        p.in_space = False
                        self.in_space_pedestrian_number -= 1
                        self.evacuated_pedestrian_number += 1
                    else:
                        self.layout[new_row][new_col] = p

    def move_strategy(self, pedestrian, neighbor="moore"):
        if neighbor == "moore":
            op_choices = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        elif neighbor == "extended_moore":
            op_choices = [
                (-1, -1),
                (-1, 0),
                (-1, 1),
                (0, 1),
                (0, -1),
                (1, -1),
                (1, 0),
                (1, 1),
            ]
        else:
            raise ValueError(f"neighbor type {neighbor} not recognized")

        location = pedestrian.current_location
        exit_loc = self.exit_id_locations[pedestrian.target_exit][0]
        new_location = location
        current_min_distance_to_exit = np.inf
        for op in op_choices:
            ped_loc = (location[0] + op[0], location[1] + op[1])
            if self.location_is_avaiable(ped_loc):
                row_diff = exit_loc[0] - ped_loc[0]
                col_diff = exit_loc[1] - ped_loc[1]
                # distance = np.linalg.norm((x_diff, y_diff))
                distance = row_diff**2 + col_diff**2
                if distance < current_min_distance_to_exit:
                    current_min_distance_to_exit = distance
                    new_location = ped_loc

        return new_location



if __name__ == "__main__":
    space = BaseSpace("data/test_large.xlsx")
