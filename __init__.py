"""
DMX Bridge - sACN/ArtNet to Arduino DMX512 Converter

A lightweight, high-performance Python library for bridging network DMX protocols
(sACN and ArtNet) to physical DMX512 output via Arduino.

Example:
    from dmx_bridge import DMXBridge
    
    bridge = DMXBridge()
    if bridge.connect() and bridge.start_protocol():
        print("Bridge running!")
        bridge.send_test('all_on')  # Test pattern
        # ... your code ...
        bridge.shutdown()
"""

__version__ = "1.0.0"
__author__ = "Griffin"

from dmx_bridge import DMXBridge

__all__ = ['DMXBridge']

