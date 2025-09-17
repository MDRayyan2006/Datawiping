import os
import json
import hashlib
import base64
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography import x509
from cryptography.x509.oid import NameOID
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

logger = logging.getLogger(__name__)


@dataclass
class WipeCertificate:
    """Certificate data for wipe verification"""
    certificate_id: str
    user_id: int
    user_name: str
    user_org: str
    device_serial: str
    device_model: str
    device_type: str
    wipe_method: str
    wipe_status: str
    target_path: str
    size_bytes: int
    passes_completed: int
    total_passes: int
    duration_seconds: float
    verification_hash: Optional[str]
    certificate_path: str
    json_path: str
    pdf_path: str
    signature_path: str
    created_at: datetime
    expires_at: datetime


@dataclass
class CertificateKeyPair:
    """RSA key pair for certificate signing"""
    private_key: rsa.RSAPrivateKey
    public_key: rsa.RSAPublicKey
    certificate: x509.Certificate


class CertificateService:
    """Service for generating and managing wipe certificates"""
    
    def __init__(self, cert_dir: str = "certificates", key_size: int = 2048):
        self.cert_dir = Path(cert_dir)
        self.cert_dir.mkdir(exist_ok=True)
        self.key_size = key_size
        self.key_pair: Optional[CertificateKeyPair] = None
        
        # Initialize or load existing key pair
        self._initialize_key_pair()
    
    def _initialize_key_pair(self):
        """Initialize or load the certificate key pair"""
        private_key_path = self.cert_dir / "private_key.pem"
        public_key_path = self.cert_dir / "public_key.pem"
        cert_path = self.cert_dir / "certificate.pem"
        
        if all(path.exists() for path in [private_key_path, public_key_path, cert_path]):
            # Load existing keys
            self._load_key_pair(private_key_path, public_key_path, cert_path)
        else:
            # Generate new key pair
            self._generate_key_pair(private_key_path, public_key_path, cert_path)
    
    def _generate_key_pair(self, private_key_path: Path, public_key_path: Path, cert_path: Path):
        """Generate a new RSA key pair and self-signed certificate"""
        logger.info("Generating new certificate key pair...")
        
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=self.key_size
        )
        
        # Generate public key
        public_key = private_key.public_key()
        
        # Create self-signed certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "DataWipe"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Certificate Authority"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "DataWipe API"),
            x509.NameAttribute(NameOID.COMMON_NAME, "DataWipe Certificate Authority"),
        ])
        
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            public_key
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.now(timezone.utc)
        ).not_valid_after(
            datetime.now(timezone.utc).replace(year=datetime.now().year + 10)
        ).add_extension(
            x509.BasicConstraints(ca=True, path_length=None),
            critical=True,
        ).sign(private_key, hashes.SHA256())
        
        # Save private key
        with open(private_key_path, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        # Save public key
        with open(public_key_path, "wb") as f:
            f.write(public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ))
        
        # Save certificate
        with open(cert_path, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        
        self.key_pair = CertificateKeyPair(private_key, public_key, cert)
        logger.info("Certificate key pair generated successfully")
    
    def _load_key_pair(self, private_key_path: Path, public_key_path: Path, cert_path: Path):
        """Load existing key pair from files"""
        logger.info("Loading existing certificate key pair...")
        
        # Load private key
        with open(private_key_path, "rb") as f:
            private_key = serialization.load_pem_private_key(
                f.read(), password=None
            )
        
        # Load public key
        with open(public_key_path, "rb") as f:
            public_key = serialization.load_pem_public_key(f.read())
        
        # Load certificate
        with open(cert_path, "rb") as f:
            cert = x509.load_pem_x509_certificate(f.read())
        
        self.key_pair = CertificateKeyPair(private_key, public_key, cert)
        logger.info("Certificate key pair loaded successfully")
    
    async def generate_certificate(
        self,
        user_id: int,
        user_name: str,
        user_org: str,
        device_serial: str,
        device_model: str,
        device_type: str,
        wipe_method: str,
        wipe_status: str,
        target_path: str,
        size_bytes: int,
        passes_completed: int,
        total_passes: int,
        duration_seconds: float,
        verification_hash: Optional[str] = None
    ) -> WipeCertificate:
        """Generate a complete wipe certificate with JSON and PDF reports"""
        
        certificate_id = self._generate_certificate_id()
        created_at = datetime.now(timezone.utc)
        expires_at = created_at.replace(year=created_at.year + 1)
        
        # Create certificate data
        cert_data = WipeCertificate(
            certificate_id=certificate_id,
            user_id=user_id,
            user_name=user_name,
            user_org=user_org,
            device_serial=device_serial,
            device_model=device_model,
            device_type=device_type,
            wipe_method=wipe_method,
            wipe_status=wipe_status,
            target_path=target_path,
            size_bytes=size_bytes,
            passes_completed=passes_completed,
            total_passes=total_passes,
            duration_seconds=duration_seconds,
            verification_hash=verification_hash,
            certificate_path="",  # Will be set below
            json_path="",  # Will be set below
            pdf_path="",  # Will be set below
            signature_path="",  # Will be set below
            created_at=created_at,
            expires_at=expires_at
        )
        
        # Generate file paths
        cert_dir = self.cert_dir / certificate_id
        cert_dir.mkdir(exist_ok=True)
        
        json_path = cert_dir / f"{certificate_id}.json"
        pdf_path = cert_dir / f"{certificate_id}.pdf"
        signature_path = cert_dir / f"{certificate_id}.sig"
        
        # Update paths
        cert_data.certificate_path = str(cert_dir)
        cert_data.json_path = str(json_path)
        cert_data.pdf_path = str(pdf_path)
        cert_data.signature_path = str(signature_path)
        
        # Generate JSON report
        await self._generate_json_report(cert_data, json_path)
        
        # Generate PDF report
        await self._generate_pdf_report(cert_data, pdf_path)
        
        # Generate digital signature
        await self._generate_digital_signature(cert_data, signature_path)
        
        logger.info(f"Certificate generated successfully: {certificate_id}")
        return cert_data
    
    async def _generate_json_report(self, cert_data: WipeCertificate, json_path: Path):
        """Generate JSON report with certificate data"""
        report_data = {
            "certificate": {
                "id": cert_data.certificate_id,
                "created_at": cert_data.created_at.isoformat(),
                "expires_at": cert_data.expires_at.isoformat(),
                "status": "valid"
            },
            "user": {
                "id": cert_data.user_id,
                "name": cert_data.user_name,
                "organization": cert_data.user_org
            },
            "device": {
                "serial": cert_data.device_serial,
                "model": cert_data.device_model,
                "type": cert_data.device_type
            },
            "wipe_operation": {
                "method": cert_data.wipe_method,
                "status": cert_data.wipe_status,
                "target_path": cert_data.target_path,
                "size_bytes": cert_data.size_bytes,
                "size_human": self._format_size(cert_data.size_bytes),
                "passes_completed": cert_data.passes_completed,
                "total_passes": cert_data.total_passes,
                "duration_seconds": cert_data.duration_seconds,
                "verification_hash": cert_data.verification_hash
            },
            "verification": {
                "certificate_hash": self._calculate_certificate_hash(cert_data),
                "signature_algorithm": "RSA-SHA256",
                "key_size": self.key_size,
                "certificate_authority": "DataWipe API"
            }
        }
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"JSON report generated: {json_path}")
    
    async def _generate_pdf_report(self, cert_data: WipeCertificate, pdf_path: Path):
        """Generate PDF report with certificate data"""
        doc = SimpleDocTemplate(str(pdf_path), pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        story.append(Paragraph("Data Wipe Certificate", title_style))
        story.append(Spacer(1, 12))
        
        # Certificate ID
        cert_id_style = ParagraphStyle(
            'CertificateID',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=6,
            alignment=TA_CENTER,
            textColor=colors.grey
        )
        story.append(Paragraph(f"Certificate ID: {cert_data.certificate_id}", cert_id_style))
        story.append(Spacer(1, 20))
        
        # Certificate Information Table
        cert_data_table = [
            ["Field", "Value"],
            ["Certificate ID", cert_data.certificate_id],
            ["Created At", cert_data.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")],
            ["Expires At", cert_data.expires_at.strftime("%Y-%m-%d %H:%M:%S UTC")],
            ["Status", "Valid"]
        ]
        
        cert_table = Table(cert_data_table, colWidths=[2*inch, 4*inch])
        cert_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(Paragraph("Certificate Information", styles['Heading2']))
        story.append(cert_table)
        story.append(Spacer(1, 20))
        
        # User Information Table
        user_data_table = [
            ["Field", "Value"],
            ["User ID", str(cert_data.user_id)],
            ["User Name", cert_data.user_name],
            ["Organization", cert_data.user_org]
        ]
        
        user_table = Table(user_data_table, colWidths=[2*inch, 4*inch])
        user_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(Paragraph("User Information", styles['Heading2']))
        story.append(user_table)
        story.append(Spacer(1, 20))
        
        # Device Information Table
        device_data_table = [
            ["Field", "Value"],
            ["Device Serial", cert_data.device_serial],
            ["Device Model", cert_data.device_model],
            ["Device Type", cert_data.device_type]
        ]
        
        device_table = Table(device_data_table, colWidths=[2*inch, 4*inch])
        device_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(Paragraph("Device Information", styles['Heading2']))
        story.append(device_table)
        story.append(Spacer(1, 20))
        
        # Wipe Operation Table
        wipe_data_table = [
            ["Field", "Value"],
            ["Wipe Method", cert_data.wipe_method],
            ["Status", cert_data.wipe_status],
            ["Target Path", cert_data.target_path],
            ["Size", f"{self._format_size(cert_data.size_bytes)} ({cert_data.size_bytes:,} bytes)"],
            ["Passes Completed", f"{cert_data.passes_completed}/{cert_data.total_passes}"],
            ["Duration", f"{cert_data.duration_seconds:.2f} seconds"],
            ["Verification Hash", cert_data.verification_hash or "N/A"]
        ]
        
        wipe_table = Table(wipe_data_table, colWidths=[2*inch, 4*inch])
        wipe_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(Paragraph("Wipe Operation Details", styles['Heading2']))
        story.append(wipe_table)
        story.append(Spacer(1, 20))
        
        # Verification Information
        verification_data_table = [
            ["Field", "Value"],
            ["Certificate Hash", self._calculate_certificate_hash(cert_data)],
            ["Signature Algorithm", "RSA-SHA256"],
            ["Key Size", f"{self.key_size} bits"],
            ["Certificate Authority", "DataWipe API"]
        ]
        
        verification_table = Table(verification_data_table, colWidths=[2*inch, 4*inch])
        verification_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(Paragraph("Verification Information", styles['Heading2']))
        story.append(verification_table)
        story.append(Spacer(1, 30))
        
        # Footer
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_CENTER,
            textColor=colors.grey
        )
        story.append(Paragraph("This certificate was digitally signed and can be verified using the provided signature file.", footer_style))
        story.append(Paragraph(f"Generated by DataWipe API on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", footer_style))
        
        doc.build(story)
        logger.info(f"PDF report generated: {pdf_path}")
    
    async def _generate_digital_signature(self, cert_data: WipeCertificate, signature_path: Path):
        """Generate digital signature for the certificate"""
        if not self.key_pair:
            raise Exception("Certificate key pair not initialized")
        
        # Create data to sign (certificate data + JSON content)
        json_path = Path(cert_data.json_path)
        with open(json_path, 'rb') as f:
            json_content = f.read()
        
        # Create signature data
        signature_data = {
            "certificate_id": cert_data.certificate_id,
            "created_at": cert_data.created_at.isoformat(),
            "json_hash": hashlib.sha256(json_content).hexdigest(),
            "pdf_hash": hashlib.sha256(open(cert_data.pdf_path, 'rb').read()).hexdigest()
        }
        
        # Convert to bytes for signing
        signature_bytes = json.dumps(signature_data, sort_keys=True).encode('utf-8')
        
        # Sign the data
        signature = self.key_pair.private_key.sign(
            signature_bytes,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        # Save signature
        signature_info = {
            "signature": base64.b64encode(signature).decode('utf-8'),
            "algorithm": "RSA-SHA256",
            "key_size": self.key_size,
            "signed_data": signature_data,
            "public_key": self.key_pair.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode('utf-8')
        }
        
        with open(signature_path, 'w') as f:
            json.dump(signature_info, f, indent=2)
        
        logger.info(f"Digital signature generated: {signature_path}")
    
    def _generate_certificate_id(self) -> str:
        """Generate a unique certificate ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_suffix = hashlib.md5(os.urandom(16)).hexdigest()[:8]
        return f"CERT-{timestamp}-{random_suffix}"
    
    def _calculate_certificate_hash(self, cert_data: WipeCertificate) -> str:
        """Calculate hash of certificate data for verification"""
        cert_string = f"{cert_data.certificate_id}{cert_data.user_id}{cert_data.device_serial}{cert_data.wipe_method}{cert_data.created_at.isoformat()}"
        return hashlib.sha256(cert_string.encode('utf-8')).hexdigest()
    
    def _format_size(self, size_bytes: int) -> str:
        """Format size in bytes to human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB", "PB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    async def verify_certificate(self, certificate_id: str) -> Dict[str, Any]:
        """Verify a certificate's digital signature"""
        cert_dir = self.cert_dir / certificate_id
        signature_path = cert_dir / f"{certificate_id}.sig"
        json_path = cert_dir / f"{certificate_id}.json"
        
        if not signature_path.exists() or not json_path.exists():
            return {"valid": False, "error": "Certificate files not found"}
        
        try:
            # Load signature
            with open(signature_path, 'r') as f:
                signature_info = json.load(f)
            
            # Load JSON content
            with open(json_path, 'rb') as f:
                json_content = f.read()
            
            # Recreate signature data
            signature_data = {
                "certificate_id": certificate_id,
                "created_at": signature_info["signed_data"]["created_at"],
                "json_hash": hashlib.sha256(json_content).hexdigest(),
                "pdf_hash": signature_info["signed_data"]["pdf_hash"]
            }
            
            # Convert to bytes
            signature_bytes = json.dumps(signature_data, sort_keys=True).encode('utf-8')
            
            # Decode signature
            signature = base64.b64decode(signature_info["signature"])
            
            # Verify signature
            self.key_pair.public_key.verify(
                signature,
                signature_bytes,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            return {
                "valid": True,
                "certificate_id": certificate_id,
                "verified_at": datetime.now().isoformat(),
                "algorithm": signature_info["algorithm"],
                "key_size": signature_info["key_size"]
            }
            
        except Exception as e:
            return {"valid": False, "error": str(e)}
    
    def get_certificate_paths(self, certificate_id: str) -> Dict[str, str]:
        """Get file paths for a certificate"""
        cert_dir = self.cert_dir / certificate_id
        return {
            "certificate_dir": str(cert_dir),
            "json_path": str(cert_dir / f"{certificate_id}.json"),
            "pdf_path": str(cert_dir / f"{certificate_id}.pdf"),
            "signature_path": str(cert_dir / f"{certificate_id}.sig")
        }


# Global certificate service instance
certificate_service = CertificateService()
