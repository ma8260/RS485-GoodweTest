#!/usr/bin/env python3
"""
RS485 Communication Testing Script for Goodwe GW3000SS Inverter
----------------------------------------------------------------
This script tests RS485 communication between Raspberry Pi 4 and
Goodwe GW3000SS inverter using a Waveshare USB to RS485 converter.

Hardware Setup:
- Raspberry Pi 4 with Home Assistant container
- Waveshare USB to RS485 converter (FT232RNL chipset)
- Goodwe GW3000SS inverter

Serial Configuration:
- Baud rate: 9600 bps
- Data bits: 8
- Stop bit: 1
- Parity: None
"""

import serial
import time
import logging
import sys
from datetime import datetime
from typing import Optional, Tuple


class RS485Tester:
    """RS485 communication tester for Goodwe inverter"""
    
    # Test packet definitions
    OFFLINE_QUERY_PACKET = bytes.fromhex("aa55807f00000001fe")
    REMOVE_REGISTER_PACKET = bytes.fromhex("aa55807f0002000200")
    # New Test Packet Definitions
    ALLOCATE_REGISTER_ADDRESS_PACKET = bytes.fromhex("aa55807f000011313330303053535531323530303039381105a9")
    READ_DATA_PACKET = bytes.fromhex("aa5580110101000192")
    
    def __init__(self, port: str = "/dev/ttyUSB0", baudrate: int = 9600,
                 log_file: str = "rs485_test.log"):
        """
        Initialize RS485 tester
        
        Args:
            port: Serial port path (default: /dev/ttyUSB0)
            baudrate: Communication speed (default: 9600)
            log_file: Path to log file (default: rs485_test.log)
        """
        self.port = port
        self.baudrate = baudrate
        self.log_file = log_file
        self.serial_conn: Optional[serial.Serial] = None
        
        # Setup logging
        self._setup_logging()
        
    def _setup_logging(self):
        """Configure logging to both file and console"""
        # Create logger
        self.logger = logging.getLogger("RS485Tester")
        self.logger.setLevel(logging.DEBUG)
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # File handler
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(console_formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
    def connect(self) -> bool:
        """
        Establish serial connection to RS485 device
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.logger.info(f"Attempting to connect to {self.port}")
            self.logger.info(f"Configuration: {self.baudrate} baud, 8N1")
            
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=2.0,
                write_timeout=2.0
            )
            
            # Clear any existing data in buffers
            self.serial_conn.reset_input_buffer()
            self.serial_conn.reset_output_buffer()
            
            self.logger.info(f"Successfully connected to {self.port}")
            return True
            
        except serial.SerialException as e:
            self.logger.error(f"Failed to connect to {self.port}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error during connection: {e}")
            return False
    
    def disconnect(self):
        """Close serial connection"""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            self.logger.info("Serial connection closed")
    
    def send_packet(self, packet: bytes, packet_name: str) -> Tuple[bool, Optional[bytes]]:
        """
        Send a packet and read response
        
        Args:
            packet: Bytes to send
            packet_name: Human-readable name for logging
            
        Returns:
            Tuple of (success: bool, response: Optional[bytes])
        """
        if not self.serial_conn or not self.serial_conn.is_open:
            self.logger.error("Serial connection not established")
            return False, None
        
        try:
            # Convert packet to hex string for logging
            packet_hex = packet.hex()
            self.logger.debug(f"Sending {packet_name}: {packet_hex}")
            
            # Clear input buffer before sending
            self.serial_conn.reset_input_buffer()
            
            # Send packet
            bytes_written = self.serial_conn.write(packet)
            
            if bytes_written != len(packet):
                self.logger.error(
                    f"Failed to send complete packet. "
                    f"Sent {bytes_written}/{len(packet)} bytes"
                )
                return False, None
            
            # Flush output to ensure data is sent
            self.serial_conn.flush()
            self.logger.debug(f"Successfully sent {bytes_written} bytes")
            
            # Wait a bit for response
            time.sleep(0.5)
            
            # Read response if available
            response = None
            if self.serial_conn.in_waiting > 0:
                response = self.serial_conn.read(self.serial_conn.in_waiting)
                response_hex = response.hex()
                self.logger.info(
                    f"Received response ({len(response)} bytes): {response_hex}"
                )
            else:
                self.logger.debug("No response received")
            
            return True, response
            
        except serial.SerialTimeoutException:
            self.logger.error("Timeout while sending packet")
            return False, None
        except serial.SerialException as e:
            self.logger.error(f"Serial error while sending packet: {e}")
            return False, None
        except Exception as e:
            self.logger.error(f"Unexpected error while sending packet: {e}")
            return False, None
    
    def send_packet_multiple_times(self, packet: bytes, packet_name: str,
        count: int = 5, interval: float = 5.0) -> int:
        """
        Send a packet multiple times with specified interval
        
        Args:
            packet: Bytes to send
            packet_name: Human-readable name for logging
            count: Number of times to send (default: 5)
            interval: Seconds between sends (default: 5.0)
            
        Returns:
            Number of successful transmissions
        """
        self.logger.info(f"Starting {packet_name} test sequence")
        self.logger.info(f"Will send packet {count} times with {interval}s intervals")
        
        successful = 0
        
        for i in range(count):
            self.logger.info(f"Transmission {i + 1}/{count}")
            
            success, response = self.send_packet(packet, packet_name)
            
            if success:
                successful += 1
                self.logger.info(f"✓ Transmission {i + 1} successful")
            else:
                self.logger.warning(f"✗ Transmission {i + 1} failed")
            
            # Wait before next transmission (except after last one)
            if i < count - 1:
                self.logger.debug(f"Waiting {interval} seconds before next transmission")
                time.sleep(interval)
        
        self.logger.info(
            f"Completed {packet_name} test sequence: "
            f"{successful}/{count} successful"
        )
        
        return successful
    
    def run_full_test(self) -> bool:
        """
        Run the complete test sequence:
        1. Send Off-line Query packet 5 times
        2. Send Remove Register packet 5 times
        3. Send Off-line Query packet 5 times again
        
        Returns:
            True if all tests completed (regardless of success rate)
        """
        try:
            self.logger.info("=" * 60)
            self.logger.info("Starting RS485 Communication Test")
            self.logger.info(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.logger.info("=" * 60)
            
            # Phase 1: Off-line Query
            self.logger.info("\n" + "=" * 60)
            self.logger.info("PHASE 1: Off-line Query Data Test")
            self.logger.info("=" * 60)
            phase1_success = self.send_packet_multiple_times(
                self.OFFLINE_QUERY_PACKET,
                "Off-line Query",
                count=5,
                interval=2.0
            )
            
            # Brief pause between phases
            time.sleep(2)
            
            # Phase 2: Remove Register
            self.logger.info("\n" + "=" * 60)
            self.logger.info("PHASE 2: Remove Register Data Test")
            self.logger.info("=" * 60)
            phase2_success = self.send_packet_multiple_times(
                self.REMOVE_REGISTER_PACKET,
                "Remove Register",
                count=5,
                interval=2.0
            )
            
            # Brief pause between phases
            time.sleep(2)
            
            # Phase 3: Off-line Query (repeated)
            self.logger.info("\n" + "=" * 60)
            self.logger.info("PHASE 3: Off-line Query Data Test (Repeated)")
            self.logger.info("=" * 60)
            phase3_success = self.send_packet_multiple_times(
                self.OFFLINE_QUERY_PACKET,
                "Off-line Query (Repeated)",
                count=5,
                interval=2.0
            )
            
            # Brief pause between phases
            time.sleep(2)
            
            # Phase 4: Allocate Register Address Test
            self.logger.info("\n" + "=" * 60)
            self.logger.info("PHASE 4: Allocate Register Address Test")
            self.logger.info("=" * 60)
            phase4_success = self.send_packet_multiple_times(
                self.ALLOCATE_REGISTER_ADDRESS_PACKET,
                "Allocate Register Address",
                count=5,
                interval=2.0  # Update to 2-second intervals
            )

            time.sleep(2)

            # Phase 5: Read Data Test
            self.logger.info("\n" + "=" * 60)
            self.logger.info("PHASE 5: Read Data Test")
            self.logger.info("=" * 60)
            phase5_success = self.send_packet_multiple_times(
                self.READ_DATA_PACKET,
                "Read Data",
                count=5,
                interval=2.0  # Update to 2-second intervals
            )

            # Update Summary
            self.logger.info("\n" + "=" * 60)
            self.logger.info("TEST SUMMARY")
            self.logger.info("=" * 60)
            self.logger.info(f"Phase 1 (Off-line Query):      {phase1_success}/5 successful")
            self.logger.info(f"Phase 2 (Remove Register):     {phase2_success}/5 successful")
            self.logger.info(f"Phase 3 (Off-line Query Rep.): {phase3_success}/5 successful")
            self.logger.info(f"Phase 4 (Allocate Address):    {phase4_success}/5 successful")
            self.logger.info(f"Phase 5 (Read Data):           {phase5_success}/5 successful")
            self.logger.info(
            f"Total: {phase1_success + phase2_success + phase3_success + phase4_success + phase5_success}/25 successful"
                )
            
            return True
            
        except KeyboardInterrupt:
            self.logger.warning("\nTest interrupted by user")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error during test: {e}")
            return False


def main():
    """Main entry point for the script"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="RS485 Communication Testing Script for Goodwe GW3000SS Inverter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test with default settings (assumes /dev/ttyUSB0)
  python3 rs485_test.py
  
  # Specify custom serial port
  python3 rs485_test.py --port /dev/ttyUSB1
  
  # Change baud rate (not recommended - use 9600 for Goodwe)
  python3 rs485_test.py --baudrate 19200
  
  # Specify custom log file
  python3 rs485_test.py --log-file /var/log/rs485_test.log

Note: Make sure you have proper permissions to access the serial port.
You may need to add your user to the 'dialout' group or run with sudo.
        """
    )
    
    parser.add_argument(
        "--port", "-p",
        default="/dev/ttyUSB0",
        help="Serial port path (default: /dev/ttyUSB0)"
    )
    
    parser.add_argument(
        "--baudrate", "-b",
        type=int,
        default=9600,
        help="Baud rate (default: 9600)"
    )
    
    parser.add_argument(
        "--log-file", "-l",
        default="rs485_test.log",
        help="Log file path (default: rs485_test.log)"
    )
    
    args = parser.parse_args()
    
    # Create tester instance
    tester = RS485Tester(
        port=args.port,
        baudrate=args.baudrate,
        log_file=args.log_file
    )
    
    try:
        # Connect to serial port
        if not tester.connect():
            print(f"\nERROR: Failed to connect to {args.port}")
            print("Please check:")
            print("  1. The device is connected")
            print("  2. The port path is correct")
            print("  3. You have proper permissions (try: sudo usermod -a -G dialout $USER)")
            print("  4. No other program is using the port")
            sys.exit(1)
        
        # Run the full test
        success = tester.run_full_test()
        
        # Disconnect
        tester.disconnect()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
