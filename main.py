"""
DMX Bridge - Command Line Interface

Simple CLI for controlling the DMX bridge with real-time status monitoring.
"""

import sys
import time
import threading
from dmx_bridge import DMXBridge
import config


class DMXBridgeCLI:
    def __init__(self):
        self.bridge = DMXBridge()
        self.running = False
        self.status_thread = None
        
    def print_banner(self):
        """Print startup banner"""
        protocol_name = config.PROTOCOL.upper()
        print("\n" + "="*60)
        print(f"  {protocol_name} to DMX Bridge - Command Line Interface")
        print("="*60)
        
    def print_config(self):
        """Display current configuration"""
        print("\nConfiguration:")
        print(f"  Protocol:        {config.PROTOCOL.upper()}")
        print(f"  Arduino Port:    {config.ARDUINO_PORT} @ {config.ARDUINO_BAUD} baud")

        if config.PROTOCOL.lower() == "sacn":
            print(f"  sACN Universe:   {config.SACN_UNIVERSE}")
        elif config.PROTOCOL.lower() == "artnet":
            print(f"  ArtNet Universe: {config.ARTNET_UNIVERSE}")
            print(f"  ArtNet IP:       {config.ARTNET_IP}")

        print(f"  DMX Channels:    {config.DMX_CHANNELS}")
        print(f"  DMX Rate:        {config.DMX_FPS} FPS")
        print(f"  Output Rate:     {config.OUTPUT_FPS} FPS (2x DMX)")
        print(f"  Buffer Size:     {config.FRAME_BUFFER_SIZE} frames")
        print(f"  Performance:     {'Enabled' if config.PERFORMANCE_MONITORING else 'Disabled'}")
        print()
        
    def start(self):
        """Start the bridge"""
        self.print_banner()
        self.print_config()
        
        print("Initializing...")
        
        # Connect Arduino
        if not self.bridge.connect():
            print("\n✗ Failed to connect to Arduino")
            print("  Check config.py for correct port settings")
            return False
            
        # Start protocol receiver
        if not self.bridge.start_protocol():
            print(f"\n✗ Failed to start {config.PROTOCOL.upper()} receiver")
            return False
            
        print("\n✓ Bridge started successfully")
        self.running = True
        
        # Start status thread
        self.status_thread = threading.Thread(target=self.status_loop, daemon=True)
        self.status_thread.start()
        
        return True
    
    def status_loop(self):
        """Background status display with performance monitoring"""
        last_fps = 0
        last_active = 0
        last_max = 0
        last_drop_rate = 0
        
        while self.running:
            time.sleep(1)
            
            # Get stats
            fps = self.bridge.get_fps()
            data = self.bridge.dmx_data
            active = sum(1 for v in data if v > 0)
            max_val = max(data) if data else 0
            
            # Get performance stats
            stats = self.bridge.get_performance_stats()
            drop_rate = stats['drop_rate']
            
            # Only print if changed
            if (fps != last_fps or active != last_active or max_val != last_max or 
                abs(drop_rate - last_drop_rate) > 0.1):
                status = (f"FPS: {fps:2d} | Active: {active:3d}/{config.DMX_CHANNELS} | "
                         f"Max: {max_val:3d} | Drop: {drop_rate:.1f}%")
                print(f"\r{status}", end='', flush=True)
                last_fps = fps
                last_active = active
                last_max = max_val
                last_drop_rate = drop_rate
    
    def print_commands(self):
        """Print available commands"""
        print("\n" + "-"*60)
        print("Commands:")
        print("  1  - Test: All OFF")
        print("  2  - Test: First 5 channels @ 255")
        print("  3  - Test: All @ 50% (128)")
        print("  4  - Test: All ON (255)")
        print("  s  - Show current status")
        print("  c  - Show configuration")
        print("  q  - Quit")
        print("-"*60)
        print()
    
    def show_status(self):
        """Show detailed status with performance metrics"""
        print("\n" + "="*60)
        print("Current Status:")
        print(f"  Arduino:    {'Connected' if self.bridge.ser and self.bridge.ser.is_open else 'Disconnected'}")

        protocol_name = config.PROTOCOL.upper()
        if config.PROTOCOL.lower() == "sacn":
            receiver_status = 'Listening' if self.bridge.receiver else 'Stopped'
            print(f"  sACN:       {receiver_status}")
        elif config.PROTOCOL.lower() == "artnet":
            receiver_status = 'Listening' if self.bridge.artnet_server else 'Stopped'
            print(f"  ArtNet:     {receiver_status}")

        print(f"  DMX Active: {'Yes' if self.bridge.active else 'No'}")
        print(f"  FPS:        {self.bridge.get_fps()}")

        data = self.bridge.dmx_data
        active = sum(1 for v in data if v > 0)
        max_val = max(data) if data else 0
        print(f"  Active Ch:  {active}/{config.DMX_CHANNELS}")
        print(f"  Max Value:  {max_val}")

        # Performance stats
        stats = self.bridge.get_performance_stats()
        print(f"  Processed:  {stats['processed_frames']}")
        print(f"  Dropped:    {stats['dropped_frames']}")
        print(f"  Drop Rate:  {stats['drop_rate']:.1f}%")
        print("="*60 + "\n")
    
    def run(self):
        """Main command loop"""
        if not self.start():
            return
        
        self.print_commands()
        
        print("Ready for commands (type command or 'q' to quit)...\n")
        
        try:
            while self.running:
                try:
                    cmd = input().strip().lower()
                    
                    if cmd == 'q':
                        break
                    elif cmd == '1':
                        self.bridge.send_test('all_off')
                    elif cmd == '2':
                        self.bridge.send_test('first_5')
                    elif cmd == '3':
                        self.bridge.send_test('dim')
                    elif cmd == '4':
                        self.bridge.send_test('all_on')
                    elif cmd == 's':
                        self.show_status()
                    elif cmd == 'c':
                        self.print_config()
                    elif cmd == '?':
                        self.print_commands()
                    elif cmd:
                        print(f"Unknown command: {cmd}")
                        
                except EOFError:
                    break
                    
        except KeyboardInterrupt:
            pass
        
        print("\n\nShutting down...")
        self.running = False
        self.bridge.shutdown()
        print("Goodbye!\n")


def main():
    cli = DMXBridgeCLI()
    cli.run()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

