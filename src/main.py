#!/usr/bin/env python3
"""
GoCube BLE Gaming Controller - Quaternion-Based Processing
Using official MsgOrientation format from GoCube documentation

Connection-focused update:
- Robust Windows discovery (handles random MACs) via BleakScanner
- Prefer connecting by name/service UUID instead of fixed MAC
- Retry with backoff; clean re-subscribe; soft reset of orientation stream
- No behavioral changes outside connection flow
"""

import asyncio
import time
import threading
from typing import Optional, List
from bleak import BleakClient, BleakScanner, BLEDevice
import pyautogui

# Import the queue system
from input_queue import InputQueueSystem, InputPriority, InputType

# Import the quaternion controller (UPDATED FOR ENHANCED VERSION)
from input_queue import AdvancedGyroController as QuaternionGyroController

# Import face turn processor
from face_turns import EnhancedFaceTurnProcessor

# Disable pyautogui failsafe for gaming
pyautogui.FAILSAFE = False


class GoCubeController:
    """
    GoCube Gaming Controller using official protocol documentation
    - MsgRotation (0x01): Face turns
    - MsgOrientation (0x03): Quaternion gyro data
    """
    
    def __init__(self, debug: bool = True):
        self.debug = debug
        self.client: Optional[BleakClient] = None
        self.connected = False
        
        # Initialize the input queue system
        self.input_queue = InputQueueSystem(
            base_delay_ms=1.0,
            max_queue_size=5,
            processing_rate_hz=200
        )
        
        # Initialize processors
        self.face_processor = EnhancedFaceTurnProcessor(
            input_queue=self.input_queue,
            debug=debug
        )
        
        self.gyro_controller = QuaternionGyroController(
            input_queue=self.input_queue,
            debug=debug
        )
        
        # GoCube BLE Service UUIDs (from documentation)
        self.GOCUBE_SERVICE_UUID = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
        self.RX_CHARACTERISTIC_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"  # Write
        self.TX_CHARACTERISTIC_UUID = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"  # Notify
        
        # Message types from documentation
        self.MSG_ROTATION = 0x01
        self.MSG_STATE = 0x02
        self.MSG_ORIENTATION = 0x03
        self.MSG_BATTERY = 0x05
        self.MSG_STATS = 0x07
        self.MSG_CUBE_TYPE = 0x08
        
        # Statistics
        self.stats = {
            'rotations': 0,
            'orientations': 0,
            'last_report': time.time()
        }
        
        self.running = False
        
        if self.debug:
            print("=" * 60)
            print("🎮 GoCube Gaming Controller - Official Protocol")
            print("=" * 60)
            print("✅ Using documented MsgOrientation quaternion format")
            print("✅ Proper packet parsing with checksums")
            print("✅ Quaternion to Euler angle conversion")
            print("✅ ENHANCED: Drift compensation and latency optimization")
            print("=" * 60)

    # ------------------------------
    # Connection helpers (Windows)
    # ------------------------------
    async def _discover_gocube(self, preferred_address: Optional[str]) -> Optional[BLEDevice]:
        """Find a GoCube by (a) exact address if resolvable; otherwise by name or service UUID.
        Why: Windows gives random BLE addresses per session; pairing shows 'Paired' but not 'Connected'."""
        # 1) Try to resolve the preferred address (if provided)
        if preferred_address:
            try:
                dev = await BleakScanner.find_device_by_address(preferred_address, timeout=6.0)
                if dev:
                    if self.debug:
                        print(f"🔎 Found device by preferred address: {dev.address} ({dev.name})")
                    return dev
            except Exception as e:
                if self.debug:
                    print(f"Address resolve failed ({preferred_address}): {e}")
        
        # 2) General discovery by name/service
        if self.debug:
            print("🔎 Scanning for GoCube / Rubik devices...")
        devices: List[BLEDevice] = await BleakScanner.discover(timeout=8.0)
        
        # Prefer devices exposing the Nordic UART Service UUID used by GoCube
        svc_match = [d for d in devices if hasattr(d, "metadata") and self.GOCUBE_SERVICE_UUID in (d.metadata or {}).get("uuids", [])]
        name_match = [d for d in devices if (d.name or "").startswith("GoCube") or (d.name or "").startswith("Rubik")]
        
        chosen = svc_match[0] if svc_match else (name_match[0] if name_match else None)
        if chosen and self.debug:
            print(f"✅ Discovered: {chosen.name or 'Unknown'} @ {chosen.address}")
        return chosen

    async def _connect_client(self, device: BLEDevice) -> bool:
        """Create BleakClient and establish a clean connection with retries."""
        # Ensure previous client is closed
        if self.client and self.client.is_connected:
            try:
                await self.client.disconnect()
            except Exception:
                pass
        
        self.client = BleakClient(device, timeout=30.0)
        tries = 3
        for attempt in range(1, tries + 1):
            try:
                if self.debug:
                    print(f"🔗 Connecting (attempt {attempt}/{tries}) to {device.name or 'Unknown'} @ {device.address}...")
                await self.client.connect()
                if not self.client.is_connected:
                    raise RuntimeError("Bleak connected=False")
                if self.debug:
                    print("✅ BLE connection established!")
                return True
            except Exception as e:
                if self.debug:
                    print(f"❌ Connect attempt {attempt} failed: {e}")
                await asyncio.sleep(1.0 * attempt)  # backoff
        return False

    async def _post_connect_setup(self) -> bool:
        """Subscribe and enable orientation stream; do a soft protocol reset to ensure notifications flow."""
        try:
            # Subscribe to TX characteristic for notifications
            await self.client.start_notify(self.TX_CHARACTERISTIC_UUID, self._notification_handler)
            
            # Soft-reset the orientation stream – some stacks need this after reconnect
            await self._send_command(0x37)  # DisableOrientation
            await asyncio.sleep(0.1)
            await self._send_command(0x38)  # EnableOrientation
            
            self.connected = True
            self.running = True
            
            if self.debug:
                print("✅ Subscribed to notifications")
                print("✅ Enabled MsgOrientation packets")
                print("\n" + "=" * 60)
                print("🎯 SYSTEM READY")
                print("=" * 60)
                print("• Place cube: White up, Green facing you")
                print("• System will auto-calibrate in 2 seconds")
                print("• Tilt for WASD movement")
                print("• Rotate for camera (O/P keys)")
                print("• Flip upside down to reset calibration")
                print("• ENHANCED: Automatic yaw drift compensation")
                print("=" * 60 + "\n")
            return True
        except Exception as e:
            if self.debug:
                print(f"❌ Post-connect setup failed: {e}")
            return False

    async def connect(self, device_address: str = "E6:EF:C6:B0:B8:A8") -> bool:
        """Connect to GoCube via BLE with robust Windows discovery.
        - Tries preferred address, otherwise discovers by name/service UUID
        - Retries connection; re-enables orientation notifications cleanly
        """
        try:
            dev = await self._discover_gocube(device_address)
            if not dev:
                if self.debug:
                    print("❌ No GoCube device found. Make sure it's paired in Windows Bluetooth and awake.")
                return False
            if not await self._connect_client(dev):
                return False
            return await self._post_connect_setup()
        except Exception as e:
            if self.debug:
                print(f"❌ Connection error: {e}")
            return False

    async def _send_command(self, command: int):
        """Send a command to the cube"""
        try:
            if self.client and self.client.is_connected:
                await self.client.write_gatt_char(self.RX_CHARACTERISTIC_UUID, bytes([command]))
        except Exception as e:
            if self.debug:
                print(f"Error sending command: {e}")

    async def reset_cube_orientation(self):
        """Reset cube orientation as if reconnecting - much more reliable than calibration"""
        try:
            if self.debug:
                print("🔄 Resetting cube orientation via protocol...")
            await self._send_command(0x37)  # DisableOrientation
            await asyncio.sleep(0.1)
            await self._send_command(0x38)  # EnableOrientation
            self.gyro_controller.protocol_reset()
            if self.debug:
                print("✅ Cube orientation reset complete - like fresh connection!")
        except Exception as e:
            if self.debug:
                print(f"Error during cube reset: {e}")
    
    def _notification_handler(self, sender, data: bytearray):
        """Handle incoming BLE notifications per official protocol"""
        try:
            data_bytes = bytes(data)
            if len(data_bytes) < 5 or data_bytes[0] != 0x2A:
                return
            msg_length = data_bytes[1]
            msg_type = data_bytes[2]
            # Optional checksum
            if len(data_bytes) >= msg_length:
                checksum = sum(data_bytes[0:msg_length-1]) % 0x100
                if checksum != data_bytes[msg_length-1]:
                    if self.debug:
                        print(f"Checksum mismatch: expected {checksum}, got {data_bytes[msg_length-1]}")
                    return
            if msg_type == self.MSG_ROTATION:
                self._process_rotation(data_bytes)
                self.stats['rotations'] += 1
            elif msg_type == self.MSG_ORIENTATION:
                self._process_orientation(data_bytes)
                self.stats['orientations'] += 1
            elif msg_type == self.MSG_BATTERY:
                self._process_battery(data_bytes)
            if time.time() - self.stats['last_report'] > 10:
                self._report_stats()
        except Exception as e:
            if self.debug:
                print(f"⚠ Error in notification handler: {e}")
    
    def _process_rotation(self, data: bytes):
        try:
            msg_length = data[1]
            for i in range(3, msg_length - 1, 2):
                if i + 1 < msg_length - 1:
                    face_rotation = data[i]
                    orientation = data[i + 1]
                    face_map = {
                        0x00: "B", 0x01: "B'",
                        0x02: "F", 0x03: "F'",
                        0x04: "U", 0x05: "U'",
                        0x06: "D", 0x07: "D'",
                        0x08: "R", 0x09: "R'",
                        0x0A: "L", 0x0B: "L'"
                    }
                    if face_rotation in face_map:
                        turn = face_map[face_rotation]
                        if self.debug:
                            print(f"🎲 Face turn: {turn} (orientation: {orientation})")
                        self.face_processor.process_turn(turn)
        except Exception as e:
            if self.debug:
                print(f"Error processing rotation: {e}")
    
    def _process_orientation(self, data: bytes):
        try:
            self.gyro_controller.process_gyro_packet(data)
        except Exception as e:
            if self.debug and self.stats['orientations'] % 100 == 0:
                print(f"Error processing orientation: {e}")
    
    def _process_battery(self, data: bytes):
        try:
            battery_level = data[3]
            if self.debug:
                print(f"🔋 Battery: {battery_level}%")
        except Exception as e:
            if self.debug:
                print(f"Error processing battery: {e}")
    
    def _report_stats(self):
        if self.debug:
            print(f"\n📊 Stats: {self.stats['rotations']} rotations, "
                  f"{self.stats['orientations']} orientations in last 10s")
        self.stats['rotations'] = 0
        self.stats['orientations'] = 0
        self.stats['last_report'] = time.time()
    
    async def disconnect(self):
        self.running = False
        if self.debug:
            print("\n🛑 Shutting down controller...")
        await self._send_command(0x37)  # DisableOrientation
        self.face_processor.cleanup()
        self.gyro_controller.cleanup()
        self.input_queue.shutdown()
        if self.client and self.client.is_connected:
            try:
                await self.client.disconnect()
                self.connected = False
                if self.debug:
                    print("✅ Disconnected from GoCube")
            except Exception as e:
                if self.debug:
                    print(f"Error disconnecting: {e}")
        if self.debug:
            print("✅ All systems shut down")
    
    def is_connected(self) -> bool:
        return self.connected and self.client and self.client.is_connected


async def main():
    print("\n" + "=" * 70)
    print(" " * 10 + "🎮 GOCUBE GAMING CONTROLLER 🎮")
    print("=" * 70)
    print("Using Official GoCube Protocol Documentation")
    print("Quaternion-based orientation tracking")
    print("ENHANCED: Drift compensation and latency optimization")
    print("=" * 70 + "\n")
    
    controller = GoCubeController(debug=True)
    
    # Make controller accessible for protocol reset
    import __main__
    __main__.controller = controller
    
    try:
        if await controller.connect():
            print("\n✅ CONTROLLER ACTIVE!")
            print("\n🎮 Controls:")
            print("  • Tilt Forward → W key")
            print("  • Tilt Backward → S key")
            print("  • Tilt Left → A key")
            print("  • Tilt Right → D key")
            print("  • Rotate Left/Right → O/P keys (camera)")
            print("  • Face turns → Combat actions")
            print("  • Numpad 5 → Protocol reset (like reconnecting)")
            print("  • ENHANCED: Automatic yaw drift compensation")
            print("\nPress Ctrl+C to stop\n")
            
            while controller.is_connected():
                await asyncio.sleep(1)
        else:
            print("\n❌ Failed to connect to GoCube")
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping controller...")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
    finally:
        await controller.disconnect()
        print("\n👋 Controller stopped")


if __name__ == "__main__":
    import sys
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())
