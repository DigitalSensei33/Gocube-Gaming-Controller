## Gocube Gaming Controller Overview

GoCube Gaming Controller is a Python application that converts (specifically) a GoCube Edge Bluetooth smart cube into a fully playable PC game controller using Bluetooth Low Energy (BLE) input and gyroscope motion tracking.

Fair warning: I'm not a software developer. This started as a fun idea I messed with after work, and I learned most of what I needed as I went. It's definitely not perfect, but it works well enough that I managed to beat Dark Souls 3 with it, which was the whole goal.

This used Ignisco's smartcube gaming controller repo (https://github.com/ignisco/Smart-Cube-Gaming-Controller) as a basic starting point/template. The only real remaining stuff from their build is some of the face-turns.py file.

Mostly uses the Bleak library for BLE communication and the Windows SendInput API for keyboard/mouse emulation. I worked with Claude sonnet and opus in late 2025 to make the code.  

I only have very fundamental Python knowledge, so Claude did most of the coding, while I focused on function, design, testing each iteration, debugging, and steering things in the right direction to make it playable.
There may be some vestigial code left behind from previous versions, and some inefficient code, but that's a problem for me to get to as I clean it all up to reach a more fully realized 1.0 version.

This is something that I've seen done in a few different ways before, but it always seemed complex and hard to set up, or otherwise limited in some way. What I wanted was to create a lightweight Python-only program that communicates directly with the cube over BLE, avoiding browser-based APIs and unnecessary shenanigans in the middle. Low input delay, responsive, all running in a single environment. As few excess moving parts as possible for a (hopefully) stable and less bug prone experience. Cube input - PC - software - game input.


## Current Status

Development Status: Active(ish)

Current Version: v0.7 (working title)

The project is fully playable as-is (v0.7) and was used to complete Dark Souls 3 from start to finish using only the cube as the primary controller.


## Features

- Bluetooth Low Energy communication using Bleak
- Face-turn detection (directional)
- Gyroscope-based movement and camera controls.
- Gyroscope UI window showing pitch/roll/yaw readings and intended inputs
- Numpad keybind for gyroscope zero/neutral position reset when yaw drifts
- Priority-based input queue system (anti-ghosting)
- Adaptive timing/delay calibration
- Protocol-level connection reset (vs. full reconnect)
- Debug/stats logging (latency, drop rate, ghosting prevented)
- Keyboard and mouse input emulation
- Fully playable in Dark Souls 3 as-is.
- Key mapping customizable (via source edit — config module planned)
- Very low input delay.

## Known Issues/Limitations

***IMPORTANT***
- HIGH PRIORITY - Current version (0.7) has gradual drift in gyroscope readings for Yaw only. Over time, mostly just when moving forward, the yaw will gradually drift to a negative integer value when held at zero yaw position, which will begin panning camera left while only moving forward. Pitching forward for movement increases the speed at which this happens. I have mitigated the drift while at neutral zeroed position, (green front/towards you, white up) but the drift rate increases with (as far as i know, only positive) pitch. 
This is currently half-solved with a zero/neutral state reset hotkey, that needs used every 10 minutes or so depending on your usage. Press 5 on numpad to reset the gyroscope to zero, make sure you're holding the cube in proper neutral position.
- Movement + camera control unusable simultaneously above ~35° pitch due to yaw isolation freeze from attempted drift fix. Isolation-mode drift compensation is unbounded / not paused during isolation.  
***IMPORTANT***

- Only 12 face turns total limits keybinds and 6 total gyroscope directions. Total 18 inputs available.
- current version can only be run from console/powershell window, and inside of a virtual environment. Immediate priority is to simplify for users by making a .bat file to run it from, and eventually making it .exe. 
- Keybinds use the Windows SendInput API (via scan codes), so editing them is a little more involved than just changing a variable to "W" — you'll need the scan code for whichever key you want. A quick search for "SendInput scan codes" will get you the reference table you need.
- Requires a paired/known GoCube Edge, unkown if other smartcubes are compatible. Almost certainly not Gan brand cubes (very proprietary)
- Directinput name for module is inaccurate currently, This actually uses the Windows SendInput API via ctypes, not legacy DirectInput API. This is just a leftover name from before I changed methods because the game window wasn't registering inputs from DirectInput.

## Setup

### Requirements
- Windows 10 or 11 (this project uses Windows-specific input APIs and will not run on macOS/Linux)
- Python 3.9 or newer ([python.org](https://www.python.org/downloads/))
- A GoCube Edge smart cube
- Dependencies: bleak, pywin32, pyautogui


### Installation

1. **Download or clone this repository**

   https://github.com/DigitalSensei33/gocube-gaming-controller.git

     or download it as a ZIP from GitHub and extract it.

2. **Pair your GoCube Edge with Windows**
   - Turn a face on the cube to wake it
   - Go to Settings > Bluetooth & devices > Add device > Bluetooth
   - Select your GoCube Edge from the list and pair it

3. **Find and input your cube's MAC address**
   - Go to Settings > Bluetooth & devices > Devices
   - Click your paired GoCube Edge, then "More devices and printer settings" (or Properties, depending on your Windows version)
   - Look for the Bluetooth unique ID / device address — it'll look like `XX:XX:XX:XX:XX:XX`
   - Open `main.py` in a text editor, find this line near the bottom of the file:
```python
     async def connect(self, device_address: str = "E6:EF:C6:B0:B8:A8") -> bool:
```
   - Replace `E6:EF:C6:B0:B8:A8` with your own cube's MAC address

4. **Run the setup script**
   - Double-click `setup.bat`
   - (If running from PowerShell instead of double-clicking, use `.\setup.bat`)
   - This creates a virtual environment and installs all required dependencies automatically

5. **Launch the controller**
   - Double-click `start.bat` (or `.\start.bat` in PowerShell)
   - Wake the cube if it's been idle (turn any face)
   - Wait for the console to confirm "cube detected" and connection — see Known Issues for current connection reliability notes
   - Once connected, hold/place the cube **white face up, green face toward you**, and hold it still for calibration (a couple seconds)

You're ready to play once calibration completes.


## Controls

Currently coded to a customized dark souls 3 control scheme, using only keyboard inputs and mouse clicks. Can be edited to change which face turns (and directions of face turns) press which keys (in face-turns.py ***ADD LINE #S). Can also be edited to change movement and camera with gyroscope tilting to other desired controls. 

***IMPORTANT***
This is all specifically coded with green in front (towards you) and white on top.

For non-cubers:
If cube is scrambled, go by the center pieces to find face color. The cube notation (U-D L-R F-B) is fairly self explanatory.

Letter alone - clockwise turn
Letter w/ Apostrophe - counterclockwise turn 
(as if you were looking directly at the face, meaning Back face (away from you) turns to the left from your perspective, but technically is turning right.)

All inputs are ONE 90° quarter turn

Face turn controls-

- U(white) → Dodge Roll (B key)***
- U' → Sprint Toggle (hold/release Space)***
- R(red) → Light Attack (LMB)
- R' → Heavy Attack (RMB)
- L(orange) → Shield/Spell/offhand (J key)
- L' → Parry/Weapon Art (Ctrl)
- D(yellow) → Rotate Items (Down Arrow)
- D' → Drink Estus/Use Item (R key)
- F(green) → Lock On (Q key)
- F' → Jump (H key)
- B(blue) → 2-Hand RH Weapon (F key)
- B' → Interact (E key)

***since Dark Souls has sprint/dodge roll as the same button/key usually, this was a little tricky. I have the code set to toggle hold/release sprint with each U' turn, but U turn/dodge roll out of a sprint also releases the space key, to feel more like natural DS3 controls. If you dodge roll out of a sprint, you'll have to U' after to sprint out of the roll.***

Gyroscope controls
Just think of the top (white) face of the cube as a joystick and tilt it around for movement

- Pitch forward/Tilt cube away from you - forward (W key)
- Pitch back/Tilt cube towards you - backward (S key)
- Roll left/Tilt cube left - move left (A key)
- Roll right/Tilt cube right - move right (D key)
- Yaw left/turn cube left (like unscrewing it from something beneath it) - cam pan left (O key)
- Yaw right/turn cube right - cam pan right (P key)

## Future plans/roadmap

- Fix yaw drift issue **TOP PRIORITY**
- add .bat file for easier user function
- Make the program an .exe file for simpler use.
- clean up excessive console readouts, remove instructions/controls in console output.
- config/keybinds UI/module for end user QoL
- better calibration
- multiple profiles (quick swap set keybinds for different games)
- considering finding a way to implement 180 degree turns for more potential inputs
