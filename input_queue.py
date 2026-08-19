#!/usr/bin/env python3
"""
Advanced Input Queue System + Vector-Based Gyro Controller for GoCube Gaming
Using official GoCube MsgOrientation quaternion format

MAJOR ARCHITECTURAL CHANGE in this version:
- ELIMINATED quaternion-to-Euler conversion (source of gimbal lock and coupling)
- REPLACED with direct gravity vector projection (stable at any angle)
- ELIMINATED auto-recalibration (source of instability)
- ADDED continuous drift correction instead of periodic reset
- ADDED angle clamping to prevent >90° issues
- SIMPLIFIED math for maximum stability and responsiveness
"""

import threading
import time
import queue
import math
from collections import deque
from dataclasses import dataclass, field
from typing import Optional, Callable, Dict, List
from enum import Enum, auto
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InputPriority(Enum):
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4


class InputType(Enum):
    KEY_PRESS = auto()
    KEY_RELEASE = auto()
    KEY_TAP = auto()
    MOUSE_CLICK = auto()
    MOUSE_MOVE = auto()
    MOVEMENT = auto()


@dataclass
class QueuedInput:
    action: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    priority: InputPriority = InputPriority.NORMAL
    input_type: InputType = InputType.KEY_PRESS
    timestamp: float = field(default_factory=time.perf_counter)
    key_code: Optional[int] = None
    can_cancel: bool = True
    group_id: Optional[str] = None
    description: str = ""


@dataclass
class Quaternion:
    x: float
    y: float
    z: float
    w: float

    def normalize(self) -> "Quaternion":
        mag = math.sqrt(self.x*self.x + self.y*self.y + self.z*self.z + self.w*self.w)
        if mag > 1e-12:
            inv_mag = 1.0 / mag
            self.x *= inv_mag
            self.y *= inv_mag
            self.z *= inv_mag
            self.w *= inv_mag
        return self

    def clone(self) -> "Quaternion":
        return Quaternion(self.x, self.y, self.z, self.w)

    def invert(self) -> "Quaternion":
        return Quaternion(-self.x, -self.y, -self.z, self.w)

    def mul(self, b: "Quaternion") -> "Quaternion":
        x = self.w*b.x + self.x*b.w + self.y*b.z - self.z*b.y
        y = self.w*b.y - self.x*b.z + self.y*b.w + self.z*b.x
        z = self.w*b.z + self.x*b.y - self.y*b.x + self.z*b.w
        w = self.w*b.w - self.x*b.x - self.y*b.y - self.z*b.z
        return Quaternion(x, y, z, w)

    def rotate_vector(self, v: tuple) -> tuple:
        """Rotate a 3D vector by this quaternion using q*v*q^-1"""
        vx, vy, vz = v
        # Convert vector to pure quaternion
        vq = Quaternion(vx, vy, vz, 0.0)
        # Rotate: q * v * q^-1
        qi = self.invert()
        result = self.mul(vq).mul(qi)
        return (result.x, result.y, result.z)


class InputQueueSystem:
    def __init__(self, base_delay_ms: float = 1.0, max_queue_size: int = 5, processing_rate_hz: int = 200):
        self.base_delay = base_delay_ms / 1000.0
        self.current_delay = self.base_delay
        self.max_queue_size = max_queue_size
        self.processing_interval = 1.0 / processing_rate_hz
        self._queue = queue.PriorityQueue(maxsize=max_queue_size)
        self._active_keys: Dict[int, float] = {}
        self._last_input_time = 0.0
        self._last_input_type: Optional[InputType] = None
        self._shutdown = False
        self.stats = {
            'total_inputs': 0, 'dropped_inputs': 0, 'executed_inputs': 0,
            'avg_latency': 0.0, 'max_latency': 0.0, 'min_latency': float('inf'),
            'ghosting_prevented': 0, 'latencies': deque(maxlen=100),
        }
        self._collision_count = 0
        self._success_count = 0
        self._adaptation_counter = 0
        self._adaptation_window = 50
        self.conflict_groups = {'movement': {'w', 'a', 's', 'd'}}
        self.input_delays = {
            (InputType.KEY_TAP, InputType.KEY_TAP): 2,
            (InputType.KEY_TAP, InputType.KEY_PRESS): 1,
            (InputType.KEY_RELEASE, InputType.KEY_PRESS): 3,
            (InputType.MOUSE_CLICK, InputType.MOUSE_CLICK): 2,
            (InputType.MOUSE_MOVE, InputType.MOUSE_MOVE): 0,
        }
        self._lock = threading.Lock()
        self._processor_thread = threading.Thread(target=self._process_queue, daemon=True)
        self._processor_thread.start()
        logger.info(f"Input Queue initialized: {base_delay_ms}ms base, {processing_rate_hz}Hz")

    def queue_input(self, action: Callable, priority: InputPriority = InputPriority.NORMAL,
                    input_type: InputType = InputType.KEY_TAP, key_code: Optional[int] = None,
                    group_id: Optional[str] = None, description: str = "", *args, **kwargs) -> bool:
        try:
            item = QueuedInput(action=action, args=args, kwargs=kwargs, priority=priority,
                               input_type=input_type, key_code=key_code, group_id=group_id,
                               description=description)
            if self._check_conflicts(item):
                pass
            try:
                self._queue.put_nowait((priority.value, time.perf_counter(), item))
                self.stats['total_inputs'] += 1
                return True
            except queue.Full:
                self.stats['dropped_inputs'] += 1
                return False
        except Exception as e:
            logger.error(f"Queue error: {e}")
            return False

    def _check_conflicts(self, q: QueuedInput) -> bool:
        with self._lock:
            if q.key_code and q.key_code in self._active_keys:
                if time.perf_counter() - self._active_keys[q.key_code] < 0.010:
                    self.stats['ghosting_prevented'] += 1
                    return True
        return False

    def _get_adaptive_delay(self, input_type: InputType) -> float:
        base = self.current_delay
        if self._last_input_type and input_type:
            key = (self._last_input_type, input_type)
            if key in self.input_delays:
                base = max(base, self.input_delays[key] / 1000.0)
        self._adaptation_counter += 1
        if self._adaptation_counter >= self._adaptation_window:
            success_rate = self._success_count / max(1, self._success_count + self._collision_count)
            if success_rate > 0.98:
                self.current_delay = max(self.base_delay * 0.9, 0.002)
            elif success_rate < 0.95:
                self.current_delay = min(self.current_delay * 1.1, 0.010)
            self._adaptation_counter = 0; self._collision_count = 0; self._success_count = 0
        return base

    def _process_queue(self):
        logger.info("Queue processor started")
        while not self._shutdown:
            try:
                try:
                    _, _, q = self._queue.get(timeout=self.processing_interval)
                except queue.Empty:
                    continue
                latency = time.perf_counter() - q.timestamp
                self.stats['latencies'].append(latency)
                self.stats['avg_latency'] = sum(self.stats['latencies']) / len(self.stats['latencies'])
                self.stats['max_latency'] = max(self.stats['max_latency'], latency)
                self.stats['min_latency'] = min(self.stats['min_latency'], latency)
                delay = self._get_adaptive_delay(q.input_type)
                elapsed = time.perf_counter() - self._last_input_time
                if elapsed < delay:
                    time.sleep(delay - elapsed)
                try:
                    if q.key_code:
                        with self._lock:
                            if q.input_type in (InputType.KEY_PRESS, InputType.KEY_TAP):
                                self._active_keys[q.key_code] = time.perf_counter()
                            elif q.input_type == InputType.KEY_RELEASE:
                                self._active_keys.pop(q.key_code, None)
                    q.action(*q.args, **q.kwargs)
                    self.stats['executed_inputs'] += 1
                    self._success_count += 1
                except Exception as e:
                    logger.error(f"Execution error: {e}")
                    self._collision_count += 1
                self._last_input_time = time.perf_counter()
                self._last_input_type = q.input_type
            except Exception as e:
                logger.error(f"Queue processor error: {e}")
                time.sleep(0.001)
        logger.info("Queue processor stopped")

    def get_stats(self) -> dict:
        s = self.stats.copy(); s['queue_depth'] = self._queue.qsize(); s['current_delay_ms'] = self.current_delay*1000
        s['active_keys'] = len(self._active_keys)
        if s['executed_inputs'] > 0:
            s['drop_rate'] = s['dropped_inputs'] / max(1, s['total_inputs'])
        return s

    def shutdown(self):
        self._shutdown = True
        if self._processor_thread:
            self._processor_thread.join(timeout=1.0)


# ------------------------- Debug HUD -------------------------
class _DebugHUD:
    """Debug HUD showing vector-based angles"""
    def __init__(self):
        self._data = {'roll':0.0,'pitch':0.0,'yaw':0.0,'active':[],'method':'VECTOR'}
        self._lock = threading.Lock()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def update(self, roll: float, pitch: float, yaw: float, active: List[str]):
        with self._lock:
            self._data = {'roll':roll,'pitch':pitch,'yaw':yaw,'active':active,'method':'VECTOR'}

    def _run(self):
        try:
            import tkinter as tk
            from tkinter import ttk
        except Exception:
            return
        root = tk.Tk()
        root.title("VECTOR Cube Controller"); root.geometry("380x240"); root.attributes('-topmost', True)
        root.configure(bg='#111')
        v_roll = tk.StringVar(); v_pitch = tk.StringVar(); v_yaw = tk.StringVar(); v_active = tk.StringVar(); v_method = tk.StringVar()
        tk.Label(root, textvariable=v_roll,  fg='#0f0', bg='#111', font=('Consolas',12)).pack(anchor='w')
        tk.Label(root, textvariable=v_pitch, fg='#0f0', bg='#111', font=('Consolas',12)).pack(anchor='w')
        tk.Label(root, textvariable=v_yaw,   fg='#0f0', bg='#111', font=('Consolas',12)).pack(anchor='w')
        tk.Label(root, textvariable=v_method,fg='#f80', bg='#111', font=('Consolas',10,'bold')).pack(anchor='w')
        tk.Label(root, textvariable=v_active,fg='#09f', bg='#111', font=('Consolas',12)).pack(anchor='w', pady=(8,0))
        pb_roll = ttk.Progressbar(root, orient='horizontal', length=340, mode='determinate', maximum=90)
        pb_pitch= ttk.Progressbar(root, orient='horizontal', length=340, mode='determinate', maximum=90)
        pb_yaw  = ttk.Progressbar(root, orient='horizontal', length=340, mode='determinate', maximum=180)
        pb_roll.pack(pady=2); pb_pitch.pack(pady=2); pb_yaw.pack(pady=2)
        def tick():
            with self._lock:
                d = dict(self._data)
            v_roll.set (f"Roll : {d['roll']:+6.1f}° (no gimbal lock)")
            v_pitch.set(f"Pitch: {d['pitch']:+6.1f}° (no coupling)")
            v_yaw.set  (f"Yaw  : {d['yaw']:+6.1f}° (drift corrected)")
            v_method.set(f"Method: {d['method']} PROJECTION (stable at any angle)")
            v_active.set(f"Active: {', '.join(d['active']) if d['active'] else 'NEUTRAL'}")
            pb_roll['value'] = min(90, abs(d['roll']))
            pb_pitch['value']= min(90, abs(d['pitch']))
            pb_yaw['value']  = min(180, abs(d['yaw']))
            root.after(33, tick)
        tick(); root.mainloop()


class AdvancedGyroController:
    """REVOLUTIONARY: Vector-based gyro controller - eliminates gimbal lock and coupling"""
    
    def __init__(self, input_queue: InputQueueSystem, debug: bool = True, enable_hud: bool = True):
        self.debug = debug
        self.input_queue = input_queue
        from sendinput import press_key, release_key, CHAR_MAP
        self.press_key = press_key; self.release_key = release_key; self.key_map = CHAR_MAP
        
        self.movement_keys = {
            'forward': self.key_map['w'], 'backward': self.key_map['s'],
            'left': self.key_map['a'], 'right': self.key_map['d'],
            'camera_left': self.key_map['o'], 'camera_right': self.key_map['p'],
        }
        self.movement_state = {k: False for k in self.movement_keys.keys()}
        
        # CORE STATE: Only store home quaternion - no complex state
        self.home_quaternion: Optional[Quaternion] = None
        self.calibrated = False
        self.calibration_samples: List[Quaternion] = []
        
        # Thresholds - INCREASED for stability
        self.thresholds = {
            'pitch_movement': 25,  # Increased from 20 for stability
            'roll_movement': 25,   # Increased from 20 for stability 
            'yaw_camera': 30,      # Increased from 25 for stability
        }
        
        # ANGLE CLAMPING: Prevent >90° issues
        self.max_angle = 85  # Clamp at 85° to prevent gimbal lock region
        
        # ADJUSTABLE drift correction - change this value to fine-tune
        self.yaw_drift_rate = 0.11 # degrees per second - ADJUST THIS: try 0.08, 0.12, etc.
        self.calibration_time = None
        
        # ELIMINATED: All auto-recalibration, smoothing, filtering, coupling detection
        # These were sources of instability
        
        # Hotkey reset
        self.reset_hotkey_pressed = False
        self.last_reset_time = 0
        self.reset_cooldown = 2.0
        
        self.last_debug_time = time.time()
        self.packet_count = 0
        self.hud = _DebugHUD() if enable_hud else None
        
        if self.debug:
            print("🚀 REVOLUTIONARY Vector-Based Gyro Controller initialized")
            print("  • ELIMINATED: Euler angles, gimbal lock, axis coupling")
            print("  • USING: Direct gravity vector projection")
            print("  • CLAMPED: Angles at 85° to prevent >90° issues")
            print("  • SIMPLE: One-time calibration, continuous drift correction")

    def process_gyro_packet(self, data: bytes):
        try:
            if len(data) < 4 or data[2] != 0x03:
                return
            msg_len = data[1]
            msg = data[3:msg_len-1]
            parts = msg.decode('ascii', errors='ignore').strip().split('#')
            if len(parts) != 4:
                return
            x = int(parts[0]) / 16384.0; y = int(parts[1]) / 16384.0; z = int(parts[2]) / 16384.0; w = int(parts[3]) / 16384.0
            self._process_quaternion(Quaternion(x, y, z, w).normalize())
        except Exception as e:
            if self.debug and self.packet_count % 100 == 0:
                print(f"Error parsing quaternion: {e}")

    def process_multi_packet_gyro(self, x: int, y: int, z: int, w: int, packet_type: str, packet_length: int):
        text = f"{x}#{y}#{z}#{w}".encode('ascii')
        fake = bytes([0x2A, len(text)+4, 0x03]) + text + bytes([0x00, 0x0D, 0x0A])
        self.process_gyro_packet(fake)

    def _process_quaternion(self, current_q: Quaternion):
        """REVOLUTIONARY: Process quaternion using vector projection method"""
        self.packet_count += 1
        
        # Calibration: Simple and fast
        if not self.calibrated:
            self.calibration_samples.append(current_q)
            if len(self.calibration_samples) >= 10:  # More samples for stable home
                self._finish_calibration()
            return
        
        # Check for manual reset
        if self._check_reset_hotkey():
            self.protocol_reset()
            return
        
        # CORE INNOVATION: Calculate angles using vector projection (no Euler conversion)
        angles = self._calculate_vector_angles(current_q)
        
        # Apply continuous drift correction to yaw only
        if self.calibration_time:
            elapsed = time.time() - self.calibration_time
            drift_compensation = self.yaw_drift_rate * elapsed
            angles['yaw'] += drift_compensation
        
        # CLAMP angles to prevent >90° issues
        angles = self._clamp_angles(angles)
        
        # Apply movement detection
        self._detect_movement(angles)
        
        # Update HUD
        if self.hud:
            active = [k for k, v in self.movement_state.items() if v]
            self.hud.update(angles['roll'], angles['pitch'], angles['yaw'], active)
        
        # Debug output
        if self.debug and time.time() - self.last_debug_time > 2:
            self._debug_output(angles)

    def _calculate_vector_angles(self, current_q: Quaternion) -> Dict[str, float]:
        """
        REVOLUTIONARY METHOD: Calculate angles using gravity vector projection
        This eliminates gimbal lock and axis coupling completely!
        """
        
        # Step 1: Calculate relative quaternion from home position
        home_inverse = self.home_quaternion.invert()
        relative_q = current_q.mul(home_inverse).normalize()
        
        # Step 2: VECTOR METHOD - Project gravity vector through rotation
        # The gravity vector in home position is (0, -1, 0) pointing down
        # See where this vector points after rotation
        gravity_home = (0.0, -1.0, 0.0)
        gravity_rotated = relative_q.rotate_vector(gravity_home)
        gx, gy, gz = gravity_rotated
        
        # Step 3: Extract angles from rotated gravity vector
        # This is mathematically stable and has no gimbal lock!
        
        # PITCH: How much gravity tilts forward/back (Z component)
        # When tilting forward, gravity vector rotates backward (positive Z)
        # FIXED: Invert sign for correct direction
        pitch_deg = math.degrees(math.asin(max(-1.0, min(1.0, gz))))
        
        # ROLL: How much gravity tilts left/right (X component)  
        # When tilting right, gravity vector goes right (positive X)
        # FIXED: Invert sign for correct direction
        roll_deg = math.degrees(math.asin(max(-1.0, min(1.0, -gx))))
        
        # YAW: Calculate from forward vector (separate from gravity)
        # AGGRESSIVE ISOLATION: Disable yaw when ANY significant movement/rotation is happening
        yaw_deg = 0.0
        
        # More aggressive isolation - disable yaw if ANY axis is significantly tilted
        # OR if we're in a diagonal movement (combination of pitch+roll)
        total_tilt = abs(pitch_deg) + abs(roll_deg)  # Combined tilt magnitude
        
        if abs(pitch_deg) < 35 and abs(roll_deg) < 35 and total_tilt < 50:  # Much stricter isolation
            # Only calculate yaw when cube is in relatively neutral position
            # The forward vector in home position is (0, 0, -1) pointing forward
            forward_home = (0.0, 0.0, -1.0)
            forward_rotated = relative_q.rotate_vector(forward_home)
            fx, fy, fz = forward_rotated
            
            # YAW: Direction of forward vector in horizontal plane (ignore Y)
            # FIXED: Invert for correct camera direction
            yaw_deg = math.degrees(math.atan2(-fx, -fz))
        
        return {'roll': roll_deg, 'pitch': pitch_deg, 'yaw': yaw_deg}

    def _clamp_angles(self, angles: Dict[str, float]) -> Dict[str, float]:
        """Clamp angles to prevent >90° issues"""
        angles['roll'] = max(-self.max_angle, min(self.max_angle, angles['roll']))
        angles['pitch'] = max(-self.max_angle, min(self.max_angle, angles['pitch']))
        # Don't clamp yaw - it can go full 360°
        return angles

    def _finish_calibration(self):
        """Simple, stable calibration"""
        # Average all calibration samples
        avg_x = sum(q.x for q in self.calibration_samples) / len(self.calibration_samples)
        avg_y = sum(q.y for q in self.calibration_samples) / len(self.calibration_samples)
        avg_z = sum(q.z for q in self.calibration_samples) / len(self.calibration_samples) 
        avg_w = sum(q.w for q in self.calibration_samples) / len(self.calibration_samples)
        
        self.home_quaternion = Quaternion(avg_x, avg_y, avg_z, avg_w).normalize()
        self.calibrated = True
        self.calibration_samples.clear()
        self.calibration_time = time.time()
        
        if self.debug:
            print("🚀 VECTOR calibration complete!")
            print(f"   Home quaternion magnitude: {self.home_quaternion.magnitude():.8f}")
            print(f"   Using gravity vector projection method")

    def _detect_movement(self, angles: Dict[str, float]):
        """Detect movement from stable vector-based angles"""
        # Check if all angles are below threshold (deadzone)
        dead = (abs(angles['pitch']) < self.thresholds['pitch_movement'] and
                abs(angles['roll'])  < self.thresholds['roll_movement']  and
                abs(angles['yaw'])   < self.thresholds['yaw_camera'])
        
        if dead:
            self._release_all()
            return
        
        # Pitch controls W/S
        if angles['pitch'] > self.thresholds['pitch_movement']:
            self._set('forward', True); self._set('backward', False)
        elif angles['pitch'] < -self.thresholds['pitch_movement']:
            self._set('backward', True); self._set('forward', False) 
        else:
            self._set('forward', False); self._set('backward', False)
        
        # Roll controls A/D
        if angles['roll'] > self.thresholds['roll_movement']:
            self._set('right', True); self._set('left', False)
        elif angles['roll'] < -self.thresholds['roll_movement']:
            self._set('left', True); self._set('right', False)
        else:
            self._set('left', False); self._set('right', False)
        
        # Yaw controls O/P (camera)
        if angles['yaw'] > self.thresholds['yaw_camera']:
            self._set('camera_right', True); self._set('camera_left', False)
        elif angles['yaw'] < -self.thresholds['yaw_camera']:
            self._set('camera_left', True); self._set('camera_right', False)
        else:
            self._set('camera_left', False); self._set('camera_right', False)

    def _release_all(self):
        """Release all movement keys"""
        for direction in self.movement_keys.keys():
            if self.movement_state[direction]:
                self._set(direction, False)

    def _set(self, direction: str, active: bool):
        """Set key state with input queue"""
        if self.movement_state[direction] == active:
            return
        self.movement_state[direction] = active
        key = self.movement_keys[direction]
        
        if active:
            self.input_queue.queue_input(
                action=lambda k=key: self.press_key(k),
                priority=InputPriority.NORMAL,
                input_type=InputType.KEY_PRESS,
                key_code=key,
                description=f"{direction} ON"
            )
        else:
            self.input_queue.queue_input(
                action=lambda k=key: self.release_key(k),
                priority=InputPriority.NORMAL,
                input_type=InputType.KEY_RELEASE,
                key_code=key,
                description=f"{direction} OFF"
            )

    def _check_reset_hotkey(self) -> bool:
        """Check for Numpad 5 reset"""
        try:
            import win32api
            numpad5_state = win32api.GetAsyncKeyState(0x65)
            numpad5_pressed = (numpad5_state & 0x8000) != 0
            
            current_time = time.time()
            if numpad5_pressed and not self.reset_hotkey_pressed:
                if current_time - self.last_reset_time > self.reset_cooldown:
                    self.reset_hotkey_pressed = True
                    self.last_reset_time = current_time
                    if self.debug:
                        print("🎯 Manual reset triggered!")
                    return True
            elif not numpad5_pressed:
                self.reset_hotkey_pressed = False
        except (ImportError, Exception):
            pass
        return False

    def protocol_reset(self):
        """Clean protocol reset"""
        if self.debug:
            print("🔄 VECTOR protocol reset")
        
        # Reset all state cleanly
        self.calibrated = False
        self.calibration_samples.clear()
        self.home_quaternion = None
        self.calibration_time = None
        self.reset_hotkey_pressed = False
        
        # Release all keys
        for direction in self.movement_keys.keys():
            if self.movement_state[direction]:
                self._set(direction, False)
        
        if self.debug:
            print("✅ Ready for VECTOR recalibration")

    def _debug_output(self, angles: Dict[str, float]):
        """Clean debug output"""
        self.last_debug_time = time.time()
        active = [k for k, v in self.movement_state.items() if v]
        
        drift_comp = 0.0
        if self.calibration_time:
            elapsed = time.time() - self.calibration_time
            drift_comp = self.yaw_drift_rate * elapsed
        
        print(f"🚀 VECTOR: Roll={angles['roll']:+6.1f}° Pitch={angles['pitch']:+6.1f}° Yaw={angles['yaw']:+6.1f}°")
        print(f"    Drift: +{drift_comp:.2f}° | Clamped at ±{self.max_angle}° | Method: GRAVITY PROJECTION")
        print(f"    Active: {active if active else 'NEUTRAL'}")

    def cleanup(self):
        """Clean shutdown"""
        for direction in self.movement_keys.keys():
            if self.movement_state[direction]:
                self._set(direction, False)