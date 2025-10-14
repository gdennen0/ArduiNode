"""DMX Bridge - Simple sACN to Arduino converter"""

import sacn
import serial
import serial.tools.list_ports
import time
import threading
import config


class DMXBridge:
    def __init__(self):
        self.ser = None
        self.receiver = None
        self.running = False
        self.last_send = 0
        self.frame_count = 0
        self.fps = 0
        self.dmx_data = [0] * config.DMX_CHANNELS
        self.active = False
        
    def connect(self):
        """Connect to Arduino"""
        try:
            print(f"  Attempting to open {config.ARDUINO_PORT} @ {config.ARDUINO_BAUD}...", flush=True)
            self.ser = serial.Serial(config.ARDUINO_PORT, config.ARDUINO_BAUD, timeout=1)
            print(f"  Port opened successfully")
            print(f"  Note: Shield TX→D4 (TX-IO), RX→D3 (RX-IO), D2=HIGH (TX mode)")
            print(f"        USB Serial is dedicated to PC link; DMX driven via D4")
            time.sleep(0.5)
            
            print(f"✓ Arduino connected on {config.ARDUINO_PORT}")
            return True
        except serial.SerialException as e:
            print(f"✗ Serial port error: {e}")
            print(f"  Port {config.ARDUINO_PORT} may be in use by another program")
            self._list_ports()
            return False
        except Exception as e:
            print(f"✗ Arduino error: {e}")
            self._list_ports()
            return False
    
    def _list_ports(self):
        """List available ports"""
        print("\nAvailable ports:")
        for port in serial.tools.list_ports.comports():
            print(f"  {port.device}: {port.description}")
    
    def start_sacn(self):
        """Start sACN receiver"""
        try:
            self.receiver = sacn.sACNreceiver()
            self.receiver.start()
            self.receiver.register_listener('universe', self._on_dmx, universe=config.SACN_UNIVERSE)
            self.receiver.join_multicast(config.SACN_UNIVERSE)
            print(f"✓ Listening on universe {config.SACN_UNIVERSE}")
            return True
        except Exception as e:
            print(f"✗ sACN error: {e}")
            return False
    
    def _on_dmx(self, packet):
        """Handle DMX packet"""
        current = time.time()
        if (current - self.last_send) < (1.0 / config.DMX_FPS):
            return
        
        self.last_send = current
        self.frame_count += 1
        
        data = packet.dmxData
        self.dmx_data = list(data)
        
        # Check if active
        has_data = any(v > 0 for v in data)
        if has_data != self.active:
            self.active = has_data
            print(f"DMX {'ACTIVE' if has_data else 'INACTIVE'}")
        
        # Send to Arduino
        packet = bytearray([0xFF, config.DMX_CHANNELS & 0xFF, (config.DMX_CHANNELS >> 8) & 0xFF])
        for i in range(config.DMX_CHANNELS):
            packet.append(data[i] if i < len(data) else 0)
        
        if self.ser and self.ser.is_open:
            self.ser.write(packet)
    
    def send_test(self, pattern='all_off'):
        """Send test pattern"""
        data = [0] * config.DMX_CHANNELS
        
        if pattern == 'all_on':
            data = [255] * config.DMX_CHANNELS
        elif pattern == 'first_5':
            data[:5] = [255] * 5
        elif pattern == 'dim':
            data = [128] * config.DMX_CHANNELS
        
        packet = bytearray([0xFF, config.DMX_CHANNELS & 0xFF, (config.DMX_CHANNELS >> 8) & 0xFF])
        packet.extend(data)
        
        if self.ser and self.ser.is_open:
            self.ser.write(packet)
            print(f"✓ Test pattern: {pattern}")
    
    def get_fps(self):
        """Get current FPS"""
        fps = self.frame_count
        self.frame_count = 0
        return fps
    
    def shutdown(self):
        """Stop everything"""
        self.running = False
        if self.receiver:
            self.receiver.stop()
        if self.ser and self.ser.is_open:
            self.ser.close()
        print("✓ Shutdown complete")
