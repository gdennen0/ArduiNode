"""
DMX Bridge - High-performance sACN/ArtNet to Arduino DMX converter

A lightweight library for converting network DMX protocols (sACN/ArtNet) 
to physical DMX512 output via Arduino.
"""

import sacn
import serial
import serial.tools.list_ports
import time
import threading
import queue
import config

try:
    from stupidArtnet import StupidArtnetServer
    ARTNET_AVAILABLE = True
except ImportError:
    ARTNET_AVAILABLE = False


class DMXBridge:
    def __init__(self):
        self.ser = None
        self.receiver = None
        self.artnet_server = None
        self.protocol = config.PROTOCOL.lower()
        self.running = False
        
        # High-performance frame processing
        self.frame_queue = queue.Queue(maxsize=config.FRAME_BUFFER_SIZE)  # Buffer for frames
        self.output_thread = None
        self.last_frame_time = 0
        self.frame_count = 0
        self.fps_counter = 0
        self.fps_start_time = time.perf_counter()
        
        # DMX data management
        self.dmx_data = [0] * config.DMX_CHANNELS
        self.active = False
        self.last_active_state = False
        
        # Performance monitoring
        self.dropped_frames = 0
        self.processed_frames = 0
        self.fps = 0
        
    def connect(self):
        """Connect to Arduino"""
        try:
            print(f"  Attempting to open {config.ARDUINO_PORT} @ {config.ARDUINO_BAUD}...", flush=True)
            self.ser = serial.Serial(
                config.ARDUINO_PORT, 
                config.ARDUINO_BAUD, 
                timeout=1,
                write_timeout=0.1  # Prevent blocking on write
            )
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
    
    def start_protocol(self):
        """Start protocol receiver and output thread"""
        try:
            if self.protocol == "sacn":
                return self._start_sacn()
            elif self.protocol == "artnet":
                return self._start_artnet()
            else:
                print(f"✗ Unknown protocol: {self.protocol}")
                return False
        except Exception as e:
            print(f"✗ Protocol error: {e}")
            return False

    def _start_sacn(self):
        """Start sACN receiver"""
        try:
            # Start sACN receiver
            self.receiver = sacn.sACNreceiver()
            self.receiver.start()
            self.receiver.register_listener('universe', self._on_dmx, universe=config.SACN_UNIVERSE)
            self.receiver.join_multicast(config.SACN_UNIVERSE)
            print(f"✓ sACN listening on universe {config.SACN_UNIVERSE}")

            # Start high-performance output thread
            self.running = True
            self.output_thread = threading.Thread(target=self._output_worker, daemon=True)
            self.output_thread.start()
            print(f"✓ Output thread started at {config.OUTPUT_FPS} FPS")

            return True
        except Exception as e:
            print(f"✗ sACN error: {e}")
            return False

    def _start_artnet(self):
        """Start ArtNet receiver using stupidArtnet library"""
        try:
            if not ARTNET_AVAILABLE:
                print("✗ stupidArtnet library not installed")
                print("  Install with: pip install stupidArtnet")
                return False

            # Create ArtNet server/receiver
            # StupidArtnetServer listens for ArtNet packets on the specified universe
            self.artnet_server = StupidArtnetServer()
            
            # Register callback for our universe
            self.artnet_server.register_listener(
                universe=config.ARTNET_UNIVERSE,
                callback_function=self._on_artnet_dmx
            )
            
            print(f"✓ ArtNet listening on universe {config.ARTNET_UNIVERSE}")

            # Start high-performance output thread
            self.running = True
            self.output_thread = threading.Thread(target=self._output_worker, daemon=True)
            self.output_thread.start()
            print(f"✓ Output thread started at {config.OUTPUT_FPS} FPS")

            return True
        except Exception as e:
            print(f"✗ ArtNet error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _on_dmx(self, packet):
        """Handle DMX packet - optimized for high performance"""
        try:
            # Get DMX data and pad/truncate to expected length
            data = list(packet.dmxData)
            if len(data) < config.DMX_CHANNELS:
                data.extend([0] * (config.DMX_CHANNELS - len(data)))
            elif len(data) > config.DMX_CHANNELS:
                data = data[:config.DMX_CHANNELS]

            # Update internal data
            self.dmx_data = data

            # Check activity state
            has_data = any(v > 0 for v in data)
            if has_data != self.last_active_state:
                self.active = has_data
                self.last_active_state = has_data
                print(f"DMX {'ACTIVE' if has_data else 'INACTIVE'}")

            # Add to processing queue (non-blocking)
            try:
                self.frame_queue.put_nowait(data)
                self.processed_frames += 1
            except queue.Full:
                self.dropped_frames += 1
                # Remove oldest frame and add new one
                try:
                    self.frame_queue.get_nowait()
                    self.frame_queue.put_nowait(data)
                except queue.Empty:
                    pass

        except Exception as e:
            print(f"Error processing DMX packet: {e}")

    def _on_artnet_dmx(self, data):
        """Handle ArtNet DMX packet - optimized for high performance
        
        stupidArtnet callback receives just the data buffer (bytearray)
        """
        try:
            # Convert to list
            data = list(data)

            # Pad/truncate to expected length
            if len(data) < config.DMX_CHANNELS:
                data.extend([0] * (config.DMX_CHANNELS - len(data)))
            elif len(data) > config.DMX_CHANNELS:
                data = data[:config.DMX_CHANNELS]

            # Update internal data
            self.dmx_data = data

            # Check activity state
            has_data = any(v > 0 for v in data)
            if has_data != self.last_active_state:
                self.active = has_data
                self.last_active_state = has_data
                print(f"ArtNet DMX {'ACTIVE' if has_data else 'INACTIVE'}")

            # Add to processing queue (non-blocking)
            try:
                self.frame_queue.put_nowait(data)
                self.processed_frames += 1
            except queue.Full:
                self.dropped_frames += 1
                # Remove oldest frame and add new one
                try:
                    self.frame_queue.get_nowait()
                    self.frame_queue.put_nowait(data)
                except queue.Empty:
                    pass

        except Exception as e:
            print(f"Error processing ArtNet DMX packet: {e}")
    
    def _output_worker(self):
        """High-performance output thread running at 2x DMX rate"""
        target_interval = 1.0 / config.OUTPUT_FPS  # 2x DMX rate
        next_send_time = time.perf_counter()
        
        while self.running:
            current_time = time.perf_counter()
            
            # Check if it's time to send
            if current_time >= next_send_time:
                try:
                    # Get latest frame (non-blocking)
                    frame_data = self.frame_queue.get_nowait()
                    self._send_frame_to_arduino(frame_data)
                    self.fps_counter += 1
                except queue.Empty:
                    # No new frame, send last known data
                    if self.dmx_data:
                        self._send_frame_to_arduino(self.dmx_data)
                        self.fps_counter += 1
                except Exception as e:
                    print(f"Output worker error: {e}")
                
                # Calculate next send time for precise timing
                next_send_time += target_interval
                
                # Prevent drift if we fall behind
                if next_send_time < current_time:
                    next_send_time = current_time + target_interval
            else:
                # Precise sleep until next send time
                sleep_time = next_send_time - current_time
                if sleep_time > 0.0001:  # Only sleep if > 0.1ms
                    time.sleep(sleep_time * 0.5)  # Sleep half the remaining time
    
    def _send_frame_to_arduino(self, data):
        """Send optimized frame to Arduino"""
        if not self.ser or not self.ser.is_open:
            return
        
        try:
            # Pre-build packet structure for maximum speed
            # [0xFF, len_lo, len_hi, data...]
            packet = bytearray(3 + len(data))
            packet[0] = 0xFF
            packet[1] = config.DMX_CHANNELS & 0xFF
            packet[2] = (config.DMX_CHANNELS >> 8) & 0xFF
            packet[3:] = data
            
            # Write packet (non-blocking)
            self.ser.write(packet)
            
        except Exception as e:
            print(f"Serial write error: {e}")
    
    def send_test(self, pattern='all_off'):
        """Send test pattern - updates internal DMX data for output worker to send"""
        data = [0] * config.DMX_CHANNELS
        
        if pattern == 'all_on':
            data = [255] * config.DMX_CHANNELS
        elif pattern == 'first_5':
            data[:5] = [255] * 5
        elif pattern == 'dim':
            data = [128] * config.DMX_CHANNELS
        
        # Update internal DMX data
        self.dmx_data = data
        
        # Add to processing queue so output worker sends it
        try:
            # Clear the queue first to make test pattern immediate
            while not self.frame_queue.empty():
                try:
                    self.frame_queue.get_nowait()
                except queue.Empty:
                    break
            
            # Add test pattern multiple times to ensure it's sent
            for _ in range(5):
                try:
                    self.frame_queue.put_nowait(data)
                except queue.Full:
                    break
        except Exception as e:
            print(f"Queue error: {e}")
        
        print(f"✓ Test pattern: {pattern} (queued for output)")
    
    def get_fps(self):
        """Get current FPS with performance stats"""
        current_time = time.perf_counter()
        elapsed = current_time - self.fps_start_time
        
        if elapsed >= 1.0:  # Update every second
            self.fps = self.fps_counter / elapsed
            self.fps_counter = 0
            self.fps_start_time = current_time
            
            # Print performance stats only if monitoring is enabled
            if config.PERFORMANCE_MONITORING and (self.dropped_frames > 0 or self.processed_frames > 0):
                drop_rate = (self.dropped_frames / (self.dropped_frames + self.processed_frames)) * 100
                if drop_rate > 5.0:  # Only warn if drop rate is significant
                    print(f"\nPerformance: {self.fps:.1f} FPS, {drop_rate:.1f}% dropped frames")
        
        return int(self.fps)
    
    def get_performance_stats(self):
        """Get detailed performance statistics"""
        total_frames = self.processed_frames + self.dropped_frames
        drop_rate = (self.dropped_frames / total_frames * 100) if total_frames > 0 else 0
        
        return {
            'fps': self.fps,
            'processed_frames': self.processed_frames,
            'dropped_frames': self.dropped_frames,
            'drop_rate': drop_rate,
            'active': self.active
        }
    
    def shutdown(self):
        """Stop everything gracefully"""
        print("\nShutting down...")
        self.running = False

        # Wait for threads to finish
        if self.output_thread and self.output_thread.is_alive():
            self.output_thread.join(timeout=1.0)

        # Stop sACN receiver
        if self.receiver:
            self.receiver.stop()

        # Stop ArtNet server
        if self.artnet_server:
            try:
                self.artnet_server.close()
            except:
                pass

        # Close serial connection
        if self.ser and self.ser.is_open:
            self.ser.close()

        # Print final stats
        stats = self.get_performance_stats()
        print(f"Final stats: {stats['fps']:.1f} FPS, {stats['drop_rate']:.1f}% dropped")
        print("✓ Shutdown complete")
