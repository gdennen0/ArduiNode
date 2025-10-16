#!/usr/bin/env python3
"""
Simple DMX Bridge Example

This example shows how to use the DMX Bridge as a library in your own projects.
"""

from dmx_bridge import DMXBridge
import time
import math

def main():
    # Create bridge instance
    bridge = DMXBridge()
    
    print("Starting DMX Bridge...")
    
    # Connect to Arduino
    if not bridge.connect():
        print("Failed to connect to Arduino")
        return
    
    # Start protocol receiver
    if not bridge.start_protocol():
        print("Failed to start protocol receiver")
        return
    
    print("Bridge is running!")
    print("Press Ctrl+C to stop\n")
    
    try:
        # Example 1: Set specific channels
        print("Example 1: Setting channels 1-3 to full")
        bridge.dmx_data[0] = 255  # Channel 1
        bridge.dmx_data[1] = 255  # Channel 2
        bridge.dmx_data[2] = 255  # Channel 3
        time.sleep(2)
        
        # Example 2: Fade effect
        print("Example 2: Smooth fade on channel 1")
        for i in range(100):
            brightness = int(128 + 127 * math.sin(i / 10))
            bridge.dmx_data[0] = brightness
            time.sleep(0.05)
        
        # Example 3: Monitor status
        print("\nExample 3: Monitoring status for 10 seconds")
        for _ in range(10):
            stats = bridge.get_performance_stats()
            active = sum(1 for v in bridge.dmx_data if v > 0)
            print(f"FPS: {bridge.get_fps()} | Active: {active}/512 | Drop: {stats['drop_rate']:.1f}%")
            time.sleep(1)
        
        # Example 4: Send all off
        print("\nExample 4: Sending blackout")
        bridge.send_test('all_off')
        time.sleep(1)
        
        print("\nDone! The bridge will continue running...")
        print("Press Ctrl+C to stop")
        
        # Keep running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\nShutting down...")
    
    finally:
        bridge.shutdown()
        print("Bridge stopped")

if __name__ == '__main__':
    main()

