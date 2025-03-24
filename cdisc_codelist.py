#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CDISC Codelist Retrieval Tool

A Python implementation of the SAS macro for fetching CDISC Controlled Terminology codelists
from the CDISC Library API, using only standard libraries and requests.
"""

import os
import sys
import json
import argparse
import requests
from dotenv import load_dotenv
import csv
from datetime import datetime

# Load environment variables from .env file
load_dotenv()


class CDISCCodelistRetriever:
    """Class for retrieving CDISC controlled terminology codelists."""
    
    VALID_STANDARDS = ["SDTM", "ADAM", "CDASH", "DEFINE-XML", "SEND", "DDF", 
                       "GLOSSARY", "MRCT", "PROTOCOL", "QRS", "QS-FT", "TMF"]
    
    # Map standard names to their latest versions (hardcoded as fallback)
    DEFAULT_VERSIONS = {
        "SDTM": "2024-09-27",
        "ADAM": "2024-09-27",
        "CDASH": "2023-12-15",
        "SEND": "2024-09-27"
    }
    
    def __init__(self, api_key=None):
        """Initialize the retriever with an API key."""
        # Try to get API key from environment variable if not provided
        self.api_key = api_key or os.environ.get('CDISC_API_KEY')
        if not self.api_key:
            raise ValueError("CDISC API key is required. Provide it as a parameter or set CDISC_API_KEY in your .env file.")
        
        self.headers = {
            "api-key": self.api_key,
            "Accept": "application/json"
        }
    
    def validate_input(self, codelist_value, standard):
        """Validate input parameters."""
        if not codelist_value:
            raise ValueError("You must specify a codelist_value (e.g., AGEU for SDTM or DTYPE for ADaM)")
        
        if standard.upper() not in self.VALID_STANDARDS:
            valid_standards_str = ", ".join(self.VALID_STANDARDS)
            raise ValueError(f"Invalid standard '{standard}'. Supported values are: {valid_standards_str}")
    
    def get_latest_version(self, standard):
        """
        Get the latest version for a standard.
        Uses hardcoded versions as a fallback if API call fails.
        """
        standard_upper = standard.upper()
        
        # Use hardcoded version as a fallback
        if standard_upper in self.DEFAULT_VERSIONS:
            default_version = self.DEFAULT_VERSIONS[standard_upper]
            return default_version
            
        # If we don't have a hardcoded version, try to get from API
        print(f"No default version available for {standard}, attempting API request...")
        
        try:
            response = requests.get(
                "https://api.library.cdisc.org/api/mdr/products/Terminology",
                headers=self.headers
            )
            
            if response.status_code != 200:
                raise Exception(f"Failed to fetch versions: {response.status_code} - {response.text}")
            
            data = response.json()
            
            # Extract available versions for the specified standard
            versions = []
            standard_prefix = standard.lower() + "ct"
            
            for link in data.get("_links", {}).get("packages", []):
                href = link.get("href", "")
                
                # Extract package name from href
                if "/" in href:
                    package_name = href.split("/")[-1]
                    
                    # Check if this package is for our standard
                    if package_name.startswith(standard_prefix + "-"):
                        # Extract version date
                        version_date = package_name[len(standard_prefix) + 1:]
                        versions.append(version_date)
            
            if versions:
                # Sort to get the latest version
                latest_version = sorted(versions, reverse=True)[0]
                print(f"Latest {standard} CT version is {latest_version}")
                return latest_version
                
        except Exception as e:
            print(f"Error getting version from API: {str(e)}")
            print("Using hardcoded fallback version.")
        
        # If we reach here, we couldn't get a version
        raise ValueError(f"Could not determine version for standard: {standard}")
    
    def get_codelist(self, codelist_value, codelist_type="ID", standard="SDTM", version=None):
        """
        Retrieve a specific CDISC Controlled Terminology codelist.
        
        Parameters:
        -----------
        codelist_value : str
            The codelist name (e.g., AGEU, PARAMCD)
        codelist_type : str, optional (default: 'ID')
            Match by 'ID' or 'CodelistCode'
        standard : str, optional (default: 'SDTM')
            The CDISC standard (e.g., SDTM, ADaM)
        version : str, optional
            Version of Controlled Terminology (empty to pull latest)
            
        Returns:
        --------
        list
            List of dictionaries containing the codelist terms
        """
        # Validate input
        self.validate_input(codelist_value, standard)
        
        # Convert standard to API format
        api_standard = f"{standard.lower()}ct"
        
        # Get latest version if not provided
        if not version:
            version = self.get_latest_version(standard)
        
        # Fetch CDISC CT package
        print(f"\nFetching {standard} CT version {version}...")
        
        url = f"https://api.library.cdisc.org/api/mdr/ct/packages/{api_standard}-{version}"
        
        try:
            response = requests.get(url, headers=self.headers)
            
            if response.status_code != 200:
                raise Exception(f"Failed to fetch codelist: {response.status_code} - {response.text}")
            
            data = response.json()
            
            # Find the requested codelist
            target_codelist = None
            
            for codelist in data.get("codelists", []):
                cl_id = codelist.get("submissionValue", "")
                cl_code = codelist.get("conceptId", "")
                
                if ((codelist_type.upper() == "ID" and cl_id.upper() == codelist_value.upper()) or 
                    (codelist_type.upper() == "CODELISTCODE" and cl_code.upper() == codelist_value.upper())):
                    target_codelist = codelist
                    break
            
            if not target_codelist:
                print(f"\nWARNING: The provided Codelist Value '{codelist_value}' does not exist in the {standard} Controlled Terminology version {version}.")
                print(f"Please check if your ID is correct or if it exists in the {standard} Codelists.")
                return None
            
            # Process the target codelist
            cl_name = target_codelist.get("name", "")
            extensible = "Yes" if target_codelist.get("extensible", "false") == "true" else "No"
            cl_id = target_codelist.get("submissionValue", "")
            cl_code = target_codelist.get("conceptId", "")
            
            # Format the terms
            terms = []
            for term in target_codelist.get("terms", []):
                terms.append({
                    "ID": cl_id,
                    "CodelistCode": cl_code, 
                    "name": cl_name,
                    "ExtensibleYN": extensible,
                    "TermCode": term.get("conceptId", ""),
                    "TERM": term.get("submissionValue", ""),
                    "TermDecodedValue": term.get("preferredTerm", "")
                })
            
            # Sort terms by submission value
            terms.sort(key=lambda x: x["TERM"])
            
            print(f"\nSubmission Values for {codelist_type}='{codelist_value}' ({standard} CT Version={version}, Extensible={extensible})")
            
            return terms
            
        except Exception as e:
            print(f"ERROR: {str(e)}")
            return None


def display_terms(terms, limit=None):
    """Display terms in a formatted table."""
    if not terms:
        return
    
    # Print header
    print("\n{:<20} {:<40}".format("TERM", "Decoded Value"))
    print("-" * 62)
    
    # Print rows
    for i, term in enumerate(terms):
        if limit is not None and i >= limit:
            print(f"\n... (showing {limit} of {len(terms)} results)")
            break
        print("{:<20} {:<40}".format(term["TERM"], term["TermDecodedValue"]))


def write_to_csv(terms, output_file):
    """Write terms to a CSV file."""
    if not terms:
        return
    
    with open(output_file, 'w', newline='') as csvfile:
        # Get all unique keys from the terms
        fieldnames = set()
        for term in terms:
            fieldnames.update(term.keys())
        
        fieldnames = sorted(list(fieldnames))
        
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for term in terms:
            writer.writerow(term)
    
    print(f"\nResults saved to {output_file}")


def main():
    """Main function to run from command line."""
    parser = argparse.ArgumentParser(description='Retrieve CDISC Controlled Terminology codelists')
    parser.add_argument('--codelist_value', required=True, help='The codelist name (e.g., AGEU, PARAMCD)')
    parser.add_argument('--codelist_type', default='ID', choices=['ID', 'CODELISTCODE'], 
                        help='Match by ID or CodelistCode')
    parser.add_argument('--standard', default='SDTM', help='CDISC standard (e.g., SDTM, ADaM)')
    parser.add_argument('--version', default=None, help='Version of Controlled Terminology (empty to pull latest)')
    parser.add_argument('--api_key', help='CDISC API key (or set CDISC_API_KEY environment variable)')
    parser.add_argument('--output', help='Output CSV file path')
    parser.add_argument('--limit', type=int, default=None, help='Limit number of displayed terms (displays all if not specified)')
    parser.add_argument('--no-clear', action='store_true', help='Do not clear the console before output')
    
    args = parser.parse_args()
    
    try:
        # Clear the console completely before starting (unless --no-clear is specified)
        if not args.no_clear:
            # Print newlines instead of using cls/clear to avoid display issues
            print("\n" * 50)
            
        # Show script header
        print("CDISC Codelist Retrieval Tool - Python Implementation")
        print("=====================================================")
        
        retriever = CDISCCodelistRetriever(api_key=args.api_key)
        result = retriever.get_codelist(
            codelist_value=args.codelist_value,
            codelist_type=args.codelist_type,
            standard=args.standard,
            version=args.version
        )
        
        if result:
            # Display results to console
            display_limit = args.limit or len(result)
            display_terms(result, limit=display_limit if display_limit < len(result) else None)
            
            print(f"\nTotal {len(result)} term(s) found for {args.codelist_value}")
            
            # Save to CSV if output path is provided
            if args.output:
                write_to_csv(result, args.output)
                
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"ERROR: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
