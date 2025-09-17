import os
import shutil
import asyncio
import hashlib
import random
import struct
import sys
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import logging
from pathlib import Path

# Add utils directory to path for privilege checker
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))

from services.certificate_service import certificate_service
from services.certificate_db_service import CertificateDBService
from privilege_checker import PrivilegeChecker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WipeMethod(str, Enum):
    """Supported wipe methods"""
    DOD_5220_22_M = "dod_5220_22_m"
    NIST_800_88 = "nist_800_88"
    SINGLE_PASS = "single_pass"
    GUTMANN = "gutmann"
    RANDOM = "random"
    ZERO = "zero"


class WipeStatus(str, Enum):
    """Wipe operation status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class WipeResult:
    """Result of a wipe operation"""
    success: bool
    method: WipeMethod
    target: str
    size_bytes: int
    passes_completed: int
    total_passes: int
    duration_seconds: float
    error_message: Optional[str] = None
    verification_hash: Optional[str] = None
    mock_mode: bool = False
    certificate_id: Optional[str] = None
    certificate_path: Optional[str] = None


class WipeService:
    """Service for secure data wiping with multiple standards support"""
    
    def __init__(self, mock_mode: bool = False, generate_certificates: bool = True):
        self.mock_mode = mock_mode
        self.generate_certificates = generate_certificates
        self.active_operations: Dict[str, WipeStatus] = {}
        self.privilege_checker = PrivilegeChecker()
        self._privilege_checked = False
        self._has_elevated_privileges = False
        
        # DoD 5220.22-M patterns (3 passes)
        self.dod_patterns = [
            b'\x00',  # Pass 1: All zeros
            b'\xFF',  # Pass 2: All ones
            b'\x00'   # Pass 3: All zeros
        ]
        
        # NIST 800-88 patterns (1 pass with random data)
        self.nist_patterns = [b'\x00']  # Single pass with zeros
        
        # Gutmann method patterns (35 passes)
        self.gutmann_patterns = [
            b'\x55', b'\xAA', b'\x92\x49\x24', b'\x49\x24\x92', b'\x24\x92\x49',
            b'\x00', b'\x11', b'\x22', b'\x33', b'\x44', b'\x55', b'\x66', b'\x77',
            b'\x88', b'\x99', b'\xAA', b'\xBB', b'\xCC', b'\xDD', b'\xEE', b'\xFF',
            b'\x92\x49\x24\x49\x24\x92\x49\x24', b'\x49\x24\x92\x49\x24\x92\x49\x24',
            b'\x24\x92\x49\x24\x92\x49\x24\x92', b'\x00\x00\x00\x00\x00\x00\x00\x00',
            b'\x11\x11\x11\x11\x11\x11\x11\x11', b'\x22\x22\x22\x22\x22\x22\x22\x22',
            b'\x33\x33\x33\x33\x33\x33\x33\x33', b'\x44\x44\x44\x44\x44\x44\x44\x44',
            b'\x55\x55\x55\x55\x55\x55\x55\x55', b'\x66\x66\x66\x66\x66\x66\x66\x66',
            b'\x77\x77\x77\x77\x77\x77\x77\x77', b'\x88\x88\x88\x88\x88\x88\x88\x88',
            b'\x99\x99\x99\x99\x99\x99\x99\x99', b'\xAA\xAA\xAA\xAA\xAA\xAA\xAA\xAA',
            b'\xBB\xBB\xBB\xBB\xBB\xBB\xBB\xBB', b'\xCC\xCC\xCC\xCC\xCC\xCC\xCC\xCC',
            b'\xDD\xDD\xDD\xDD\xDD\xDD\xDD\xDD', b'\xEE\xEE\xEE\xEE\xEE\xEE\xEE\xEE',
            b'\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF'
        ]
    
    async def wipe_file(self, path: str, method: WipeMethod) -> WipeResult:
        """
        Securely wipe a single file
        
        Args:
            path: Path to the file to wipe
            method: Wipe method to use
            
        Returns:
            WipeResult with operation details
        """
        # Validate privileges for file wipe operation
        self._validate_privileges_for_operation("file wipe")
        
        start_time = datetime.now()
        operation_id = f"file_{os.path.basename(path)}_{int(start_time.timestamp())}"
        
        try:
            if not os.path.exists(path):
                return WipeResult(
                    success=False,
                    method=method,
                    target=path,
                    size_bytes=0,
                    passes_completed=0,
                    total_passes=0,
                    duration_seconds=0,
                    error_message="File does not exist",
                    mock_mode=self.mock_mode
                )
            
            file_size = os.path.getsize(path)
            self.active_operations[operation_id] = WipeStatus.IN_PROGRESS
            
            if self.mock_mode:
                logger.info(f"Mock mode: Would wipe file {path} using {method.value}")
                await asyncio.sleep(0.1)  # Simulate processing time
                result = WipeResult(
                    success=True,
                    method=method,
                    target=path,
                    size_bytes=file_size,
                    passes_completed=self._get_total_passes(method),
                    total_passes=self._get_total_passes(method),
                    duration_seconds=0.1,
                    mock_mode=True
                )
            else:
                result = await self._perform_file_wipe(path, method, file_size)
            
            self.active_operations[operation_id] = WipeStatus.COMPLETED
            return result
            
        except Exception as e:
            logger.error(f"Error wiping file {path}: {e}")
            self.active_operations[operation_id] = WipeStatus.FAILED
            return WipeResult(
                success=False,
                method=method,
                target=path,
                size_bytes=0,
                passes_completed=0,
                total_passes=0,
                duration_seconds=(datetime.now() - start_time).total_seconds(),
                error_message=str(e),
                mock_mode=self.mock_mode
            )
        finally:
            if operation_id in self.active_operations:
                del self.active_operations[operation_id]
    
    async def wipe_folder(self, path: str, method: WipeMethod) -> WipeResult:
        """
        Securely wipe all files in a folder and remove the folder
        
        Args:
            path: Path to the folder to wipe
            method: Wipe method to use
            
        Returns:
            WipeResult with operation details
        """
        # Validate privileges for folder wipe operation
        self._validate_privileges_for_operation("folder wipe")
        
        start_time = datetime.now()
        operation_id = f"folder_{os.path.basename(path)}_{int(start_time.timestamp())}"
        
        try:
            if not os.path.exists(path):
                return WipeResult(
                    success=False,
                    method=method,
                    target=path,
                    size_bytes=0,
                    passes_completed=0,
                    total_passes=0,
                    duration_seconds=0,
                    error_message="Folder does not exist",
                    mock_mode=self.mock_mode
                )
            
            if not os.path.isdir(path):
                return WipeResult(
                    success=False,
                    method=method,
                    target=path,
                    size_bytes=0,
                    passes_completed=0,
                    total_passes=0,
                    duration_seconds=0,
                    error_message="Path is not a directory",
                    mock_mode=self.mock_mode
                )
            
            self.active_operations[operation_id] = WipeStatus.IN_PROGRESS
            
            if self.mock_mode:
                logger.info(f"Mock mode: Would wipe folder {path} using {method.value}")
                await asyncio.sleep(0.2)  # Simulate processing time
                result = WipeResult(
                    success=True,
                    method=method,
                    target=path,
                    size_bytes=0,  # Would calculate total size in real mode
                    passes_completed=self._get_total_passes(method),
                    total_passes=self._get_total_passes(method),
                    duration_seconds=0.2,
                    mock_mode=True
                )
            else:
                result = await self._perform_folder_wipe(path, method)
            
            self.active_operations[operation_id] = WipeStatus.COMPLETED
            return result
            
        except Exception as e:
            logger.error(f"Error wiping folder {path}: {e}")
            self.active_operations[operation_id] = WipeStatus.FAILED
            return WipeResult(
                success=False,
                method=method,
                target=path,
                size_bytes=0,
                passes_completed=0,
                total_passes=0,
                duration_seconds=(datetime.now() - start_time).total_seconds(),
                error_message=str(e),
                mock_mode=self.mock_mode
            )
        finally:
            if operation_id in self.active_operations:
                del self.active_operations[operation_id]
    
    async def wipe_drive(self, device: str, method: WipeMethod) -> WipeResult:
        """
        Securely wipe an entire drive
        
        Args:
            device: Device path (e.g., /dev/sda, \\\\.\\PhysicalDrive0)
            method: Wipe method to use
            
        Returns:
            WipeResult with operation details
        """
        # Validate privileges for drive wipe operation
        self._validate_privileges_for_operation("drive wipe")
        
        start_time = datetime.now()
        operation_id = f"drive_{os.path.basename(device)}_{int(start_time.timestamp())}"
        
        try:
            self.active_operations[operation_id] = WipeStatus.IN_PROGRESS
            
            if self.mock_mode:
                logger.info(f"Mock mode: Would wipe drive {device} using {method.value}")
                await asyncio.sleep(1.0)  # Simulate processing time
                result = WipeResult(
                    success=True,
                    method=method,
                    target=device,
                    size_bytes=0,  # Would get actual drive size in real mode
                    passes_completed=self._get_total_passes(method),
                    total_passes=self._get_total_passes(method),
                    duration_seconds=1.0,
                    mock_mode=True
                )
            else:
                result = await self._perform_drive_wipe(device, method)
            
            self.active_operations[operation_id] = WipeStatus.COMPLETED
            return result
            
        except Exception as e:
            logger.error(f"Error wiping drive {device}: {e}")
            self.active_operations[operation_id] = WipeStatus.FAILED
            return WipeResult(
                success=False,
                method=method,
                target=device,
                size_bytes=0,
                passes_completed=0,
                total_passes=0,
                duration_seconds=(datetime.now() - start_time).total_seconds(),
                error_message=str(e),
                mock_mode=self.mock_mode
            )
        finally:
            if operation_id in self.active_operations:
                del self.active_operations[operation_id]
    
    async def _perform_file_wipe(self, path: str, method: WipeMethod, file_size: int) -> WipeResult:
        """Perform actual file wiping"""
        start_time = datetime.now()
        total_passes = self._get_total_passes(method)
        patterns = self._get_patterns(method)
        
        try:
            # Ensure file is not read-only on Windows
            try:
                os.chmod(path, 0o666)
            except Exception:
                pass
            with open(path, 'r+b') as f:
                for pass_num in range(total_passes):
                    pattern = patterns[pass_num % len(patterns)]
                    f.seek(0)
                    
                    # Write pattern in chunks
                    chunk_size = 1024 * 1024  # 1MB chunks
                    bytes_written = 0
                    
                    while bytes_written < file_size:
                        chunk = pattern * min(chunk_size, file_size - bytes_written)
                        f.write(chunk)
                        bytes_written += len(chunk)
                    
                    f.flush()
                    os.fsync(f.fileno())
                    
                    logger.info(f"Completed pass {pass_num + 1}/{total_passes} for {path}")
            
            # Delete the file
            # Final attempt to remove; clear attributes again in case AV changed it
            try:
                os.chmod(path, 0o666)
            except Exception:
                pass
            os.remove(path)
            
            duration = (datetime.now() - start_time).total_seconds()
            return WipeResult(
                success=True,
                method=method,
                target=path,
                size_bytes=file_size,
                passes_completed=total_passes,
                total_passes=total_passes,
                duration_seconds=duration,
                mock_mode=False
            )
            
        except Exception as e:
            raise Exception(f"Failed to wipe file {path}: {e}")
    
    async def _perform_folder_wipe(self, path: str, method: WipeMethod) -> WipeResult:
        """Perform actual folder wiping"""
        start_time = datetime.now()
        total_passes = self._get_total_passes(method)
        total_size = 0
        
        try:
            # Walk through all files in the folder
            for root, dirs, files in os.walk(path, topdown=False):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        file_size = os.path.getsize(file_path)
                        total_size += file_size
                        
                        # Wipe the file
                        # Ensure file is writable (clear read-only attribute on Windows)
                        try:
                            os.chmod(file_path, 0o666)
                        except Exception:
                            pass

                        file_result = await self._perform_file_wipe(file_path, method, file_size)
                        if not file_result.success:
                            logger.warning(f"Failed to wipe file {file_path}: {file_result.error_message}")
                    
                    except Exception as e:
                        logger.warning(f"Error processing file {file_path}: {e}")
                
                # Remove empty directories
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    try:
                        os.rmdir(dir_path)
                    except OSError:
                        pass  # Directory not empty, skip
            
            # Remove the main directory (if empty now)
            try:
                os.rmdir(path)
            except OSError:
                # If not empty due to locked/hidden items, try best-effort removal of remaining files
                for root, dirs, files in os.walk(path, topdown=False):
                    for file in files:
                        fp = os.path.join(root, file)
                        try:
                            os.chmod(fp, 0o666)
                            os.remove(fp)
                        except Exception:
                            logger.warning(f"Residual file could not be removed: {fp}")
                    for d in dirs:
                        dp = os.path.join(root, d)
                        try:
                            os.rmdir(dp)
                        except Exception:
                            pass
                os.rmdir(path)
            
            duration = (datetime.now() - start_time).total_seconds()
            return WipeResult(
                success=True,
                method=method,
                target=path,
                size_bytes=total_size,
                passes_completed=total_passes,
                total_passes=total_passes,
                duration_seconds=duration,
                mock_mode=False
            )
            
        except Exception as e:
            raise Exception(f"Failed to wipe folder {path}: {e}")
    
    async def _perform_drive_wipe(self, device: str, method: WipeMethod) -> WipeResult:
        """Perform actual drive wiping"""
        start_time = datetime.now()
        total_passes = self._get_total_passes(method)
        patterns = self._get_patterns(method)
        
        try:
            # Open device for raw writing
            with open(device, 'wb') as f:
                # Get device size (this is platform-specific)
                device_size = self._get_device_size(device)
                
                for pass_num in range(total_passes):
                    pattern = patterns[pass_num % len(patterns)]
                    f.seek(0)
                    
                    # Write pattern in chunks
                    chunk_size = 1024 * 1024  # 1MB chunks
                    bytes_written = 0
                    
                    while bytes_written < device_size:
                        chunk = pattern * min(chunk_size, device_size - bytes_written)
                        f.write(chunk)
                        bytes_written += len(chunk)
                    
                    f.flush()
                    os.fsync(f.fileno())
                    
                    logger.info(f"Completed pass {pass_num + 1}/{total_passes} for {device}")
            
            duration = (datetime.now() - start_time).total_seconds()
            return WipeResult(
                success=True,
                method=method,
                target=device,
                size_bytes=device_size,
                passes_completed=total_passes,
                total_passes=total_passes,
                duration_seconds=duration,
                mock_mode=False
            )
            
        except Exception as e:
            raise Exception(f"Failed to wipe drive {device}: {e}")
    
    def _get_total_passes(self, method: WipeMethod) -> int:
        """Get total number of passes for a wipe method"""
        if method == WipeMethod.DOD_5220_22_M:
            return 3
        elif method == WipeMethod.NIST_800_88:
            return 1
        elif method == WipeMethod.SINGLE_PASS:
            return 1
        elif method == WipeMethod.GUTMANN:
            return 35
        elif method == WipeMethod.RANDOM:
            return 1
        elif method == WipeMethod.ZERO:
            return 1
        else:
            return 1
    
    def _get_patterns(self, method: WipeMethod) -> List[bytes]:
        """Get patterns for a wipe method"""
        if method == WipeMethod.DOD_5220_22_M:
            return self.dod_patterns
        elif method == WipeMethod.NIST_800_88:
            return self.nist_patterns
        elif method == WipeMethod.SINGLE_PASS:
            return [b'\x00']
        elif method == WipeMethod.GUTMANN:
            return self.gutmann_patterns
        elif method == WipeMethod.RANDOM:
            return [os.urandom(1)]
        elif method == WipeMethod.ZERO:
            return [b'\x00']
        else:
            return [b'\x00']
    
    def _get_device_size(self, device: str) -> int:
        """Get device size in bytes"""
        try:
            # This is a simplified implementation
            # In practice, you'd use platform-specific methods
            if os.path.exists(device):
                stat = os.stat(device)
                return stat.st_size
            return 0
        except Exception:
            return 0
    
    def get_active_operations(self) -> Dict[str, WipeStatus]:
        """Get currently active wipe operations"""
        return self.active_operations.copy()
    
    def cancel_operation(self, operation_id: str) -> bool:
        """Cancel an active wipe operation"""
        if operation_id in self.active_operations:
            self.active_operations[operation_id] = WipeStatus.CANCELLED
            return True
        return False
    
    def set_mock_mode(self, enabled: bool):
        """Enable or disable mock mode"""
        self.mock_mode = enabled
        logger.info(f"Mock mode {'enabled' if enabled else 'disabled'}")
    
    def _check_privileges(self) -> bool:
        """Check if we have elevated privileges for wipe operations"""
        if not self._privilege_checked:
            self._has_elevated_privileges, message = self.privilege_checker.check_privileges()
            self._privilege_checked = True
            logger.info(f"Privilege check: {message}")
        
        return self._has_elevated_privileges
    
    def _validate_privileges_for_operation(self, operation_type: str) -> None:
        """Validate privileges for a specific operation type"""
        if self.mock_mode:
            logger.info(f"Mock mode enabled - skipping privilege check for {operation_type}")
            return
        
        if not self._check_privileges():
            error_msg = (
                f"Insufficient privileges for {operation_type}. "
                f"Secure wiping operations require administrator/root privileges. "
                f"Please run the application with elevated privileges or enable mock mode for testing."
            )
            logger.error(error_msg)
            raise PermissionError(error_msg)
    
    async def generate_certificate_after_wipe(
        self,
        result: WipeResult,
        user_id: int,
        user_name: str,
        user_org: str,
        device_serial: str,
        device_model: str,
        device_type: str,
        db_service: Optional[CertificateDBService] = None
    ) -> Optional[str]:
        """Generate a certificate after a successful wipe operation"""
        if not result.success or not self.generate_certificates:
            return None
        
        try:
            # Generate certificate
            cert_data = await certificate_service.generate_certificate(
                user_id=user_id,
                user_name=user_name,
                user_org=user_org,
                device_serial=device_serial,
                device_model=device_model,
                device_type=device_type,
                wipe_method=result.method.value,
                wipe_status="completed",
                target_path=result.target,
                size_bytes=result.size_bytes,
                passes_completed=result.passes_completed,
                total_passes=result.total_passes,
                duration_seconds=result.duration_seconds,
                verification_hash=result.verification_hash
            )
            
            # Save to database if db_service is provided
            if db_service:
                await db_service.create_certificate(cert_data)
            
            # Update result with certificate info
            result.certificate_id = cert_data.certificate_id
            result.certificate_path = cert_data.certificate_path
            
            logger.info(f"Certificate generated: {cert_data.certificate_id}")
            return cert_data.certificate_id
            
        except Exception as e:
            logger.error(f"Failed to generate certificate: {e}")
            return None


# Global wipe service instance
wipe_service = WipeService(mock_mode=False)
