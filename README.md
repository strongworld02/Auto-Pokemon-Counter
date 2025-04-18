# Auto-Pokemon-Counter
A simple automatic tracker to count the number of Pokémon encountered.

The program periodically checks the screen for a specific color and increases the counter by a specified number once that color was detected.
This takes advantage of the fact that most Pokémon games start their encounter by flashing to white or black.
Naturally this program requires access to a constant video feed of the game.

The number of encounters is saved to a file, so it persists after restarting the program.
Every encounter is saved immediatly so it can for example be read by OBS and displayed on screen.


## Settings
It's possible to configure:
- the number added to the counter
- the color to be detected
- the window size and location of the game
- the area inside the game window that is being checked for the specified color


## Controls
The program is not designed to be particularly user friendly or pretty. So here's a full list of controls (as of 2025-04-18):

### Checking encounters
- Start checking encounters by pressing the appropriate button or hitting ^
- Stop checking encounters by pressing the appropriate button or hitting ESC

### Configure game size and location
When starting for the first time or clearing the config you automatically start the configuration of the games location (resize event).<br/>
This can be triggered again by pressing the appropriate button.
- Once the resize event has been triggered the program minimizes and is looking for your next mouse clicks.
  - Your very next left mouse click should be on the top left corner of your game window.
  - Your second left mouse click should be on the bottom right corner of your game window.<br/>
    (Note that the program will keep listening for left mouse clicks until you click somewhere below and to the right of your first click. Clicking above or to the left of your first click won't register.)
- To just move the game location without changing the size you can click on the "Move" button. This updates the view to show the current detection area (it may take up to 2 seconds depending on the last preview update).
  - To start moving the window you can either hold left click on the preview and move it with your mouse or use the arrow keys.<br/>
    Holding Shift while using the arrow keys makes it move faster.
  - Press the "Move" button again (which now reads "Accept") to apply the changes made and save them to the config.
  - Press ESC to revert the changes and exit move mode

### Configure detection area
By default the game checks about 10% in the center of the game window.<br/>
To make any changes start by making a double left click on the preview. You'll see a red square appear on the preview, showing you the current detection area (it may take up to 2 seconds depending on the last preview update).
- By left clicking the preview repeatedly you can set the coordinates of the detection are in alternating order to your cursors location
- You can also hold left click and move your mouse to define the area. This sets the coordinates to where you first pressed down and where you let go. The preview will not update while dragging your mouse.
- Using the arrow keys let's you increase the size of the detection area.
- Holding Shift and pressing the arrow keys let's you decrease the size of the detection area.
- Press the "Move" button to enter move mode.
  - To start moving the detection area you can either hold left click on the preview and move it with your mouse or use the arrow keys.<br/>
    Holding Shift while using the arrow keys makes it move faster.
  - Press the "Move" button again (which now reads "Change Shape") to exit move mode
- Press R to reset the detection area to default (not your previous setting).
- Press ESC to apply the changes and save them to the config (If you want to revert your changes you'll have to restart the program without hitting ESC)

### Update detected color
Near the top you'll find a combo box letting you choose between black, white and a custom color.
- To define a custom color first select "Custom". This makes the button "Define Color" appear.
- Click on "Define Color" and either put a screenshot over the game window or get to a moment in the game you want to be counted.
- Hit Space to select the currently detected color and save it to the config. The game window will be evaluated the moment you hit Space, regardless of what the preview currently shows.

### Set the number to be added to the counter
Press the - or + buttons at the top of the screen.<br/>
You can go below 1 to set up some hard to track scenarios like soft resetting or reviving fossils.



## FAQ (No one has actually asked a question)
- Q: Why is the preview so low?<br/>
  A: It only updated once every 2 seconds when you are not moving it or changing the tracking area to save on resources. This interval is decreased while you're making changes.<br/>
     Don't worry, it checks for encounters more often (currently that would be every 0.35 seconds).
- Q: Why did it detect an encounter when there wasn't one (or the other way around)?<br/>
  A: If that happens then you need to either change the color to be detected or change the area that is being checked. Try looking for colors that are unlikely to appear on the Pokémon or trainers as the camera changes during battle might make them appear somewhere unexpected.<br/>
     As an example: For BDSP soft resets I had to look for the Turtwig that appears on the loading screen when starting the game. Since the loading screen is played twice when starting the game I set the encounters to 1/2 and because it's jumping I had to tweak the detection area quite a bit to have it only ever include green pixels. Once I had that set up it worked perfectly every time as long as I didn't move the game window.
- Q: Moving the games window / detection area by dragging it isn't accurate. What's up with that?<br/>
  A: True. Probably a bug, maybe just inefficient. ¯\_(ツ)_/¯
- Q: Is the preview being use to check for encounters or for setting a custom color?<br/>
  A: No, the preview is just for you to control what the program is able to see.
