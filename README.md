# DMX Bridge - Command Line Interface

Convert sACN (E1.31) network DMX to physical DMX using Arduino Uno + CQRobot DMX Shield.

## What You Need

**Hardware:**
- Arduino Uno
- [CQRobot DMX Shield (AngelDFR0260US)](http://www.cqrobot.wiki/index.php/DMX_Shield_for_Arduino_SKU:_AngelDFR0260US)
- USB cable
- DMX fixtures with XLR cables

**Software:**
- Python 3.7+
- Arduino IDE or PlatformIO

## Quick Start

### 1. Install Python Packages
```bash
pip install -r requirements.txt
```

### 2. Set Shield Jumpers

On your CQRobot shield, set these jumpers:

| Jumper | Setting |
|--------|---------|
| TX | Pin 4 (TX-IO position) |
| RX | Pin 3 (RX-IO position) |
| Slave/Master | Middle → DE, controlled by D2 (HIGH = TX) |
| Enable | Connected (remove to upload) |

**Important:** Remove "Enable" jumper before uploading Arduino code, reconnect after.

### 3. Upload Arduino Code

**Option A: Using PlatformIO**
```bash
pio run --target upload
```

**Option B: Using Arduino IDE**
1. Install DmxSimple library (Tools → Manage Libraries → search "DmxSimple")
2. Open `src/main.cpp`
3. Remove "Enable" jumper from shield
4. Upload to Arduino
5. Reconnect "Enable" jumper
6. Power cycle Arduino

### 4. Configure Port

Edit `config.py`:
```python
ARDUINO_PORT = "COM3"   # Your Arduino port
ARDUINO_BAUD = 250000   # Must match firmware USB Serial
SACN_UNIVERSE = 1       # Your sACN universe
```

Find your port:
- **Windows:** Device Manager → COM ports (COM3, COM4, etc.)
- **Mac:** `/dev/cu.usbserial` or `/dev/cu.usbmodem`
- **Linux:** `/dev/ttyUSB0` or `/dev/ttyACM0`

### 5. Run the App
```bash
python main.py
```

The command-line interface will display:
- Configuration settings
- Connection status (Arduino, sACN, DMX)
- Real-time FPS counter and active channels
- Interactive command menu
- Test pattern options

## How It Works

```
sACN Source → Network → Python Bridge → USB → Arduino → DMX Shield → XLR → Fixtures
  (MA3,QLC+)                                  (Uno)    (CQRobot)         (Lights)
```

**Super Simple Code Structure:**
```
config.py      - Settings (10 lines)
dmx_bridge.py  - Core logic (117 lines)
main.py        - CLI interface (168 lines)
src/main.cpp   - Arduino firmware (70 lines)
```

**Total: ~365 lines of clean, readable code**

## Using the CLI

**Available Commands:**
- **1** - Test: All OFF (DMX blackout)
- **2** - Test: First 5 channels @ 255
- **3** - Test: All @ 50% (128)
- **4** - Test: All ON (255)
- **s** - Show current status
- **c** - Show configuration
- **q** - Quit

**Real-time Display:**
- FPS counter (updates per second)
- Active channels (non-zero values)
- Maximum channel value
- Connection status
- DMX activity indicators

## Testing Your Setup

1. Run `python main.py`
2. Verify Arduino and sACN show connected ✓
3. Type `2` and press Enter to send "First 5" test pattern
4. First 5 DMX channels should output at full brightness
5. Your fixtures should respond
6. Type `s` to see detailed status

## sACN Setup

Configure your lighting software (MA3 onPC, QLC+, ETC Nomad, etc.):
- Protocol: sACN (E1.31)
- Universe: 1 (or match config.py)
- Same network as this computer

When you send DMX data:
- DMX status turns green
- FPS counter shows update rate (~44 fps max)
- Active channels count updates
- Log shows "DMX ACTIVE"

## Technical Details

**Library:** DmxSimple by Paul Stoffregen - proven compatibility with CQRobot shields

**Protocol:** Simple binary format
```
[0xFF] [channels_low] [channels_high] [ch1] [ch2] ... [ch512]
```

**Timing:**
- Max FPS: 44 (DMX512 standard)
- PC↔Arduino baud: 250000 (USB Serial)
- DMX channels: 512
- Update rate limiting in Python

**Shield Documentation:** [CQRobot Wiki](http://www.cqrobot.wiki/index.php/DMX_Shield_for_Arduino_SKU:_AngelDFR0260US)

## Troubleshooting

**Arduino won't connect:**
- Check USB cable
- Verify COM port in config.py
- Make sure "Enable" jumper is connected (after upload)
- Check Device Manager (Windows) or `ls /dev/tty*` (Mac/Linux)

**No DMX output:**
- Verify shield jumpers: TX→Pin 4, RX→Pin 3, Enable→Connected
- Check XLR cable connections (Pin 1=GND, Pin 2=Data-, Pin 3=Data+)
- Try test patterns from GUI
- Verify fixtures are set to DMX addresses 1-5 for "First 5" test

**sACN not receiving:**
- Check universe number matches your source
- Verify you're on the same network
- Check firewall (must allow UDP port 5568)
- Try disabling VPN if connected

**GUI won't start:**
- Make sure PyQt6 is installed: `pip install PyQt6`
- Check Python version: `python --version` (need 3.7+)

## Integration Into Your Projects

The code is designed to be simple and reusable:

```python
from dmx_bridge import DMXBridge

# Create bridge
bridge = DMXBridge()

# Connect
if bridge.connect() and bridge.start_sacn():
    print("Bridge ready!")
    
    # Send test pattern
    bridge.send_test('all_on')
    
    # Check status
    print(f"Active: {bridge.active}")
    print(f"FPS: {bridge.get_fps()}")
    print(f"Data: {bridge.dmx_data[:10]}")  # First 10 channels
    
    # Cleanup when done
    bridge.shutdown()
```

All core logic is in `dmx_bridge.py` - clean, simple, well-commented.

## References

- [CQRobot Shield Wiki](http://www.cqrobot.wiki/index.php/DMX_Shield_for_Arduino_SKU:_AngelDFR0260US)
- [DmxSimple Library](https://github.com/PaulStoffregen/DmxSimple)
- [Arduino DMX Playground](http://playground.arduino.cc/DMX/DMXShield)
- [sACN (E1.31) Specification](https://tsp.esta.org/tsp/documents/docs/E1-31-2018.pdf)

## Why This is Better

**vs Web Interface:**
- No web server complexity
- No browser required
- Faster, more responsive
- Native desktop experience

**vs Old Code:**
- 83% less code (340 lines vs 1,704)
- No code duplication
- Clear, simple structure
- Easy to understand and modify
- Follows CQRobot documentation exactly

## License

Open source - use as you wish. Based on CQRobot documentation and community examples.
