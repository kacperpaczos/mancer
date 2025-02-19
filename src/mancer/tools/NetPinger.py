#!/usr/bin/env python3

import platform
import subprocess
import ipaddress
from datetime import datetime
import concurrent.futures
import re
from typing import Tuple, List, Optional
import logging
from pathlib import Path
import sys

# Configure logging at module level
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def validate_network_address(ip_str: str) -> bool:
    """
    Validate if the given IP address is a valid network address (last octet is 0).
    
    Args:
        ip_str: IP address string
        
    Returns:
        bool: True if valid network address, False otherwise
    """
    try:
        ip = ipaddress.ip_address(ip_str)
        return ip_str.split('.')[-1] == '0'
    except ValueError:
        return False

def get_network_input() -> str:
    """
    Get and validate network address input from user.
    
    Returns:
        str: Valid network address in CIDR notation
    """
    while True:
        network = input("Enter network address (e.g., 192.168.1.0): ")
        
        try:
            # Validate IP format
            ip = ipaddress.ip_address(network)
            
            # Check if it's a proper network address
            if not validate_network_address(network):
                logger.error("Invalid network address. Last octet must be 0")
                sys.exit(1)
            
            # If no mask was provided, ask for it
            mask = input("Enter network mask (e.g., 24 for /24): ").strip()
            if not mask:
                logger.error("Network mask is required")
                continue
                
            try:
                mask_int = int(mask)
                if not (0 <= mask_int <= 32):
                    logger.error("Network mask must be between 0 and 32")
                    continue
                    
                return f"{network}/{mask}"
                
            except ValueError:
                logger.error("Invalid network mask format")
                continue
                
        except ValueError:
            logger.error("Invalid IP address format")
            continue

class NetworkScanner:
    def __init__(self, network: str):
        """
        Initialize NetworkScanner with target network.
        
        Args:
            network: Network address in CIDR notation (e.g., '192.168.1.0/24')
        """
        self.network = ipaddress.ip_network(network)
        self.local_addresses = self._get_local_addresses()
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_file = Path(f"network_scan_{self.timestamp}.txt")

    def _get_local_addresses(self) -> List[str]:
        """
        Detect local IP addresses belonging to the target network using 'ip a' command.
        
        Returns:
            List of local IP addresses that belong to the target network.
        """
        try:
            result = subprocess.run(
                ['ip', 'a'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            
            # Extract all IPv4 addresses using regex
            ip_pattern = r'inet (\d+\.\d+\.\d+\.\d+)/\d+'
            all_addresses = re.findall(ip_pattern, result.stdout)
            
            # Filter addresses that belong to the target network
            matching_addresses = [
                addr for addr in all_addresses 
                if ipaddress.ip_address(addr) in self.network
            ]
            
            logger.info(f"Detected local addresses in network: {matching_addresses}")
            return matching_addresses
            
        except subprocess.SubprocessError as e:
            logger.error(f"Failed to get local addresses: {e}")
            return []

    def _check_host(self, ip: str) -> Tuple[Optional[str], bool]:
        """
        Check if a host is alive using ping command.
        
        Args:
            ip: IP address to check
            
        Returns:
            Tuple of (IP address if host is alive, bool indicating if it's a local address)
        """
        try:
            ping_params = ['-n', '1', '-w', '500'] if platform.system() == "Windows" else ['-c', '1', '-W', '1']
            result = subprocess.run(
                ['ping'] + ping_params + [str(ip)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False
            )
            
            if result.returncode == 0:
                return str(ip), str(ip) in self.local_addresses
            return None, False
            
        except subprocess.SubprocessError:
            return None, False

    def scan(self) -> None:
        """
        Perform network scan and save results to file.
        """
        active_hosts = []
        logger.info(f"Starting network scan for {self.network}")
        logger.info(f"Results will be saved to: {self.output_file}")

        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            futures = {
                executor.submit(self._check_host, str(ip)): ip 
                for ip in self.network.hosts()
            }
            
            with open(self.output_file, 'w', encoding='utf-8') as f:
                self._write_header(f)
                
                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    if result[0]:
                        self._process_active_host(result[0], result[1], f, active_hosts)

        self._print_summary(active_hosts)

    def _write_header(self, file) -> None:
        """Write scan header information to file."""
        file.write(f"Network Scan Results\n")
        file.write(f"===================\n")
        file.write(f"Target Network: {self.network}\n")
        file.write(f"Scan Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        file.write(f"Local Addresses: {', '.join(self.local_addresses)}\n\n")
        file.write("Active Hosts:\n")
        file.write("-------------\n")

    def _process_active_host(self, ip: str, is_local: bool, file, active_hosts: List[str]) -> None:
        """Process and record an active host."""
        marker = " <-- YOUR MACHINE" if is_local else ""
        message = f"Host available: {ip}{marker}"
        
        logger.info(message)
        file.write(f"{message}\n")
        active_hosts.append(ip)

    def _print_summary(self, active_hosts: List[str]) -> None:
        """Print scan summary."""
        logger.info("\nScan completed!")
        logger.info(f"Found {len(active_hosts)} active hosts")
        logger.info(f"Detailed results saved to: {self.output_file}")

def print_banner():
    """Display program banner."""
    banner = """
    NetPinger v1.0.0
    ================
    Network Host Discovery Tool
    """
    print(banner)

def main():
    try:
        print_banner()
        network = get_network_input()
        scanner = NetworkScanner(network)
        scanner.scan()
    except KeyboardInterrupt:
        logger.warning("\nScan interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()