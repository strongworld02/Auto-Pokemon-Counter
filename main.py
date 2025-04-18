from tkinter import font
from PIL import ImageGrab as ig
from PIL import ImageTk
from pynput.keyboard import Key
from pynput import keyboard
import os.path
import numpy as np
import time
import tkinter as tk
from tkinter import ttk
import threading

from config import Config
from SoundPlayer import SoundPlayer

# Make application on windows resulution aware.
# If resolution is scaled then it would be blurry without this.
try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except:
    pass

config_file_name: str = "encounter_counter.config"
counter_file_name: str = "counter.txt"

selected_color: list[int] = None
preview_width: int = 640
preview_height: int = 360
preview_refresh_delay: int = 2000

counter: float = 0
show_preview: bool = True
exit_script: bool = True
defining_color: bool = False
is_on_encounter: bool = False
sample_area_selector_active: bool = False
post_double_click: bool = False
move_mode: bool = False

sample_select_drag_start: tuple | None = None
last_drag_position: tuple | None = None
ctrl_pressed: bool = False

config: Config = None
sound: SoundPlayer = SoundPlayer()
resize_thread: threading.Thread = None

def on_press(key):
    global exit_script
    global config
    global counter
    global ctrl_pressed
    global defining_color
    global move_mode
    global sample_area_selector_active

    if (key == Key.ctrl or key == Key.ctrl_l or key == Key.ctrl_r):
        ctrl_pressed = True
        return
    
    if key == Key.esc:
        if sample_area_selector_active:
            complete_sample_area_selection()
        elif move_mode:
            toggle_move(False)
        if not exit_script:
            disable_encounter_check()
        if defining_color:
            stop_define_custom_color(False)
        return
    
    if defining_color:
        if key == Key.space:
            stop_define_custom_color(True)
            return

    if sample_area_selector_active:
        if (not move_mode):
            if key == Key.up:
                if ctrl_pressed:
                    config.modify_sample_bounding_box(config.Border.BOTTOM, -1, False)
                else:
                    config.modify_sample_bounding_box(config.Border.TOP, 1, False)
                return
            elif key == Key.down:
                if ctrl_pressed:
                    config.modify_sample_bounding_box(config.Border.TOP, -1, False)
                else:
                    config.modify_sample_bounding_box(config.Border.BOTTOM, 1, False)
                return
            elif key == Key.left:
                if ctrl_pressed:
                    config.modify_sample_bounding_box(config.Border.RIGHT, -1, False)
                else:
                    config.modify_sample_bounding_box(config.Border.LEFT, 1, False)
                return
            elif key == Key.right:
                if ctrl_pressed:
                    config.modify_sample_bounding_box(config.Border.LEFT, -1, False)
                else:
                    config.modify_sample_bounding_box(config.Border.RIGHT, 1, False)
                return
        try:
            if key.char == 'r':
                config.set_sample_default(False)
                return
        except AttributeError:
            pass

    if move_mode:
        if key == Key.up:
            if sample_area_selector_active:
                config.move_sample_area(0, -5 if ctrl_pressed else -1, False)
            else:
                config.move_view(0, -5 if ctrl_pressed else -1, False)
            return
        elif key == Key.down:
            if sample_area_selector_active:
                config.move_sample_area(0, 5 if ctrl_pressed else 1, False)
            else:
                config.move_view(0, 5 if ctrl_pressed else 1, False)
            return
        elif key == Key.left:
            if sample_area_selector_active:
                config.move_sample_area(-5 if ctrl_pressed else -1, 0, False)
            else:
                config.move_view(-5 if ctrl_pressed else -1, 0, False)
            return
        elif key == Key.right:
            if sample_area_selector_active:
                config.move_sample_area(5 if ctrl_pressed else 1, 0, False)
            else:
                config.move_view(5 if ctrl_pressed else 1, 0, False)
            return

    if exit_script:
        try:
            if key.char == '^' and check_routine_btn["state"] != "disabled":
                enable_encounter_check()
        except AttributeError:
            pass
    else:
        try:
            if key.char == '+':
                update_counter(counter + 1)
            elif key.char == '-':
                update_counter(counter - 1)
        except AttributeError:
            pass

def on_release(key):
    global ctrl_pressed
    if (key == Key.ctrl or key == Key.ctrl_l or key == Key.ctrl_r):
        ctrl_pressed = False

def update_counter(value: int | float):
    global counter
    f = open(counter_file_name, "w")
    if type(value) is float:
        if value.is_integer():
            value = int(value)
        elif (value % 1) > 0.9:
            value = round(value)
        else:
            value = round(value, 2)
    counter = value
    f.write(str(value))
    f.close()

def read_counter() -> float:
    f = open(counter_file_name, "r")
    value = float(f.read())
    f.close()
    return value

def is_predefined_color(average_color: list[int]) -> bool:
    if (selected_color == None):
        return False
    if (average_color[0] >= selected_color[0] - 2 and average_color[0] <= selected_color[0] + 2 and
        average_color[1] >= selected_color[1] - 2 and average_color[1] <= selected_color[1] + 2 and
        average_color[2] >= selected_color[2] - 2 and average_color[2] <= selected_color[2] + 2):
        return True
    else:
        return False

def grab_average_color() -> list[int]:
    screenshot = np.array(ig.grab(config.sample_bounding_box(), all_screens=True))
    average_color_row = np.average(screenshot, axis=0)
    average_color = np.average(average_color_row, axis=0).tolist()
    return [round(x) for x in average_color]

def check_screen_routine():
    global is_on_encounter
    global config
    global counter
    
    if (selected_color == None):
        return
    
    while(not exit_script):
        average_color = grab_average_color()
        if (not is_on_encounter):
            if (is_predefined_color(average_color)):
                update_counter(counter + config.step_size())
                is_on_encounter = True
        else:
            if (not is_predefined_color(average_color)):
                is_on_encounter = False
        time.sleep(0.35)


key_listener = keyboard.Listener(
    on_press=on_press,
    on_release=on_release
)
key_listener.start()

counter = 0
if not os.path.exists(counter_file_name):
    update_counter(counter)
else:
    counter = read_counter()

root= tk.Tk()
root.title("Encounter counter")

step_size_frame = tk.Frame(root)
pic_frame = tk.Frame(root)
color_selection_frame = tk.Frame(root)
preview_label_frame = tk.Frame(pic_frame, width=preview_width, height=preview_height)
preview_label_frame.grid_propagate(0)

def change_step_size(modifier):
    if (config.step_size() <= 1):
        if (modifier < 0):
            match config.step_size():
                case 1:
                    modifier = -0.5
                case 0.5:
                    modifier = -0.17
                case 0.33:
                    modifier = -0.08
                case 0.25:
                    modifier = -0.05
                case 0.2:
                    return
        elif (modifier > 0):
            match config.step_size():
                case 0.5:
                    modifier = 0.5
                case 0.33:
                    modifier = 0.17
                case 0.25:
                    modifier = 0.08
                case 0.2:
                    modifier = 0.05
    
    if (modifier != 0):
        config.set_step_size(config.step_size() + modifier)
        
    step_size = config.step_size()
    if step_size.is_integer():
        step_size = int(step_size)
    
    step_size_label_text = step_size
    match step_size:
        case 0.5:
            step_size_label_text = "1/2"
        case 0.33:
            step_size_label_text = "1/3"
        case 0.25:
            step_size_label_text = "1/4"
        case 0.2:
            step_size_label_text = "1/5"
    step_size_label.configure(text=step_size_label_text)

def update_preview():
    global config
    global move_mode
    global preview_height
    global preview_refresh_delay
    global preview_width
    global show_preview
    global sample_area_selector_active
    if not show_preview or config.bounding_box() == None:
        return False
    img2 = ig.grab(config.bounding_box(), all_screens=True)
    if (sample_area_selector_active or move_mode):
        sample_b_box = config.sample_bounding_box()
        bounding_box = config.bounding_box()
        sample_b_box = (sample_b_box[0] - bounding_box[0], sample_b_box[1] - bounding_box[1],
                        sample_b_box[2] - bounding_box[0], sample_b_box[3] - bounding_box[1])
        bounding_box = (0, 0, bounding_box[2] - bounding_box[0], bounding_box[3] - bounding_box[1])

        pixels = img2.load()
        pixelColor = None
        if sample_area_selector_active:
            pixelColor = (255, 127 if move_mode else 0, 127 if move_mode else 0)
        else:
            pixelColor = (46, 201, 132)
        for i in range(img2.size[0]):
            for j in range(img2.size[1]):
                if (((i == sample_b_box[0] or i == sample_b_box[2]) and j >= sample_b_box[1] and j <= sample_b_box[3]) or
                    ((j == sample_b_box[1] or j == sample_b_box[3]) and i >= sample_b_box[0] and i <= sample_b_box[2])):
                    pixels[i, j] = pixelColor
    img2.thumbnail((preview_width, preview_height))
    img2 = ImageTk.PhotoImage(img2)
    preview_label.configure(image=img2)
    preview_label.image = img2
    root.after(preview_refresh_delay, update_preview)

def toggle_preview():
    global show_preview
    if show_preview:
        show_preview = False
        preview_label.configure(image="")
    else:
        show_preview = True
        update_preview()

def enable_encounter_check():
    global exit_script
    if exit_script and selected_color != None:
        exit_script = False
        message_label.configure(text="Press + to increase counter by 1 / stop with Esc")
        check_routine_btn.configure(text="Stop checking encounters", bg="red")
        threading.Thread(target=check_screen_routine, daemon=True).start()
        sound.play_start_sound()

def disable_encounter_check():
    global exit_script
    if not exit_script:
        exit_script = True
        message_label.configure(text="")
        check_routine_btn.configure(text="Start checking encounters", bg="green")
        sound.play_stop_sound()

def toggle_encounter_check():
    global exit_script
    if exit_script:
        enable_encounter_check()
    else:
        disable_encounter_check()

def enable_check_routine_btn():
    global resize_thread
    global config
    message = ""
    while resize_thread.is_alive():
        message = config.message()
        if message != None:
            message_label.configure(text=message)
        time.sleep(0.2)
    resize_thread.join()
    message_label.configure(text="")
    check_routine_btn.configure(state=tk.NORMAL)
    resize_preview_btn.configure(state=tk.NORMAL)

def resize_preview():
    global exit_script
    global resize_thread
    if not exit_script:
        toggle_encounter_check()
    check_routine_btn.configure(state=tk.DISABLED)
    resize_preview_btn.configure(state=tk.DISABLED)
    root.iconify()
    resize_thread = threading.Thread(target=config.resize_game_view, daemon=True)
    resize_thread.start()
    threading.Thread(target=enable_check_routine_btn, daemon=True).start()

def update_color_preview():
    global selected_color
    if selected_color != None:
        color_preview_label.configure(text="", background=f'#{selected_color[0]:02x}{selected_color[1]:02x}{selected_color[2]:02x}')
    else:
        color_preview_label.configure(text="?", background="white")

def selected_color_changed(event):
    global config
    global selected_color
    selected_item = selected_color_combo_item.get()
    selected_color = config.set_selected_color(selected_item)
    update_color_preview()
    if selected_item != "Custom":
        set_encounter_color_btn.grid_forget()
    else:
        set_encounter_color_btn.grid(column=1, row=1)

def start_define_custom_color():
    global defining_color
    global preview_refresh_delay

    color_selection_message_label.configure(text="Press Space to save currently detected color")
    defining_color = True
    set_encounter_color_btn.configure(state=tk.DISABLED)
    preview_refresh_delay = 250

def stop_define_custom_color(save: bool):
    global config
    global defining_color
    global preview_refresh_delay
    global selected_color

    defining_color = False
    color_selection_message_label.configure(text="")
    set_encounter_color_btn.configure(state=tk.NORMAL)
    preview_refresh_delay = 2000
    if (save):
        selected_color = grab_average_color()
        config.set_selected_color(selected_color)
        update_color_preview()

def enable_sample_area_selector(event):
    global exit_script
    global move_mode
    global preview_refresh_delay
    global sample_area_selector_active
    global show_preview
    if ((not exit_script) or move_mode):
        return
    
    if not show_preview:
        toggle_preview()
    preview_refresh_delay = 250
    sample_area_selector_active = True
    message_label.configure(text="Sample area selector enabled. Press 'r' for default and 'esc' to exit. " +
                            "Left click on preview to change area.")
    check_routine_btn.configure(state=tk.DISABLED)
    resize_preview_btn.configure(state=tk.DISABLED)
    hide_preview_btn.configure(state=tk.DISABLED)

def complete_sample_area_selection():
    global config
    global move_mode
    global post_double_click
    global preview_refresh_delay
    global sample_area_selector_active
    message_label.configure(text="")
    post_double_click = False
    sample_area_selector_active = False
    if move_mode:
        toggle_move(True)
    else:
        config.save_current_config()
        check_routine_btn.configure(state=tk.NORMAL)
        resize_preview_btn.configure(state=tk.NORMAL)
        hide_preview_btn.configure(state=tk.NORMAL)
        preview_refresh_delay = 2000

def transform_preview_coordinate(coord: tuple, image_width: int, image_height: int) -> tuple:
    global config
    bounding_box = config.bounding_box()
    x = (round(((bounding_box[2] - bounding_box[0]) / image_width) * coord[0])) + bounding_box[0]
    y = (round(((bounding_box[3] - bounding_box[1]) / image_height) * coord[1])) + bounding_box[1]
    return (x, y)

def preview_mouse_down(event):
    global last_drag_position
    global move_mode
    global sample_area_selector_active
    global sample_select_drag_start
    if move_mode:
        last_drag_position = (event.x, event.y)
    elif sample_area_selector_active:
        sample_select_drag_start = (event.x, event.y)

def preview_mouse_up(event):
    global config
    global move_mode
    global post_double_click
    global preview_width
    global preview_height
    global sample_area_selector_active
    global sample_select_drag_start
    if move_mode:
        return
    if sample_area_selector_active:
        if not post_double_click:
            post_double_click = True
            return
        img = ig.grab(config.bounding_box(), all_screens=True)
        img.thumbnail((preview_width, preview_height))
        if (sample_select_drag_start != None and (sample_select_drag_start[0] != event.x or sample_select_drag_start[1] != event.y)):
            config.set_sample_coordinate(transform_preview_coordinate(sample_select_drag_start, img.width, img.height))
        config.set_sample_coordinate(transform_preview_coordinate((event.x, event.y), img.width, img.height))
        sample_select_drag_start = None

def preview_mouse_drag(event):
    global config
    global last_drag_position
    global move_mode
    global sample_area_selector_active
    if not move_mode:
        return
    
    if last_drag_position != None:
        if sample_area_selector_active:
            config.move_sample_area(event.x - last_drag_position[0], event.y - last_drag_position[1], False)
        else:
            config.move_view(last_drag_position[0] - event.x, last_drag_position[1] - event.y, False)
    last_drag_position = (event.x, event.y)

def toggle_move(save: bool):
    global config
    global move_mode
    global preview_refresh_delay
    global sample_area_selector_active
    global show_preview
    if move_mode:
        move_mode = False
        move_btn.configure(text="Move")
        if sample_area_selector_active:
            return
        if save:
            config.save_current_config()
        else:
            config.load_config()
        check_routine_btn.configure(state=tk.NORMAL)
        resize_preview_btn.configure(state=tk.NORMAL)
        hide_preview_btn.configure(state=tk.NORMAL)
        preview_refresh_delay = 2000
    else:
        if not show_preview:
            toggle_preview()
        move_mode = True
        check_routine_btn.configure(state=tk.DISABLED)
        resize_preview_btn.configure(state=tk.DISABLED)
        hide_preview_btn.configure(state=tk.DISABLED)
        if sample_area_selector_active:
            move_btn.configure(text="Change Shape")
        else:
            move_btn.configure(text="Accept")
        preview_refresh_delay = 70

selected_color_combo_item = tk.StringVar()

step_size_expl_label = tk.Label(step_size_frame, text="Counter increase per encounter:")
message_label = tk.Label(root, text="", justify=tk.RIGHT, font=(font.nametofont("TkDefaultFont").actual(), 11), wraplength=292)
step_size_increase_btn = tk.Button(step_size_frame, text="+", command=lambda: change_step_size(1))
step_size_decrease_btn = tk.Button(step_size_frame, text="-", command=lambda: change_step_size(-1))
color_selection_label = tk.Label(color_selection_frame, text="Detected color: ")
color_selection_combo = ttk.Combobox(color_selection_frame, state="readonly", values=Config.availabel_colors(), textvariable=selected_color_combo_item)
color_preview_label = tk.Label(color_selection_frame, text="", anchor="center", borderwidth=2, relief="groove", width=2)
color_selection_message_label = tk.Label(root, text="", justify=tk.RIGHT, font=(font.nametofont("TkDefaultFont").actual(), 11), wraplength=292)
hide_preview_btn = tk.Button(pic_frame, text="Toggle Preview", command=toggle_preview, width=12)
set_encounter_color_btn = tk.Button(pic_frame, text="Define Color", command=start_define_custom_color, width=12)
move_btn = tk.Button(pic_frame, text="Move", command=lambda: toggle_move(True), width=12)
resize_preview_btn = tk.Button(pic_frame, text="Resize", command=resize_preview, width=12)
check_routine_btn = tk.Button(root, text="Start checking encounters", bg="green", command=toggle_encounter_check)

preview_label = tk.Label(preview_label_frame, image="")
step_size_label = tk.Label(step_size_frame, text="")

# Root grid
step_size_frame.grid(column=0, row=0, sticky=tk.W+tk.N)
message_label.grid(column=1, row=0, sticky=tk.E+tk.N, padx=10)
color_selection_frame.grid(column=0, row=1, padx=10, pady=10, sticky=tk.N+tk.W)
color_selection_message_label.grid(column=1, row=1, sticky=tk.E+tk.N, padx=10)
pic_frame.grid(columnspan=2, row=2)
check_routine_btn.grid(columnspan=2, row=3, pady=10)

# Step size grid
step_size_expl_label.grid(column=0, row=0, padx=10, pady=10)
step_size_decrease_btn.grid(column=1, row=0)
step_size_label.grid(column=2, row=0, padx=5)
step_size_increase_btn.grid(column=3, row=0)

# Color selection grid
color_selection_label.grid(column=0, row=0, sticky=tk.N+tk.W)
color_preview_label.grid(column=1, row=0, sticky=tk.N+tk.W)
color_selection_combo.grid(column=2, row=0, sticky=tk.N+tk.W)

# Picture grid
preview_label_frame.grid(columnspan=4, row=0)
preview_label.place(x=int(preview_width/2), y=int(preview_height/2), anchor="center")

hide_preview_btn.grid(column=0, row=1, pady=5)
set_encounter_color_btn.grid(column=1, row=1)
move_btn.grid(column=2, row=1)
resize_preview_btn.grid(column=3, row=1)

config = Config(config_file_name)
if config.bounding_box() == None:
    show_preview = False
    resize_preview()

preview_label.bind("<Double-Button-1>", enable_sample_area_selector)
preview_label.bind("<Button-1>", preview_mouse_down)
preview_label.bind("<ButtonRelease-1>", preview_mouse_up)
preview_label.bind("<B1-Motion>", preview_mouse_drag)
color_selection_combo.bind("<<ComboboxSelected>>", selected_color_changed)
initial_color_selection = config.selected_color_str()
if initial_color_selection != None:
    selected_color_combo_item.set(config.selected_color_str())
    selected_color_changed(None)
else:
    set_encounter_color_btn.grid_forget()

change_step_size(0)
update_preview()
root.mainloop()