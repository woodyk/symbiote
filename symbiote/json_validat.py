#!/usr/bin/env python3
#
# json_validat.py

import json

def validate_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Check each site's data for common issues
        for site, details in data.items():
            if not isinstance(details, dict):
                print(f"Error: Entry for {site} is not a dictionary.")
                continue

            if "url" not in details:
                print(f"Warning: 'url' key missing for {site}")

            if "errorType" not in details:
                print(f"Warning: 'errorType' key missing for {site}")

            if "errorMsg" in details and not isinstance(details["errorMsg"], (str, list)):
                print(f"Warning: 'errorMsg' for {site} is not a string or list.")

            if "isNSFW" in details and not isinstance(details["isNSFW"], bool):
                print(f"Warning: 'isNSFW' for {site} is not a boolean.")
        
        print("JSON validation completed successfully.")
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}")
    except Exception as e:
        print(f"Error: {e}")

# Example usage
validate_json('sherlock_data.json')

