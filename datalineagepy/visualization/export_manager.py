"""
Export manager for data lineage visualizations.
Supports multiple export formats and batch processing.
"""

import asyncio
import json
import logging
import os
import tempfile
import zipfile
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Callable, Set, Union, BinaryIO, Tuple
from datetime import datetime
from enum import Enum
import threading
import uuid
import base64
from pathlib import Path

try:
    import plotly.graph_objects as go
    import plotly.io as pio
    from plotly.offline import plot
    import pandas as pd
    import numpy as np
except ImportError:
    go = None
    pio = None
    plot = None
    pd = None
    np = None

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

try:
    from PIL import Image as PILImage
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

logger = logging.getLogger(__name__)


class ExportFormat(Enum):
    """Supported export formats."""
    PNG = "png"
    JPEG = "jpeg"
    SVG = "svg"
    PDF = "pdf"
    HTML = "html"
    JSON = "json"
    CSV = "csv"
    EXCEL = "excel"
    POWERPOINT = "powerpoint"
    WORD = "word"
    ZIP = "zip"


class ExportQuality(Enum):
    """Export quality settings."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ULTRA = "ultra"


class ExportSize(Enum):
    """Predefined export sizes."""
    THUMBNAIL = "thumbnail"      # 200x150
    SMALL = "small"             # 800x600
    MEDIUM = "medium"           # 1200x900
    LARGE = "large"             # 1920x1080
    EXTRA_LARGE = "xl"          # 2560x1440
    PRINT_LETTER = "print_letter"  # 8.5x11 inches
    PRINT_A4 = "print_a4"      # A4 size
    CUSTOM = "custom"


@dataclass
class ExportConfig:
    """Configuration for export operations."""
    format: ExportFormat
    quality: ExportQuality = ExportQuality.HIGH
    size: ExportSize = ExportSize.LARGE

    # Custom dimensions (used when size is CUSTOM)
    width: Optional[int] = None
    height: Optional[int] = None
    dpi: int = 300

    # File settings
    filename: Optional[str] = None
    output_dir: str = "exports"
    include_timestamp: bool = True

    # Content settings
    include_title: bool = True
    include_legend: bool = True
    include_metadata: bool = True
    include_statistics: bool = False

    # Styling
    background_color: str = "white"
    theme: str = "plotly_white"
    font_family: str = "Arial"
    font_size: int = 12

    # Batch settings
    batch_processing: bool = False
    compression: bool = True

    # Security
    watermark: Optional[str] = None
    password_protect: bool = False
    password: Optional[str] = None


@dataclass
class ExportJob:
    """Export job tracking."""
    id: str
    config: ExportConfig
    source_data: Any
    status: str = "pending"  # pending, processing, completed, failed
    progress: float = 0.0
    output_path: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    file_size: Optional[int] = None


class ExportManager:
    """Manager for exporting data lineage visualizations."""

    def __init__(self, base_output_dir: str = "exports"):
        self.base_output_dir = Path(base_output_dir)
        self.base_output_dir.mkdir(exist_ok=True)

        # Job tracking
        self.jobs: Dict[str, ExportJob] = {}
        self.job_queue: asyncio.Queue = asyncio.Queue()
        self.worker_tasks: List[asyncio.Task] = []
        self.max_workers: int = 3

        # Export handlers
        self.format_handlers: Dict[ExportFormat, Callable] = {
            ExportFormat.PNG: self._export_png,
            ExportFormat.JPEG: self._export_jpeg,
            ExportFormat.SVG: self._export_svg,
            ExportFormat.PDF: self._export_pdf,
            ExportFormat.HTML: self._export_html,
            ExportFormat.JSON: self._export_json,
            ExportFormat.CSV: self._export_csv,
            ExportFormat.EXCEL: self._export_excel,
            ExportFormat.ZIP: self._export_zip,
        }

        # Statistics
        self.stats = {
            'total_exports': 0,
            'successful_exports': 0,
            'failed_exports': 0,
            'total_file_size': 0,
            'export_formats': {},
            'average_export_time': 0.0,
            'last_export': None,
        }

        self._lock = threading.Lock()
        self._running = False

        # Check dependencies
        if go is None:
            raise ImportError("plotly is required for export functionality")

    async def start(self):
        """Start the export manager."""
        self._running = True

        # Start worker tasks
        for i in range(self.max_workers):
            task = asyncio.create_task(self._worker(f"worker-{i}"))
            self.worker_tasks.append(task)

        logger.info(f"Export manager started with {self.max_workers} workers")

    async def stop(self):
        """Stop the export manager."""
        self._running = False

        # Cancel worker tasks
        for task in self.worker_tasks:
            task.cancel()

        # Wait for tasks to complete
        if self.worker_tasks:
            await asyncio.gather(*self.worker_tasks, return_exceptions=True)

        self.worker_tasks.clear()
        logger.info("Export manager stopped")

    async def export_visualization(
        self,
        figure: go.Figure,
        config: ExportConfig,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Export a visualization with the given configuration."""
        # Create export job
        job = ExportJob(
            id=str(uuid.uuid4()),
            config=config,
            source_data={'figure': figure, 'metadata': metadata or {}}
        )

        # Add to tracking
        with self._lock:
            self.jobs[job.id] = job

        # Queue for processing
        await self.job_queue.put(job)

        return job.id

    async def export_dashboard(
        self,
        dashboard_html: str,
        config: ExportConfig,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Export a dashboard with the given configuration."""
        # Create export job
        job = ExportJob(
            id=str(uuid.uuid4()),
            config=config,
            source_data={'dashboard_html': dashboard_html,
                         'metadata': metadata or {}}
        )

        # Add to tracking
        with self._lock:
            self.jobs[job.id] = job

        # Queue for processing
        await self.job_queue.put(job)

        return job.id

    async def export_data(
        self,
        data: Union[Dict, List, pd.DataFrame],
        config: ExportConfig,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Export raw data with the given configuration."""
        # Create export job
        job = ExportJob(
            id=str(uuid.uuid4()),
            config=config,
            source_data={'data': data, 'metadata': metadata or {}}
        )

        # Add to tracking
        with self._lock:
            self.jobs[job.id] = job

        # Queue for processing
        await self.job_queue.put(job)

        return job.id

    async def batch_export(
        self,
        items: List[Dict[str, Any]],
        base_config: ExportConfig
    ) -> List[str]:
        """Export multiple items in batch."""
        job_ids = []

        for i, item in enumerate(items):
            # Create individual config
            config = ExportConfig(
                format=base_config.format,
                quality=base_config.quality,
                size=base_config.size,
                width=base_config.width,
                height=base_config.height,
                filename=f"{base_config.filename or 'export'}_{i+1:03d}",
                output_dir=base_config.output_dir,
                batch_processing=True,
                **item.get('config_overrides', {})
            )

            # Create job
            job = ExportJob(
                id=str(uuid.uuid4()),
                config=config,
                source_data=item
            )

            # Add to tracking
            with self._lock:
                self.jobs[job.id] = job

            # Queue for processing
            await self.job_queue.put(job)
            job_ids.append(job.id)

        return job_ids

    async def get_job_status(self, job_id: str) -> Optional[ExportJob]:
        """Get the status of an export job."""
        with self._lock:
            return self.jobs.get(job_id)

    async def wait_for_job(self, job_id: str, timeout: float = 60.0) -> ExportJob:
        """Wait for an export job to complete."""
        start_time = asyncio.get_event_loop().time()

        while True:
            job = await self.get_job_status(job_id)
            if not job:
                raise ValueError(f"Job {job_id} not found")

            if job.status in ['completed', 'failed']:
                return job

            # Check timeout
            if asyncio.get_event_loop().time() - start_time > timeout:
                raise TimeoutError(f"Export job {job_id} timed out")

            await asyncio.sleep(0.1)

    async def _worker(self, worker_name: str):
        """Worker task for processing export jobs."""
        logger.info(f"Export worker {worker_name} started")

        while self._running:
            try:
                # Get job from queue
                job = await asyncio.wait_for(self.job_queue.get(), timeout=1.0)

                # Process job
                await self._process_job(job)

                # Mark task as done
                self.job_queue.task_done()

            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in export worker {worker_name}: {e}")

        logger.info(f"Export worker {worker_name} stopped")

    async def _process_job(self, job: ExportJob):
        """Process a single export job."""
        try:
            # Update job status
            job.status = "processing"
            job.started_at = datetime.utcnow()
            job.progress = 0.1

            # Get handler for format
            handler = self.format_handlers.get(job.config.format)
            if not handler:
                raise ValueError(
                    f"Unsupported export format: {job.config.format}")

            # Create output directory
            output_dir = self.base_output_dir / job.config.output_dir
            output_dir.mkdir(parents=True, exist_ok=True)

            # Generate filename
            filename = self._generate_filename(job)
            output_path = output_dir / filename

            job.progress = 0.3

            # Execute export
            await handler(job, output_path)

            job.progress = 0.9

            # Get file size
            if output_path.exists():
                job.file_size = output_path.stat().st_size
                job.output_path = str(output_path)

            # Update job status
            job.status = "completed"
            job.completed_at = datetime.utcnow()
            job.progress = 1.0

            # Update statistics
            with self._lock:
                self.stats['total_exports'] += 1
                self.stats['successful_exports'] += 1
                self.stats['total_file_size'] += job.file_size or 0

                format_key = job.config.format.value
                self.stats['export_formats'][format_key] = self.stats['export_formats'].get(
                    format_key, 0) + 1

                # Calculate average export time
                if job.started_at and job.completed_at:
                    export_time = (job.completed_at -
                                   job.started_at).total_seconds()
                    current_avg = self.stats['average_export_time']
                    total_exports = self.stats['successful_exports']
                    self.stats['average_export_time'] = (
                        current_avg * (total_exports - 1) + export_time) / total_exports

                self.stats['last_export'] = datetime.utcnow()

            logger.info(f"Export job {job.id} completed successfully")

        except Exception as e:
            # Update job status
            job.status = "failed"
            job.error = str(e)
            job.completed_at = datetime.utcnow()

            # Update statistics
            with self._lock:
                self.stats['total_exports'] += 1
                self.stats['failed_exports'] += 1

            logger.error(f"Export job {job.id} failed: {e}")

    def _generate_filename(self, job: ExportJob) -> str:
        """Generate filename for export."""
        base_name = job.config.filename or "export"

        # Add timestamp if requested
        if job.config.include_timestamp:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            base_name = f"{base_name}_{timestamp}"

        # Add extension
        extension = job.config.format.value
        if extension == "jpeg":
            extension = "jpg"

        return f"{base_name}.{extension}"

    def _get_dimensions(self, config: ExportConfig) -> Tuple[int, int]:
        """Get export dimensions based on configuration."""
        if config.size == ExportSize.CUSTOM and config.width and config.height:
            return config.width, config.height

        size_map = {
            ExportSize.THUMBNAIL: (200, 150),
            ExportSize.SMALL: (800, 600),
            ExportSize.MEDIUM: (1200, 900),
            ExportSize.LARGE: (1920, 1080),
            ExportSize.EXTRA_LARGE: (2560, 1440),
            ExportSize.PRINT_LETTER: (2550, 3300),  # 8.5x11 at 300 DPI
            ExportSize.PRINT_A4: (2480, 3508),     # A4 at 300 DPI
        }

        return size_map.get(config.size, (1200, 900))

    async def _export_png(self, job: ExportJob, output_path: Path):
        """Export as PNG image."""
        if 'figure' not in job.source_data:
            raise ValueError("Figure required for PNG export")

        figure = job.source_data['figure']
        width, height = self._get_dimensions(job.config)

        # Configure figure
        figure.update_layout(
            width=width,
            height=height,
            paper_bgcolor=job.config.background_color,
            plot_bgcolor=job.config.background_color,
            font=dict(family=job.config.font_family, size=job.config.font_size)
        )

        # Export
        pio.write_image(
            figure,
            str(output_path),
            format="png",
            width=width,
            height=height,
            scale=2 if job.config.quality == ExportQuality.HIGH else 1
        )

    async def _export_jpeg(self, job: ExportJob, output_path: Path):
        """Export as JPEG image."""
        if 'figure' not in job.source_data:
            raise ValueError("Figure required for JPEG export")

        figure = job.source_data['figure']
        width, height = self._get_dimensions(job.config)

        # Configure figure
        figure.update_layout(
            width=width,
            height=height,
            paper_bgcolor=job.config.background_color,
            plot_bgcolor=job.config.background_color,
            font=dict(family=job.config.font_family, size=job.config.font_size)
        )

        # Export
        pio.write_image(
            figure,
            str(output_path),
            format="jpg",
            width=width,
            height=height,
            scale=2 if job.config.quality == ExportQuality.HIGH else 1
        )

    async def _export_svg(self, job: ExportJob, output_path: Path):
        """Export as SVG vector image."""
        if 'figure' not in job.source_data:
            raise ValueError("Figure required for SVG export")

        figure = job.source_data['figure']
        width, height = self._get_dimensions(job.config)

        # Configure figure
        figure.update_layout(
            width=width,
            height=height,
            paper_bgcolor=job.config.background_color,
            plot_bgcolor=job.config.background_color,
            font=dict(family=job.config.font_family, size=job.config.font_size)
        )

        # Export
        pio.write_image(
            figure,
            str(output_path),
            format="svg",
            width=width,
            height=height
        )

    async def _export_pdf(self, job: ExportJob, output_path: Path):
        """Export as PDF document."""
        if not REPORTLAB_AVAILABLE:
            raise ImportError("reportlab is required for PDF export")

        # Create PDF document
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4 if job.config.size == ExportSize.PRINT_A4 else letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )

        # Build content
        story = []
        styles = getSampleStyleSheet()

        # Title
        if job.config.include_title:
            title = job.source_data.get('metadata', {}).get(
                'title', 'Data Lineage Visualization')
            story.append(Paragraph(title, styles['Title']))
            story.append(Spacer(1, 12))

        # Add figure if present
        if 'figure' in job.source_data:
            # Export figure as temporary image
            temp_img_path = output_path.with_suffix('.temp.png')

            figure = job.source_data['figure']
            width, height = self._get_dimensions(job.config)

            pio.write_image(
                figure,
                str(temp_img_path),
                format="png",
                width=width,
                height=height,
                scale=2
            )

            # Add image to PDF
            img = Image(str(temp_img_path))
            img.drawHeight = 6 * inch
            img.drawWidth = 8 * inch
            story.append(img)
            story.append(Spacer(1, 12))

            # Clean up temp file
            temp_img_path.unlink()

        # Add metadata table
        if job.config.include_metadata:
            metadata = job.source_data.get('metadata', {})
            if metadata:
                story.append(Paragraph("Metadata", styles['Heading2']))

                table_data = [['Property', 'Value']]
                for key, value in metadata.items():
                    table_data.append([str(key), str(value)])

                table = Table(table_data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 14),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))

                story.append(table)

        # Build PDF
        doc.build(story)

    async def _export_html(self, job: ExportJob, output_path: Path):
        """Export as HTML document."""
        if 'figure' in job.source_data:
            figure = job.source_data['figure']

            # Configure figure
            width, height = self._get_dimensions(job.config)
            figure.update_layout(
                width=width,
                height=height,
                paper_bgcolor=job.config.background_color,
                plot_bgcolor=job.config.background_color,
                font=dict(family=job.config.font_family,
                          size=job.config.font_size)
            )

            # Export as HTML
            html_content = pio.to_html(
                figure,
                include_plotlyjs='cdn',
                div_id="lineage-visualization"
            )

        elif 'dashboard_html' in job.source_data:
            html_content = job.source_data['dashboard_html']
        else:
            raise ValueError(
                "Figure or dashboard HTML required for HTML export")

        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

    async def _export_json(self, job: ExportJob, output_path: Path):
        """Export as JSON data."""
        if 'data' in job.source_data:
            data = job.source_data['data']
        elif 'figure' in job.source_data:
            # Export figure as JSON
            figure = job.source_data['figure']
            data = figure.to_dict()
        else:
            data = job.source_data

        # Write JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)

    async def _export_csv(self, job: ExportJob, output_path: Path):
        """Export as CSV data."""
        if not pd:
            raise ImportError("pandas is required for CSV export")

        data = job.source_data.get('data')
        if not data:
            raise ValueError("Data required for CSV export")

        # Convert to DataFrame if needed
        if isinstance(data, dict):
            df = pd.DataFrame(data)
        elif isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, pd.DataFrame):
            df = data
        else:
            raise ValueError("Unsupported data format for CSV export")

        # Export CSV
        df.to_csv(output_path, index=False)

    async def _export_excel(self, job: ExportJob, output_path: Path):
        """Export as Excel file."""
        if not pd:
            raise ImportError("pandas is required for Excel export")

        data = job.source_data.get('data')
        if not data:
            raise ValueError("Data required for Excel export")

        # Convert to DataFrame if needed
        if isinstance(data, dict):
            df = pd.DataFrame(data)
        elif isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, pd.DataFrame):
            df = data
        else:
            raise ValueError("Unsupported data format for Excel export")

        # Export Excel
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Data', index=False)

            # Add metadata sheet if available
            metadata = job.source_data.get('metadata', {})
            if metadata:
                metadata_df = pd.DataFrame(
                    list(metadata.items()), columns=['Property', 'Value'])
                metadata_df.to_excel(
                    writer, sheet_name='Metadata', index=False)

    async def _export_zip(self, job: ExportJob, output_path: Path):
        """Export as ZIP archive."""
        # Create temporary directory for files
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Export multiple formats
            formats_to_export = [
                ExportFormat.PNG,
                ExportFormat.HTML,
                ExportFormat.JSON
            ]

            files_to_zip = []

            for fmt in formats_to_export:
                try:
                    # Create temporary job for this format
                    temp_config = ExportConfig(
                        format=fmt,
                        quality=job.config.quality,
                        size=job.config.size,
                        filename=f"export_{fmt.value}",
                        include_timestamp=False
                    )

                    temp_job = ExportJob(
                        id=f"{job.id}_{fmt.value}",
                        config=temp_config,
                        source_data=job.source_data
                    )

                    # Export to temp directory
                    temp_file = temp_path / f"export.{fmt.value}"
                    handler = self.format_handlers.get(fmt)
                    if handler:
                        await handler(temp_job, temp_file)
                        if temp_file.exists():
                            files_to_zip.append(temp_file)

                except Exception as e:
                    logger.warning(
                        f"Failed to export {fmt.value} for ZIP: {e}")

            # Create ZIP file
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in files_to_zip:
                    zipf.write(file_path, file_path.name)

    def get_stats(self) -> Dict[str, Any]:
        """Get export manager statistics."""
        with self._lock:
            return self.stats.copy()

    def cleanup_old_exports(self, days_old: int = 30):
        """Clean up old export files."""
        cutoff_date = datetime.utcnow().timestamp() - (days_old * 24 * 60 * 60)

        cleaned_count = 0
        cleaned_size = 0

        for export_dir in self.base_output_dir.iterdir():
            if export_dir.is_dir():
                for file_path in export_dir.iterdir():
                    if file_path.is_file() and file_path.stat().st_mtime < cutoff_date:
                        file_size = file_path.stat().st_size
                        file_path.unlink()
                        cleaned_count += 1
                        cleaned_size += file_size

        logger.info(
            f"Cleaned up {cleaned_count} old export files ({cleaned_size} bytes)")
        return {'files_cleaned': cleaned_count, 'bytes_cleaned': cleaned_size}


def create_export_manager(base_output_dir: str = "exports") -> ExportManager:
    """Factory function to create export manager."""
    return ExportManager(base_output_dir)


def create_export_config(
    format: ExportFormat,
    quality: ExportQuality = ExportQuality.HIGH,
    size: ExportSize = ExportSize.LARGE,
    **kwargs
) -> ExportConfig:
    """Factory function to create export configuration."""
    return ExportConfig(
        format=format,
        quality=quality,
        size=size,
        **kwargs
    )
