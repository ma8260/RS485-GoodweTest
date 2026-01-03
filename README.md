# RS485-GoodweTest

RS485 communication testing script for Goodwe GW3000SS inverter on Raspberry Pi 4.

## Overview

This project provides a Python script to test RS485 communication between a Raspberry Pi 4 and a Goodwe GW3000SS solar inverter using a Waveshare USB to RS485 converter.

## Hardware Requirements

- **Raspberry Pi 4** running Home Assistant container (or any Linux-based system)
- **Waveshare USB to RS485 converter** with FT232RNL chipset
- **Goodwe GW3000SS inverter**

## Software Requirements

- Python 3.6 or higher
- PySerial library (see Installation section)

## Installation

1. Clone this repository:
```bash
git clone https://github.com/ma8260/RS485-GoodweTest.git
cd RS485-GoodweTest
```

2. Install the required Python dependencies:
```bash
pip3 install -r requirements.txt
```

3. Ensure your user has permission to access the serial port:
```bash
sudo usermod -a -G dialout $USER
```
Note: You'll need to log out and log back in for the group change to take effect.

## RS485 Configuration

The script is configured for the following serial port settings (as per Goodwe documentation):
- **Baud rate:** 9600 bps
- **Data bits:** 8
- **Stop bit:** 1
- **Parity:** None

## Usage

### Basic Usage

Run the test with default settings (assumes serial port at `/dev/ttyUSB0`):

```bash
python3 rs485_test.py
```

### Advanced Options

Specify a custom serial port:
```bash
python3 rs485_test.py --port /dev/ttyUSB1
```

Specify a custom log file location:
```bash
python3 rs485_test.py --log-file /var/log/rs485_test.log
```

Change the baud rate (not recommended - use 9600 for Goodwe):
```bash
python3 rs485_test.py --baudrate 19200
```

View all available options:
```bash
python3 rs485_test.py --help
```

## Test Sequence

The script performs the following three-phase test:

1. **Phase 1: Off-line Query Data Test**
   - Sends packet `aa55807f00000001fe` 5 times
   - 5-second interval between each transmission

2. **Phase 2: Remove Register Data Test**
   - Sends packet `aa55807f0002000200` 5 times
   - 5-second interval between each transmission

3. **Phase 3: Off-line Query Data Test (Repeated)**
   - Sends packet `aa55807f00000001fe` 5 times again
   - 5-second interval between each transmission

## Logging

The script logs all communication events to:
- **Console output** (INFO level and above)
- **Log file** (DEBUG level and above) - default: `rs485_test.log`

Log entries include:
- Timestamp
- Connection status
- Packet transmissions (hex format)
- Responses received (hex format)
- Error messages
- Test summary statistics

## Output Example

```
14:30:15 - INFO - Attempting to connect to /dev/ttyUSB0
14:30:15 - INFO - Configuration: 9600 baud, 8N1
14:30:15 - INFO - Successfully connected to /dev/ttyUSB0
============================================================
Starting RS485 Communication Test
Test started at: 2026-01-03 14:30:15
============================================================

============================================================
PHASE 1: Off-line Query Data Test
============================================================
14:30:15 - INFO - Starting Off-line Query test sequence
14:30:15 - INFO - Will send packet 5 times with 5.0s intervals
14:30:15 - INFO - Transmission 1/5
14:30:15 - INFO - ✓ Transmission 1 successful
...
```

## Troubleshooting

### Serial Port Not Found

If you get an error about the serial port not being found:
1. Check if the USB to RS485 converter is connected: `ls /dev/ttyUSB*`
2. Verify the device is recognized: `dmesg | grep tty`
3. Try specifying the correct port with `--port` option

### Permission Denied

If you get a permission error:
1. Add your user to the `dialout` group: `sudo usermod -a -G dialout $USER`
2. Log out and log back in
3. Alternatively, run with sudo: `sudo python3 rs485_test.py`

### No Response from Inverter

If packets are sent successfully but no response is received:
1. Check physical RS485 connections (A/B wiring)
2. Verify the inverter is powered on
3. Ensure the inverter address matches (default is usually 0x7F)
4. Check if the inverter is in the correct mode for RS485 communication

### Running in Home Assistant Container

If running inside a Home Assistant container:
1. Ensure the USB device is passed through to the container
2. Add to your `docker-compose.yml` or container configuration:
   ```yaml
   devices:
     - /dev/ttyUSB0:/dev/ttyUSB0
   ```
3. You may need to run the script with appropriate permissions

## Technical Details

### Packet Formats

**Off-line Query Data Packet:**
- Hex: `aa 55 80 7f 00 00 00 01 fe`
- Purpose: Query offline data from the inverter

**Remove Register Data Packet:**
- Hex: `aa 55 80 7f 00 02 00 02 00`
- Purpose: Remove/clear register data

### Error Checking

The script includes comprehensive error checking:
- Serial port connection validation
- Transmission success verification (bytes written check)
- Timeout handling
- Exception catching and logging
- Summary statistics of successful/failed transmissions

## License

This project is provided as-is for testing purposes.

## Contributing

Feel free to open issues or submit pull requests for improvements.

## References

- [Goodwe Inverter Documentation](https://www.goodwe.com/)
- [PySerial Documentation](https://pyserial.readthedocs.io/)
- [RS485 Protocol Basics](https://en.wikipedia.org/wiki/RS-485)