#!/usr/bin/env python3
"""
Enhanced Face Turns Processing Module with Input Queue Integration
Eliminates ghosting and ensures 100% reliable input execution
"""

import time
from sendinput import press_key, release_key, CHAR_MAP
import pyautogui

# Import the queue system
from input_queue import InputQueueSystem, InputPriority, InputType

# Disable pyautogui failsafe for gaming
pyautogui.FAILSAFE = False


class EnhancedFaceTurnProcessor:
    def __init__(self, input_queue: InputQueueSystem, debug=True):
        self.debug = debug
        self.input_queue = input_queue
        
        # State tracking
        self.sprint_active = False
        self.held_keys = set()
        
        # Button mappings with priorities
        self.button_mappings = {
            'U': (self._handle_U, InputPriority.CRITICAL),           # B key - Dodge Roll
            "U'": (self._handle_U_prime, InputPriority.HIGH),          # Space toggle - Sprint
            'R': (self._handle_R, InputPriority.HIGH),            # LMB - Light Attack
            "R'": (self._handle_R_prime, InputPriority.HIGH),           # RMB - Heavy Attack
            'L': (self._handle_L, InputPriority.HIGH),        # Left Ctrl - Parry
            "L'": (self._handle_L_prime, InputPriority.NORMAL),         # J key - Shield/Spell
            'D': (self._handle_D, InputPriority.LOW),             # Down Arrow - Rotate
            "D'": (self._handle_D_prime, InputPriority.NORMAL),          # R key - Use Item
            'F': (self._handle_F, InputPriority.NORMAL),               # Q key - Lock On
            "F'": (self._handle_F_prime, InputPriority.NORMAL),                 # H key - Jump
            'B': (self._handle_B, InputPriority.LOW),          # F key - 2-Hand
            "B'": (self._handle_B_prime, InputPriority.NORMAL),             # E key - Interact
        }
        
        if self.debug:
            print("✓ Enhanced Face Turn Processor initialized")
            print("   • Input queue integration for 100% reliability")
            print("   • Smart priority system for critical actions")
            print("   • Anti-ghosting with minimal latency")
    
    def process_turn(self, turn):
        """Process face turn through the input queue"""
        if turn in self.button_mappings:
            action, priority = self.button_mappings[turn]
            
            if self.debug:
                print(f"🎲 Queueing face turn: {turn} (priority={priority.name})")
            
            # Queue the action instead of executing directly
            action()
        else:
            if self.debug:
                print(f"⚠️ Unmapped face turn: {turn}")
    
    # === ENHANCED GAMING CONTROLS WITH QUEUE ===
    
    def _handle_U(self):
        """U - Space (tap)"""
        if self.sprint_active:
            # Sprint is active - need special sequence for dodge
            if self.debug:
                print(f"→ U")
            
            # Queue the dodge sequence with CRITICAL priority
            # 1. Release sprint
            self.input_queue.queue_input(
                action=lambda: self._release_key_direct('space'),
                priority=InputPriority.CRITICAL,
                input_type=InputType.KEY_RELEASE,
                key_code=CHAR_MAP['space'],
                group_id='space_release',
                description="Sprint release for dodge"
            )
            
            # 2. Longer pause then tap for dodge (20ms for maximum reliability)
            time.sleep(0.020)  # 20ms pause for rock-solid sprint->dodge reliability
            
            self.input_queue.queue_input(
                action=lambda: self._tap_key_direct('space'),
                priority=InputPriority.CRITICAL,
                input_type=InputType.KEY_TAP,
                key_code=CHAR_MAP['space'],
                group_id='space_tap',
                description="U tap"
            )
            
            self.sprint_active = False
        else:
            # Normal dodge roll
            if self.debug:
                print(f"→ U (normal)")
            
            self.input_queue.queue_input(
                action=lambda: self._tap_key_direct('space'),
                priority=InputPriority.CRITICAL,
                input_type=InputType.KEY_TAP,
                key_code=CHAR_MAP['space'],
                group_id='space_tap',
                description="U"
            )
    
    def _handle_U_prime(self):
        """U' - Space (toggle)"""
        if self.debug:
            print(f"→ U' toggle (current={self.sprint_active})")
        
        if self.sprint_active:
            # Turn OFF sprint
            self.input_queue.queue_input(
                action=lambda: self._release_key_direct('space'),
                priority=InputPriority.HIGH,
                input_type=InputType.KEY_RELEASE,
                key_code=CHAR_MAP['space'],
                group_id='space_release',
                description="U' OFF"
            )
            self.sprint_active = False
        else:
            # Turn ON sprint
            self.input_queue.queue_input(
                action=lambda: self._press_key_direct('space'),
                priority=InputPriority.HIGH,
                input_type=InputType.KEY_PRESS,
                key_code=CHAR_MAP['space'],
                group_id='space_hold',
                description="U' ON"
            )
            self.sprint_active = True
    
    def _handle_R(self):
        """R - LMB - Light Attack with proper timing"""
        self.input_queue.queue_input(
            action=self._click_mouse_left,
            priority=InputPriority.HIGH,
            input_type=InputType.MOUSE_CLICK,
            group_id='lmb',
            description="R (LMB)"
        )
    
    def _handle_R_prime(self):
        """R' - RMB"""
        self.input_queue.queue_input(
            action=self._click_mouse_right,
            priority=InputPriority.HIGH,
            input_type=InputType.MOUSE_CLICK,
            group_id='rmb',
            description="R' (RMB)"
        )
    
    def _handle_L_prime(self):
        """L' - J key"""
        self.input_queue.queue_input(
            action=lambda: self._tap_key_direct('j'),
            priority=InputPriority.NORMAL,
            input_type=InputType.KEY_TAP,
            key_code=CHAR_MAP['j'],
            description="L' (J)"
        )
    
    def _handle_L(self):
        """L - Left Ctrl"""
        self.input_queue.queue_input(
            action=lambda: self._tap_key_direct('left ctrl'),
            priority=InputPriority.HIGH,
            input_type=InputType.KEY_TAP,
            key_code=CHAR_MAP['left ctrl'],
            description="L (Ctrl)"
        )
    
    def _handle_D(self):
        """D - Down Arrow"""
        self.input_queue.queue_input(
            action=lambda: self._tap_key_direct('down arrow'),
            priority=InputPriority.LOW,
            input_type=InputType.KEY_TAP,
            key_code=CHAR_MAP['down arrow'],
            description="D (Down)"
        )
    
    def _handle_D_prime(self):
        """D' - R key"""
        self.input_queue.queue_input(
            action=lambda: self._tap_key_direct('r'),
            priority=InputPriority.NORMAL,
            input_type=InputType.KEY_TAP,
            key_code=CHAR_MAP['r'],
            description="D' (R)"
        )
    
    def _handle_F(self):
        """F - Q key"""
        self.input_queue.queue_input(
            action=lambda: self._tap_key_direct('q'),
            priority=InputPriority.NORMAL,
            input_type=InputType.KEY_TAP,
            key_code=CHAR_MAP['q'],
            description="F (Q)"
        )
    
    def _handle_F_prime(self):
        """F' - H key"""
        self.input_queue.queue_input(
            action=lambda: self._tap_key_direct('h'),
            priority=InputPriority.NORMAL,
            input_type=InputType.KEY_TAP,
            key_code=CHAR_MAP['h'],
            description="F' (H)"
        )
    
    def _handle_B(self):
        """B - F key"""
        self.input_queue.queue_input(
            action=lambda: self._tap_key_direct('f'),
            priority=InputPriority.LOW,
            input_type=InputType.KEY_TAP,
            key_code=CHAR_MAP['f'],
            description="B (F)"
        )
    
    def _handle_B_prime(self):
        """B' - E key"""
        self.input_queue.queue_input(
            action=lambda: self._tap_key_direct('e'),
            priority=InputPriority.NORMAL,
            input_type=InputType.KEY_TAP,
            key_code=CHAR_MAP['e'],
            description="B' (E)"
        )
    
    # === DIRECT INPUT METHODS (called by queue) ===
    
    def _tap_key_direct(self, key_name):
        """Direct key tap execution with enhanced press/release method"""
        try:
            if key_name in CHAR_MAP:
                key_code = CHAR_MAP[key_name]
                if self.debug:
                    print(f"  Tapping key: '{key_name}' -> scan code {key_code}")
                
                # Enhanced method: ensure clean state first (like mouse clicks)
                release_key(key_code)     # Ensure clean state
                time.sleep(0.001)         # Brief pause
                press_key(key_code)
                time.sleep(0.020)         # 20ms hold for rock-solid reliability
                release_key(key_code)
            else:
                if self.debug:
                    print(f"  ERROR: Key '{key_name}' not found in CHAR_MAP")
        except Exception as e:
            if self.debug:
                print(f"Key tap error: {e}")
    
    def _press_key_direct(self, key_name):
        """Direct key press (hold) execution"""
        try:
            if key_name in CHAR_MAP:
                key_code = CHAR_MAP[key_name]
                press_key(key_code)
                self.held_keys.add(key_name)
        except Exception as e:
            if self.debug:
                print(f"Key press error: {e}")
    
    def _release_key_direct(self, key_name):
        """Direct key release execution"""
        try:
            if key_name in CHAR_MAP:
                key_code = CHAR_MAP[key_name]
                release_key(key_code)
                self.held_keys.discard(key_name)
        except Exception as e:
            if self.debug:
                print(f"Key release error: {e}")
    
    def _click_mouse_left(self):
        """Execute left mouse click using working method with timing control"""
        from sendinput import mouse_press_left, mouse_release_left
        try:
            # Ensure clean state first (from working version)
            mouse_release_left()  # Make sure it's not stuck down
            time.sleep(0.001)     # Brief pause
            mouse_press_left()
            time.sleep(0.020)     # 20ms hold for rock-solid reliability
            mouse_release_left()
            
            if self.debug:
                print("  Left mouse click (working method)")
        except Exception as e:
            if self.debug:
                print(f"Left mouse click error: {e}")
    
    def _click_mouse_right(self):
        """Execute right mouse click using working method with timing control"""
        from sendinput import mouse_press_right, mouse_release_right
        try:
            # Ensure clean state first (from working version)
            mouse_release_right()  # Make sure it's not stuck down
            time.sleep(0.001)      # Brief pause
            mouse_press_right()
            time.sleep(0.020)      # 20ms hold for rock-solid reliability
            mouse_release_right()
            
            if self.debug:
                print("  Right mouse click (working method)")
        except Exception as e:
            if self.debug:
                print(f"Right mouse click error: {e}")
    
    def cleanup(self):
        """Clean up any held keys"""
        # Release sprint if active
        if self.sprint_active:
            self._release_key_direct('space')
            self.sprint_active = False
        
        # Release any other held keys
        for key_name in self.held_keys.copy():
            self._release_key_direct(key_name)
        
        if self.debug:
            print("✓ Face Turn Processor cleaned up")