import fnmatch
import shutil
import tempfile
import zipfile
from itertools import batched
from pathlib import Path

import duckdb
from rich.progress import track

from .. import console

conn = duckdb.connect()
conn.execute("SET enable_progress_bar = false")


def convert_zip_to_parquet(
    zip_file_path: str | Path,
    parquet_dir_path: str | Path,
    batch_size: int = 10,
) -> None:
    """Convert a zip archive from the DVSA MOT History API to a directory of
    Parquet files.

    The zip file should contain bulk data as gzipped JSON files. The gzip files
    will be extracted from the zip file to a temporary directory in batches (to
    save disk space during the conversion). DuckDB will be used to import each
    batch into a Parquet file.

    Args:
        zip_file_path: Path to the zip archive.
        parquet_dir_path: Directory for output Parquet files.
        batch_size: Number of gzipped JSON files to process in each batch. Also
            determines the number of output Parquet files.
    """
    zip_file_path = Path(zip_file_path)
    parquet_dir_path = Path(parquet_dir_path)

    with (
        zipfile.ZipFile(zip_file_path, "r") as zip_file,
        tempfile.TemporaryDirectory(prefix=".tmp-", dir=parquet_dir_path.parent) as temp_dir,
    ):
        temp_dir = Path(temp_dir)

        # We are only interested in bulk gzip files and not delta gzip files that will also be
        # present in the zip archive
        gzip_files = fnmatch.filter(zip_file.namelist(), "bulk-light-vehicle_*_*.json.gz")
        if not gzip_files:
            raise ValueError("No bulk gzipped JSON files found in the zip archive.")

        # We save parquet data into the temporary directory and only move it when everything else is
        # successful
        temp_parquet_dir = temp_dir / "output.parquet.d"
        temp_parquet_dir.mkdir()

        # Extract, import, remove for each batch of gzip files
        batched_gzip_files = list(batched(gzip_files, batch_size))
        filename_padding = len(str(len(batched_gzip_files)))
        for batch_no, batch_files in enumerate(track(batched_gzip_files, console=console)):
            zip_file.extractall(path=temp_dir, members=batch_files)
            conn.execute(f"""
                COPY (SELECT * FROM read_json('{temp_dir / "*.json.gz"}'))
                TO '{temp_parquet_dir / f"bulk_{batch_no:0{filename_padding}}.parquet"}';
            """)
            for batch_file in batch_files:
                (temp_dir / batch_file).unlink()

        shutil.rmtree(parquet_dir_path, ignore_errors=True)
        temp_parquet_dir.rename(parquet_dir_path)
