import json
from threading import Thread
import time
from tkinter import filedialog as fd
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

from pedestrian_evacuation.space import RandomSpace
from pedestrian_evacuation.space import ShortestExitSpace
from pedestrian_evacuation.space import ExpSpace
from pedestrian_evacuation.space import RandomExitSpace


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Pedestrian Evacuation Simulator")
        self.geometry("1000x600")
        # self.center_window()
        self.init_gui()
        self.disable_frame(self.config_frame)
        self.state("zoomed")

        self.configs = None
        self.sim = None
        self.sim_running = False
        self.sim_img = None
        self.sim_step_thread = None

    def init_gui(self):
        self.bind("<Configure>", self.on_window_resized)

        self.grid_columnconfigure(0, minsize=200)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, minsize=50)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, minsize=20)

        # top
        self.top_frame = tk.Frame(self, bg="#8c8c8c")
        self.top_frame.grid(row=0, column=0, sticky="nswe", columnspan=2)
        self.title = tk.Label(
            self.top_frame,
            text="Pedestrian Evacuation Simulator",
            font=("Arial", 24, "bold"),
            background="#8c8c8c",
            foreground="white",
        )
        self.title.grid(row=0, column=0, padx=20, pady=10)

        # left
        self.left_frame = tk.Frame(self)
        self.left_frame.grid(row=1, column=0, padx=0, pady=0, sticky="nswe")
        self.left_frame.grid_rowconfigure(2, weight=1)

        self.btn_load_config = ttk.Button(
            self.left_frame,
            text="Load Configuration",
            command=self.btn_load_config_callback,
        )
        self.btn_load_config.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")

        self.btn_save_config = ttk.Button(
            self.left_frame, text="Save Configuration", command=self.btn_save_config_callback
        )
        self.btn_save_config.grid(row=1, column=0, padx=10, pady=(0, 5), sticky="ew")

        # left-config
        self.config_frame = tk.Frame(self.left_frame)
        self.config_frame.grid(row=2, column=0, sticky="nsew")

        self.layout_path_label = tk.Label(
            self.config_frame,
            text="Layout Path:",
            font=("Microsoft Yahei", 8),
        )
        self.layout_path_label.grid(row=2, column=0, padx=(10, 0), pady=5)

        self.layout_path_var = tk.StringVar()
        self.layout_path = ttk.Entry(
            self.config_frame, textvariable=self.layout_path_var, width=5
        )
        self.layout_path.grid(row=2, column=1, pady=5, padx=10, sticky="ew")

        self.pedestrian_nbumber_label = tk.Label(
            self.config_frame, text="Number of Pedestrian:", font=("Microsoft Yahei", 8)
        )
        self.pedestrian_nbumber_label.grid(row=3, column=0, padx=(10, 0), pady=5)
        self.pedestrian_number_var = tk.IntVar()
        self.pedestrian_number = ttk.Spinbox(
            self.config_frame, to=100, textvariable=self.pedestrian_number_var, width=15
        )
        self.pedestrian_number.grid(row=3, column=1, pady=5, padx=10, sticky="ew")

        self.strategy_label = tk.Label(
            self.config_frame, text="Evacuation Strategy:", font=("Microsoft Yahei", 8)
        )
        self.strategy_label.grid(row=4, column=0, padx=(10, 0), pady=5)
        self.strategy_var = tk.StringVar()
        self.strategy = ttk.Combobox(
            self.config_frame,
            state="readonly",
            values=["random", "shortest_exit", "exp", "random_exit"],
            textvariable=self.strategy_var,
            width=10,
        )
        self.strategy.grid(row=4, column=1, pady=5, padx=10, sticky="ew")

        self.simulation_interval_label = tk.Label(
            self.config_frame, text="Simulation Interval (ms):", font=("Microsoft Yahei", 8)
        )
        self.simulation_interval_label.grid(row=5, column=0, padx=(10, 0), pady=5)
        self.simulation_interval_var = tk.IntVar(value=10)
        self.simulation_interval = ttk.Spinbox(
            self.config_frame,
            from_=10,
            to=10000,
            textvariable=self.simulation_interval_var,
            width=10,
        )
        self.simulation_interval.grid(row=5, column=1, pady=5, padx=10, sticky="ew")

        # left-sim-control
        self.sim_control_frame = tk.Frame(self.left_frame)
        self.sim_control_frame.grid(
            row=3, column=0, padx=0, pady=0, ipady=2, sticky="nsew"
        )
        self.sim_control_frame.grid_columnconfigure(0, weight=1)

        self.sep = ttk.Separator(self.sim_control_frame)
        self.sep.grid(row=0, column=0, sticky="nsew", pady=5)

        self.btn_init_sim = ttk.Button(
            self.sim_control_frame,
            text="Initialize Simulation",
            command=self.btn_init_sim_callback,
        )
        self.btn_init_sim.grid(row=1, column=0, padx=5, pady=5, sticky="we")
        self.btn_init_sim["state"] = tk.DISABLED
        self.btn_start_sim = ttk.Button(
            self.sim_control_frame, text="Start Simulation", command=self.btn_start_sim_callback
        )
        self.btn_start_sim.grid(row=2, column=0, padx=5, pady=5, sticky="we")
        self.btn_start_sim["state"] = tk.DISABLED
        self.btn_pause_sim = ttk.Button(
            self.sim_control_frame, text="Pause Simulation", command=self.btn_pause_sim_callback
        )
        self.btn_pause_sim.grid(row=3, column=0, padx=5, pady=5, sticky="we")
        self.btn_pause_sim["state"] = tk.DISABLED
        self.btn_stop_sim = ttk.Button(
            self.sim_control_frame, text="Stop Simulation", command=self.btn_stop_sim_callback
        )
        self.btn_stop_sim.grid(row=4, column=0, padx=5, pady=5, sticky="we")
        self.btn_stop_sim["state"] = tk.DISABLED

        # right
        self.right_frame = ttk.Frame(self)
        self.right_frame.grid(row=1, column=1, sticky="nswe")
        self.right_frame.grid_rowconfigure(0, weight=1)
        self.right_frame.grid_columnconfigure(0, weight=1)
        self.photo_img = None
        self.label = ttk.Label(self.right_frame, background="white", anchor="center")
        self.label.grid(row=0, column=0, sticky="nswe")

        # bottom
        self.bottom_frame = tk.Frame(self, background="#8c8c8c")
        self.bottom_frame.grid(
            row=2, column=0, padx=0, pady=0, sticky="nsew", columnspan=2
        )
        self.status = tk.Label(
            self.bottom_frame,
            text="Simulator Launch Successed",
            font=("Microsoft Yahei", 8),
            background="#8c8c8c",
            foreground="white",
        )
        self.status.grid(row=0, column=0, padx=5, pady=1, sticky="nswe")

    def center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

    def enable_frame(self, frame):
        for child in frame.winfo_children():
            child.configure(state="normal")

    def disable_frame(self, frame):
        for child in frame.winfo_children():
            child.configure(state="disable")

    def update_config(self):
        try:
            self.configs["layout_filename"] = self.layout_path_var.get()
            self.configs["number_of_pedstrians"] = self.pedestrian_number_var.get()
            self.configs["strategy"] = self.strategy_var.get()
            self.configs["simulation_interval"] = self.simulation_interval_var.get()

            for c in self.configs.values():
                if c == "":
                    raise ValueError("Error identified in Configuration Item...")
        except:
            raise ValueError("Error identified in Configuration Item...")

    def btn_load_config_callback(self):
        # print("load config")
        config_filename = fd.askopenfilename(filetypes=[("Configuration File", "*.json")])
        try:
            with open(config_filename) as f:
                self.configs = json.load(f)
            if "layout_filename" in self.configs:
                self.layout_path_var.set(self.configs["layout_filename"])
            if "number_of_pedstrians" in self.configs:
                self.pedestrian_number_var.set(self.configs["number_of_pedstrians"])
            if "strategy" in self.configs:
                self.strategy_var.set(self.configs["strategy"])
            if "simulation_interval" in self.configs:
                self.simulation_interval_var.set(self.configs["simulation_interval"])

            self.btn_init_sim["state"] = tk.NORMAL
            self.enable_frame(self.config_frame)
            self.btn_init_sim_callback()
            self.enable_frame(self.config_frame)
        except Exception as e:
            self.status.configure(text=e)

    def btn_save_config_callback(self):
        try:
            self.update_config()
            config_filename = fd.asksaveasfilename(filetypes=[("Configuration File", "*.json")])
            with open(config_filename, "w") as f:
                json.dump(self.configs, f, indent=2)
            self.status.configure(text=f"Configuration File Successfully Saved to {config_filename}")
        except Exception as e:
            self.status.configure(text=e)

    def btn_init_sim_callback(self):
        # print("init_sim")
        try:
            self.update_config()
            if self.configs["strategy"] == "random":
                self.sim = RandomSpace(
                    self.configs["layout_filename"],
                    self.configs["number_of_pedstrians"],
                    self.configs
                )
            elif self.configs["strategy"] == "shortest_exit":
                self.sim = ShortestExitSpace(
                    self.configs["layout_filename"],
                    self.configs["number_of_pedstrians"],
                    self.configs
                )
            elif self.configs["strategy"] == "exp":
                self.sim = ExpSpace(
                    self.configs["layout_filename"],
                    self.configs["number_of_pedstrians"],
                    self.configs
                )
            elif self.configs["strategy"] == "random_exit":
                self.sim = RandomExitSpace(
                    self.configs["layout_filename"],
                    self.configs["number_of_pedstrians"],
                    self.configs
                )
            self.sim.init_pedestrian()
            self.sim_img = self.sim.get_current_layout_as_image_beautify()
            new_size = self.get_sim_image_size(self.sim_img.size)
            img = self.sim_img.resize(new_size, Image.Resampling.NEAREST)
            self.photo_img = ImageTk.PhotoImage(image=img)
            self.label.configure(image=self.photo_img)
            self.pedestrian_number.configure(to=len(self.sim.waiting_locations))
            self.status.configure(text=f"Initialization Successed. Layout Size is : {self.sim.layout_shape}")
            self.btn_start_sim["state"] = tk.NORMAL
            self.btn_stop_sim["state"] = tk.DISABLED
        except Exception as e:
            self.status.configure(text=e)

    def btn_start_sim_callback(self):
        # print("start_sim")
        self.btn_load_config["state"] = tk.DISABLED
        self.btn_save_config["state"] = tk.DISABLED
        self.btn_init_sim["state"] = tk.DISABLED
        self.btn_start_sim["state"] = tk.DISABLED
        self.btn_pause_sim["state"] = tk.NORMAL
        self.btn_stop_sim["state"] = tk.NORMAL
        self.disable_frame(self.config_frame)

        self.sim_running = True
        # self.run_one_sim_step()
        self.run_one_sim_step_thread()

    def btn_pause_sim_callback(self):
        # print("pause sim")
        self.btn_load_config["state"] = tk.DISABLED
        self.btn_init_sim["state"] = tk.DISABLED
        self.btn_start_sim["state"] = tk.NORMAL
        self.btn_pause_sim["state"] = tk.DISABLED
        self.btn_stop_sim["state"] = tk.NORMAL

        self.sim_running = False

    def btn_stop_sim_callback(self):
        # print("stop sim")
        self.btn_load_config["state"] = tk.NORMAL
        self.btn_save_config["state"] = tk.NORMAL
        self.btn_init_sim["state"] = tk.NORMAL
        self.btn_start_sim["state"] = tk.DISABLED
        self.btn_pause_sim["state"] = tk.DISABLED
        self.btn_stop_sim["state"] = tk.DISABLED

        self.enable_frame(self.config_frame)

        self.sim_running = False

    def run_one_sim_step_thread(self):
        if self.sim_step_thread is None:
            self.sim_step_thread = Thread(target=self.sim.step, daemon=True)
            self.sim_step_thread.start()

        if self.sim_step_thread.is_alive():
            # print("alive")
            self.label.after(
                self.configs["simulation_interval"], self.run_one_sim_step_thread
            )
            self.status.configure(
                text=f"Current Executing Step is : {self.sim.step_number}, Number of Pedestrian Evacuated : {self.sim.evacuated_pedestrian_number}"
            )
        else:
            # print("not alive")
            self.sim_step_thread = None
            self.sim_img = self.sim.get_current_layout_as_image_beautify()
            new_size = self.get_sim_image_size(self.sim_img.size)
            img = self.sim_img.resize(new_size, Image.Resampling.NEAREST)
            self.photo_img = ImageTk.PhotoImage(image=img)
            self.label.configure(image=self.photo_img)
            if self.sim_running:
                if not self.sim.is_all_evacuated():
                    self.label.after(
                        self.configs["simulation_interval"],
                        self.run_one_sim_step_thread,
                    )
                    self.status.configure(
                        text=f"Current Executing Step is : {self.sim.step_number}, Number of Pedestrian Evacuated : {self.sim.evacuated_pedestrian_number}"
                    )
                else:
                    self.sim.save_data()
                    self.status.configure(
                        text=f"Simulation Completed. Total steps Executed : {self.sim.step_number}, Number of Pedestrian Evacuated : {self.sim.evacuated_pedestrian_number}"
                    )
                    self.btn_stop_sim_callback()

    def run_one_sim_step(self):
        # this will freeze gui
        self.sim.step()
        self.sim_img = self.sim.get_current_layout_as_image_beautify()
        new_size = self.get_sim_image_size(self.sim_img.size)
        img = self.sim_img.resize(new_size, Image.Resampling.NEAREST)
        self.photo_img = ImageTk.PhotoImage(image=img)
        self.label.configure(image=self.photo_img)

        self.status.configure(
            text=f"Current Executing Step is : {self.sim.step_number}, Number of Pedestrian Evacuated : {self.sim.evacuated_pedestrian_number}"
        )

        if self.sim_running:
            if not self.sim.is_all_evacuated():
                self.label.after(
                    self.configs["simulation_interval"], self.run_one_sim_step
                )
                self.status.configure(
                    text=f"Current Executing Step is : {self.sim.step_number}, Number of Pedestrian Evacuated : {self.sim.evacuated_pedestrian_number}"
                )
            else:
                self.sim.save_data()
                self.status.configure(text=f"Simulation Completed. Total steps Executed : {self.sim.step_number}, Number of Pedestrian Evacuated : {self.sim.evacuated_pedestrian_number}")
                self.btn_stop_sim_callback()

    def get_sim_image_size(self, img_size):
        label_width = self.label.winfo_width()
        label_height = self.label.winfo_height()
        img_width, img_height = img_size

        width_ratio = label_width / img_width

        height_ratio = label_height / img_height

        scale_ratio = min(width_ratio, height_ratio)
        scale_ratio *= 0.9

        new_width = img_width * scale_ratio
        new_height = img_height * scale_ratio

        return (int(new_width), int(new_height))

    def on_window_resized(self, event):
        if self.sim_img is not None:
            new_size = self.get_sim_image_size(self.sim_img.size)
            img = self.sim_img.resize(new_size, Image.Resampling.NEAREST)
            self.photo_img = ImageTk.PhotoImage(image=img)
            self.label.configure(image=self.photo_img)


def main():
    app = App()
    app.mainloop()
