from enum import Enum
from pynput import mouse
from pynput.mouse import Listener
import os.path
from screeninfo import get_monitors, Monitor

class Config:
    class Border(Enum):
        TOP = 1
        RIGHT = 2
        BOTTOM = 3
        LEFT = 4

    _average_white: list[int] = [233, 233, 233]
    _average_black: list[int] = [16, 16, 16]

    _config_file_name: str = ""
    _first: bool = True
    _last_sample: tuple = None
    _monitors: list[Monitor] = None

    _step_size: float = 1.0
    _top_left: tuple = None
    _bottom_right: tuple = None
    _bounding_box: tuple = None
    _selected_color: list[int] = None
    _custom_color: list[int] = None
    _sample_bounding_box: tuple = None

    _message: str = None

    def step_size(self) -> float:
        return self._step_size
    def top_left(self) -> tuple | None:
        return self._top_left
    def bottom_right(self) -> tuple | None:
        return self._bottom_right
    def bounding_box(self) -> tuple | None:
        return self._bounding_box
    def selected_color(self) -> list[int]:
        return self._selected_color
    def custom_color(self) -> list[int]:
        return self._custom_color
    def message(self) -> str | None:
        return self._message
    def sample_bounding_box(self) -> tuple | None:
        if self._sample_bounding_box == None and self._bounding_box != None:
            return self._get_default_sample_bounding_box()
        return self._sample_bounding_box
    
    def availabel_colors() -> list[str]:
        return ["Black", "White", "Custom"]
    def selected_color_str(self) -> str:
        if self._selected_color == None:
            return None
        if self._selected_color == self._average_black:
            return "Black"
        elif self._selected_color == self._average_white:
            return "White"
        else:
            return "Custom"

    def save_current_config(self):
        self._write_config_file()

    def load_config(self):
        self._read_config_file()

    def set_step_size(self, value, save: bool = True):
        if type(value) != int and type(value) != float:
            raise Exception("Can't set a step size of type " + str(type(value)))
        elif value <= 0 :
            self._step_size = 1.0
        else:
            self._step_size = round(value, 2)
        if save:
            self._write_config_file()

    def resize_game_view(self) -> tuple:
        self._first = True
        self._bottom_right = None
        self._bounding_box = self._grab_bounding_box()
        self._sample_bounding_box = None
        self._write_config_file()
        return self.bounding_box()
    
    def set_sample_default(self, save: bool = True):
        self._sample_bounding_box = None
        if save:
            self._write_config_file()
    
    def set_view_default(self, save: bool):
        self._set_default_view_bounding_box()
        if save:
            self._write_config_file()

    def set_view_to_full_screen(self, monitor: int, save: bool):
        if (self._monitors == None):
            self._monitors = get_monitors()
        if (self._monitors != None and len(self._monitors) > monitor):
            self._set_view_to_monitor(self._monitors[monitor])
        if save:
            self._write_config_file()

    def modify_view_bounding_box(self, border: Border, modifier: int, save: bool):
        if (modifier == 0 or self._bounding_box == None):
            return
        
        temp = self._modify_bounding_box(border, self._bounding_box, modifier)
        if (not self._check_monitor_dimensions(temp[0], temp[1], temp[2], temp[3])):
            return
        self._bounding_box = temp
        self._top_left = (self._bounding_box[0], self._bounding_box[1])
        self._bottom_right = (self._bounding_box[2], self._bounding_box[3])
        self._limit_sample_bounding_box()
        if save:
            self._write_config_file()

    def modify_sample_bounding_box(self, border: Border, modifier: int, save: bool):
        if (modifier == 0 or self._bounding_box == None):
            return
        
        if self._sample_bounding_box == None:
            self._sample_bounding_box = self._get_default_sample_bounding_box()

        self._sample_bounding_box = self._modify_bounding_box(border, self._sample_bounding_box, modifier)
        self._limit_sample_bounding_box()
        if save:
            self._write_config_file()

    def set_sample_coordinate(self, coord: tuple, save: bool = True):
        if (coord == None or len(coord) != 2):
            raise Exception("Can not set coordinates for sample bounding box because given coordinates don't have 2 elements.")
        if (self._bounding_box == None):
            raise Exception("Can not set coordinates for sample bounding box without a game bounding box.")
        if (self._sample_bounding_box == None):
            self._sample_bounding_box = (coord[0], coord[1], coord[0], coord[1])
        else:
            if (self._last_sample == None):
                self._sample_bounding_box = (coord[0], coord[1], self._sample_bounding_box[2], self._sample_bounding_box[3])
            else:
                self._sample_bounding_box = (self._last_sample[0], self._last_sample[1], coord[0], coord[1])
            self._last_sample = (coord[0], coord[1])
            self._sample_bounding_box = self._cleanup_bounding_box(self._sample_bounding_box)
        self._limit_sample_bounding_box()
        if (save):
            self._write_config_file()

    def set_selected_color(self, value, save: bool = True) -> list[int]:
        if type(value) == str:
            if value == "White":
                self._selected_color = self._average_white
            elif value == "Black":
                self._selected_color = self._average_black
            elif value == "Custom":
                self._selected_color = self._custom_color
            else:
                raise Exception("Unkown color " + value)
            self._write_config_file()
        elif type(value) != list:
            raise Exception("Can't set the selected color with type " + str(type(value)))
        elif len(value) != 3:
            raise Exception("To set a color proved exactly 3 values. " + len(value) + " Values were received.")
        else:
            self._selected_color = value
            self._custom_color = value
            if (save):
                self._write_config_file()
            
        return self._selected_color

    def move_view(self, horizontal: int, vertical: int, save: bool):
        if self._bounding_box == None:
            return
        
        min_x = self._top_left[0] + horizontal
        min_y = self._top_left[1] + vertical
        max_x = self._bottom_right[0] + horizontal
        max_y = self._bottom_right[1] + vertical
        if not self._check_monitor_dimensions(min_x, min_y, max_x, max_y):
            return
        self._top_left = (min_x, min_y)
        self._bottom_right = (max_x, max_y)
        self._bounding_box = self._top_left + self._bottom_right
        if self._sample_bounding_box != None:
            self._sample_bounding_box = (self._sample_bounding_box[0] + horizontal,
                                         self._sample_bounding_box[1] + vertical,
                                         self._sample_bounding_box[2] + horizontal,
                                         self._sample_bounding_box[3] + vertical)
        if save:
            self._write_config_file()

    def move_sample_area(self, horizontal: int, vertical: int, save: bool):
        if self._bounding_box == None:
            return
        
        if self._sample_bounding_box == None:
            self._sample_bounding_box = self._get_default_sample_bounding_box()

        if horizontal > 0:
            horizontal = min(horizontal, self._bounding_box[2] - self._sample_bounding_box[2])
        elif horizontal < 0:
            horizontal = max(horizontal, self._bounding_box[0] - self._sample_bounding_box[0])
        
        if vertical > 0:
            vertical = min(vertical, self._bounding_box[3] - self._sample_bounding_box[3])
        elif vertical < 0:
            vertical = max(vertical, self._bounding_box[1] - self._sample_bounding_box[1])

        if (horizontal == 0 and vertical == 0):
            return

        self._sample_bounding_box = (self._sample_bounding_box[0] + horizontal, self._sample_bounding_box[1] + vertical, self._sample_bounding_box[2] + horizontal, self._sample_bounding_box[3] + vertical)
        self._limit_sample_bounding_box()
        if save:
            self._write_config_file()

    def __init__(self, file_name):
        self._config_file_name = file_name
        self._step_size = 1
        if not os.path.exists(file_name):
            self._create_config_file()
        else:
            self._read_config_file()

    def _create_config_file(self):
        # Set defaults
        self._selected_color = self._average_white
        self._step_size = 1.0
        self._set_default_view_bounding_box()
        
        # Write config
        config_file = open(self._config_file_name, "w")
        config_file.write("bounding_box=" + (','.join(str(x) for x in (self._bounding_box)) if self._bounding_box != None else "") +
                          "\nsample_bounding_box=default" +
                          "\nstep_size=" + str(self._step_size) +
                          "\ncolor_indicating_encounter=" + self.selected_color_str() +
                          "\ncustom_color=")

    def _write_config_file(self):
        config_file = open(self._config_file_name, "w")
        if self._bounding_box != None:
            config_file.write("bounding_box=" + ','.join(str(x) for x in (self._bounding_box)) + "\n")
        else:
            config_file.write("bounding_box=\n")
        
        if self._bounding_box == None or self._sample_bounding_box == None or self._sample_bounding_box == self._get_default_sample_bounding_box():
            config_file.write("sample_bounding_box=default\n")
        else:
            config_file.write("sample_bounding_box=" + ','.join(str(x) for x in (self._sample_bounding_box)) + "\n")

        if self._step_size != None:
            config_file.write("step_size=" + str(self._step_size) + "\n")
        else:
            config_file.write("step_size=1\n")

        if self._selected_color != None:
            if self._selected_color == self._average_black:
                config_file.write("color_indicating_encounter=Black\n")
            elif self._selected_color == self._average_white:
                config_file.write("color_indicating_encounter=White\n")
            else:
                config_file.write("color_indicating_encounter=Custom\n")
        else:
            config_file.write("color_indicating_encounter=White\n")

        if self._custom_color != None:
            config_file.write("custom_color=" + str(self._custom_color))
        else:
            config_file.write("custom_color=")
        
        config_file.close()

    def _read_config_file(self):
        config_file = open(self._config_file_name, "r")
        lines = config_file.readlines()

        for i, line in enumerate(lines):
            if line.endswith('\n'):
                lines[i] = line[:-1]
        
        config_file.close()

        for line in lines:
            content = line.split('=', 1)[1]
            if len(content) == 0:
                continue
            
            # Read bounding box
            if line.startswith("bounding_box"):
                if (len(content) >= 7):
                    self._bounding_box = [int(x) for x in content.split(",")]
                    if len(self._bounding_box) != 4:
                        self._bounding_box = None
                    else:
                        self._bounding_box = self._cleanup_bounding_box(self._bounding_box)
                        self._top_left = (self._bounding_box[0], self._bounding_box[1])
                        self._bottom_right = (self._bounding_box[2], self._bounding_box[3])

            # Read sample bounding box
            elif line.startswith("sample_bounding_box"):
                if (content == "default"):
                    self._sample_bounding_box = None
                elif (len(content) >= 7):
                    self._sample_bounding_box = [int(x) for x in content.split(",")]
                    if len(self._sample_bounding_box) != 4:
                        self._sample_bounding_box = None
                    else:
                        self._sample_bounding_box = self._cleanup_bounding_box(self._sample_bounding_box)

            #Read step size
            elif line.startswith("step_size"):
                self._step_size = float(content)

            #Read selected color
            elif line.startswith("color_indicating_encounter"):
                if content == "Black":
                    self._selected_color = self._average_black
                elif content == "White":
                    self._selected_color = self._average_white
                elif content != "Custom":
                    raise Exception("Invalid config file! Valid values for \"color_indicating_encounter\" are \"Black\", \"White\" and \"Custom\".")

            #Read custom color
            elif line.startswith("custom_color"):
                values: list[str] = content.split(",")
                if len(values) != 3:
                    continue
        
                self._custom_color = [0, 0, 0]
                for i, valuestr in enumerate(values):
                    if valuestr.startswith("["):
                        valuestr = valuestr[1:]
                    elif valuestr.endswith("]"):
                        valuestr = valuestr[:-1]
                    self._custom_color[i] = int(valuestr.strip())
                if self._selected_color == None:
                    self._selected_color = self._custom_color
        
        self._limit_sample_bounding_box()

        # To not lose any saved data we first read it and now we prevent an incomplete config by overwriting it.
        # Then we need to read it again to apply default values
        if len(lines) != 5:
            self._write_config_file()
            self._read_config_file()


    def _on_click(self, x, y, button, pressed):
        if pressed and button == mouse.Button.left:
            if self._first:
                self._top_left = (x, y)
                self._first = False
                self._message= "Now click bottom right of game window"
            else:
                if x >= self._top_left[0] and y >= self._top_left[1]:
                    self._bottom_right = (x, y)
        elif self._bottom_right != None:
            self._message = None
            return False

    def _grab_bounding_box(self) -> tuple:
        self._message = "Click top left of game window"
        with Listener(
            on_click=self._on_click
        ) as listener:
            listener.join()
        return self._top_left + self._bottom_right

    def _get_default_sample_bounding_box(self) -> tuple | None:
        if self._bounding_box == None:
            return None
        distance_x = self._bottom_right[0] - self._top_left[0]
        distance_y = self._bottom_right[1] - self._top_left[1]
        margin_x = int(distance_x * 0.05)
        margin_y = int(distance_y * 0.05)
        mid_x = int(self._top_left[0] + distance_x / 2)
        mid_y = int(self._top_left[1] + distance_y / 2)
        return (mid_x - margin_x, mid_y - margin_y, mid_x + margin_x, mid_y + margin_y)
    
    def _cleanup_bounding_box(self, box: tuple | list[int]) -> tuple:
        min_x = min(box[0], box[2])
        min_y = min(box[1], box[3])
        max_x = max(box[2], box[0])
        max_y = max(box[3], box[1])
        return (min_x, min_y, max_x, max_y)
    
    def _limit_sample_bounding_box(self):
        if self._sample_bounding_box == None:
            return
        if self._bounding_box == None and self._sample_bounding_box != None:
            self._sample_bounding_box = None
            return

        if (self._sample_bounding_box[0] < self._bounding_box[0]):
            self._sample_bounding_box = (self._bounding_box[0], self._sample_bounding_box[1], self._sample_bounding_box[2], self._sample_bounding_box[3])
        if (self._sample_bounding_box[1] < self._bounding_box[1]):
            self._sample_bounding_box = (self._sample_bounding_box[0], self._bounding_box[1], self._sample_bounding_box[2], self._sample_bounding_box[3])
        if (self._sample_bounding_box[2] > self._bounding_box[2]):
            self._sample_bounding_box = (self._sample_bounding_box[0], self._sample_bounding_box[1], self._bounding_box[2], self._sample_bounding_box[3])
        if (self._sample_bounding_box[3] > self._bounding_box[3]):
            self._sample_bounding_box = (self._sample_bounding_box[0], self._sample_bounding_box[1], self._sample_bounding_box[2], self._bounding_box[3])

        if (self._sample_bounding_box[2] < self._bounding_box[0]):
            self._sample_bounding_box = (self._sample_bounding_box[0], self._sample_bounding_box[1], self._bounding_box[0], self._sample_bounding_box[3])
        if (self._sample_bounding_box[3] < self._bounding_box[1]):
            self._sample_bounding_box = (self._sample_bounding_box[0], self._sample_bounding_box[1], self._sample_bounding_box[2], self._bounding_box[1])
        if (self._sample_bounding_box[0] > self._bounding_box[2]):
            self._sample_bounding_box = (self._bounding_box[2], self._sample_bounding_box[1], self._sample_bounding_box[2], self._sample_bounding_box[3])
        if (self._sample_bounding_box[1] > self._bounding_box[3]):
            self._sample_bounding_box = (self._sample_bounding_box[0], self._bounding_box[3], self._sample_bounding_box[2], self._sample_bounding_box[3])

    def _modify_bounding_box(self, border: Border, boundingBox: tuple, modifier: int) -> tuple:
        if border == self.Border.TOP:
            if (boundingBox[1] - modifier) < boundingBox[3]:
                boundingBox = (boundingBox[0], boundingBox[1] - modifier, boundingBox[2], boundingBox[3])
        elif border == self.Border.RIGHT:
            if boundingBox[0] < (boundingBox[2] + modifier):
                boundingBox = (boundingBox[0], boundingBox[1], boundingBox[2] + modifier, boundingBox[3])
        elif border == self.Border.BOTTOM:
            if boundingBox[1] < (boundingBox[3] + modifier):
                boundingBox = (boundingBox[0], boundingBox[1], boundingBox[2], boundingBox[3] + modifier)
        elif border == self.Border.LEFT:
            if (boundingBox[0] - modifier) < boundingBox[2]:
                boundingBox = (boundingBox[0] - modifier, boundingBox[1], boundingBox[2], boundingBox[3])
        return boundingBox
    
    """"
    Checks if coordinates fit on screen.

    Returns
    -------
    bool
        True if coordinates are ok, False else
    """
    def _check_monitor_dimensions(self, min_x: int, min_y: int, max_x: int, max_y: int) -> bool:
        if self._monitors == None:
            self._monitors = get_monitors()

        tl_ok = False
        bl_ok = False
        tr_ok = False
        br_ok = False
        for m in self._monitors:
            min_x_ok = min_x <= (m.x + m.width) and min_x >= m.x
            min_y_ok = min_y <= (m.y + m.height) and min_y >= m.y
            max_x_ok = max_x <= (m.x + m.width) and max_x >= m.x
            max_y_ok = max_y <= (m.y + m.height) and max_y >= m.y
            if (min_x_ok and min_y_ok):
                tl_ok = True
            if (min_x_ok and max_y_ok):
                bl_ok = True
            if (max_x_ok and min_y_ok):
                tr_ok = True
            if (max_x_ok and max_y_ok):
                br_ok = True
        
        return tl_ok and bl_ok and tr_ok and br_ok
    
    def _set_default_view_bounding_box(self):
        if (self._monitors == None):
            self._monitors = get_monitors()

        if self._monitors != None and len(self._monitors) > 0:
            primaryMonitor = next(monitor for monitor in self._monitors if monitor.is_primary == True)
            self._set_view_to_monitor(primaryMonitor if primaryMonitor != None else self._monitors[0])

    def _set_view_to_monitor(self, monitor: Monitor):
        self._bounding_box = (monitor.x, monitor.y, monitor.x + monitor.width, monitor.y + monitor.height)
        self._top_left = (self._bounding_box[0], self._bounding_box[1])
        self._bottom_right = (self._bounding_box[2], self._bounding_box[3])