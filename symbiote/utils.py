#!/usr/bin/env python3
#
# symbiote/utils.py

import subprocess
import json

def extract_metadata(filepath):
    """Extracts metadata from a file using exiftool"""
    # Run exiftool with the '-j' flag to output metadata as JSON
    result = subprocess.run(['exiftool', '-j', filepath], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise RuntimeError(f'exiftool failed with code {result.returncode}: {result.stderr.decode()}')
    # Parse the JSON output and return the metadata as a dictionary
    metadata = json.loads(result.stdout.decode())[0]
    return metadata
