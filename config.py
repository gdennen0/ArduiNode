"""
Configuration for DMX Bridge

Adjust these settings to match your hardware and network setup.
"""

# ============================================================================
# ARDUINO CONFIGURATION
# ============================================================================
ARDUINO_PORT = "COM3"      # Windows: COM3, Mac: /dev/cu.usbserial, Linux: /dev/ttyUSB0
ARDUINO_BAUD = 250000      # Baud rate for USB serial (250000 recommended)

# ============================================================================
# PROTOCOL CONFIGURATION
# ============================================================================
PROTOCOL = "sacn"          # Options: "sacn" or "artnet"

# sACN Settings (when PROTOCOL = "sacn")
SACN_UNIVERSE = 1          # Universe number (1-63999)

# ArtNet Settings (when PROTOCOL = "artnet")
ARTNET_UNIVERSE = 0        # Universe number (0-15)
ARTNET_IP = "255.255.255.255"  # Broadcast address (usually don't change)

# ============================================================================
# DMX CONFIGURATION
# ============================================================================
DMX_CHANNELS = 512         # Number of DMX channels (1-512)
DMX_FPS = 44               # Standard DMX refresh rate
OUTPUT_FPS = 88            # Output rate (2x DMX for smooth operation)

# ============================================================================
# PERFORMANCE SETTINGS
# ============================================================================
FRAME_BUFFER_SIZE = 50     # Frame buffer size (increase if dropping frames)
PERFORMANCE_MONITORING = True  # Show performance statistics
