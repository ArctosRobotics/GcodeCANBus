
# G-code to CAN BUS Converter

Watch the demo: https://www.youtube.com/watch?v=CeugYSGpj0s

These two files convert G-code to CAN BUS messages, supporting 6 axis style G-code for: X, Y, Z, A, B, and C axes.

## Prerequisites

- Python 3
- python-can

```
$ pip install python-can[serial]
```

G-code is converted to follow Makerbase CAN bus message format:

### CAN Message Structure

```
ID + Mode + Speed + Acceleration + Position + CRC
```

- **ID:** Configured from ID 01 to ID 06
- **Mode:** F5 for absolute axis
- **Speed:** Taken from Feedrate in G-code
- **Acceleration:** Configured as 02 (default)
- **Position:** Converted from G-code
- **CRC:** Cyclic Redundancy Check calculated by the formula: CRC = (ID + Mode + Speed + Acceleration + Position) & 0xFF

To change the gear ratio on each axis, modify the following line in `convert.py` script:

```python
gear_ratios = [0.5, 0.5, 1, 1, 1, 1]
```

## Usage

### Convert G-code to CAN messages

`convert.py` converts a G-code file in `.tap` format and creates a corresponding `.txt` file containing CAN messages.

### Send CAN messages

`send.py` streams CAN messages to the Canable adapter. If you need to change the port, modify the following line in `send.py`:

```python
bus = can.interface.Bus(bustype='slcan', channel='/dev/ttyACM0', bitrate=500000)
```

Feel free to adapt and use these scripts for your robotic arm!
```

Make sure to replace the actual paths and details according to your specific setup. This markdown formatting is suitable for a clear and organized display on GitHub.
