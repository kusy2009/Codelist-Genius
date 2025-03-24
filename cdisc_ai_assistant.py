#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CDISC AI Assistant

An AI-powered assistant for retrieving CDISC Controlled Terminology codelists
using natural language queries.
"""

import os
import sys
import json
import requests
import subprocess
import argparse
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class CDISCAIAssistant:
    """AI-powered assistant for CDISC codelist retrieval."""
    
    def __init__(self, api_key=None):
        """Initialize the assistant with an API key."""
        # Try to get API key from environment variable if not provided
        self.api_key = api_key or os.environ.get('OPENROUTER_API_KEY')
        if not self.api_key:
            raise ValueError("OpenRouter API key is required. Provide it as a parameter or set OPENROUTER_API_KEY in your .env file.")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://localhost", # Your site URL
            "X-Title": "CDISC AI Assistant"      # Your app name
        }
        
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "mistralai/mistral-small-3.1-24b-instruct:free"
        
    def extract_parameters(self, query):
        """
        Extract parameters from the user's query using an LLM.
        
        Parameters:
        -----------
        query : str
            The user's query
            
        Returns:
        --------
        dict
            A dictionary of extracted parameters
        """
        # List of common codelist names to help with extraction
        common_codelists = ["AGEU", "SEX", "RACE", "ETHNIC", "COUNTRY", "VISIT", "DOMAIN", 
                           "ARM", "ARMCD", "DTYPE", "PARAMCD", "PARAMTYP", "UNIT"]
        
        # Check for direct mentions of codelists in the query
        for codelist in common_codelists:
            if codelist in query.upper():
                return {
                    "codelist_value": codelist,
                    "standard": "SDTM"  # Default to SDTM
                }
        
        # Prepare the system prompt
        system_prompt = """You are an assistant that extracts parameters from user queries about CDISC controlled terminology codelists.
Extract the following parameters if present in the query:
- codelist_value: The codelist ID (e.g., AGEU, SEX, RACE, ETHNIC, COUNTRY)
- standard: The CDISC standard (SDTM, ADaM, CDASH, SEND)

Format your response as a JSON object with these parameters."""

        # Prepare the user query
        user_prompt = f"Extract parameters from this query: {query}"
        
        try:
            # Make the request to the LLM API
            response = self._call_llm_api(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.1,  # Low temperature for more deterministic output
            )
            
            # Try to parse the response as JSON
            import json
            import re
            
            # Look for JSON-like content
            json_pattern = r'\{.*\}'
            json_match = re.search(json_pattern, response, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(0)
                extracted_params = json.loads(json_str)
                
                # Apply default values
                if "standard" not in extracted_params and "codelist_value" in extracted_params:
                    extracted_params["standard"] = "SDTM"
                
                # Print the extracted parameters
                print("\nExtracted parameters:")
                for key, value in extracted_params.items():
                    print(f"  {key}: {value}")
                
                return extracted_params
            else:
                # Fallback for when JSON parsing fails
                params = {}
                
                # Manually extract parameters
                if "ageu" in query.lower():
                    params["codelist_value"] = "AGEU"
                elif "sex" in query.lower():
                    params["codelist_value"] = "SEX"
                elif "race" in query.lower():
                    params["codelist_value"] = "RACE"
                elif "ethnic" in query.lower():
                    params["codelist_value"] = "ETHNIC"

                # Default standard
                if "standard" not in params and "codelist_value" in params:
                    params["standard"] = "SDTM"
                
                # Print the extracted parameters
                if params:
                    print("\nExtracted parameters (fallback method):")
                    for key, value in params.items():
                        print(f"  {key}: {value}")
                
                return params
        except Exception as e:
            print(f"Error extracting parameters: {str(e)}")
            return {}
    
    def analyze_query_type(self, query, output):
        """
        Analyze query to determine if it's asking about extensibility or value membership.
        
        Parameters:
        -----------
        query : str
            The original query
        output : str
            The raw output from the codelist tool
            
        Returns:
        --------
        str
            AI-generated answer to specific questions, or None if no specific question detected
        """
        query_lower = query.lower()
        
        # Check if asking about extensibility
        if "extensible" in query_lower or "extend" in query_lower:
            # Extract extensibility info from output
            extensible_info = None
            for line in output.split('\n'):
                if "Extensible=" in line:
                    extensible_info = "Yes" if "Extensible=Yes" in line else "No"
                    break
            
            if extensible_info:
                codelist = None
                for line in output.split('\n'):
                    if "ID='" in line and "'" in line.split("ID='")[1]:
                        codelist = line.split("ID='")[1].split("'")[0]
                        break
                
                if codelist:
                    return f"The {codelist} codelist is {'extensible' if extensible_info == 'Yes' else 'not extensible'}.\n"
        
        # Check if asking about value membership
        value_keywords = ["valid", "part of", "in", "included", "member", "accepted", "allowed"]
        if any(keyword in query_lower for keyword in value_keywords):
            # Extract all capitalized words that might be potential terms
            potential_values = []
            
            # Extract the codelist ID first to avoid confusion
            codelist = None
            for line in output.split('\n'):
                if "ID='" in line and "'" in line.split("ID='")[1]:
                    codelist = line.split("ID='")[1].split("'")[0]
                    break
            
            # First check for specific words we're looking for in the query
            custom_terms = ["century", "decade", "millisecond", "microsecond", "gay", "other"]
            for term in custom_terms:
                if term in query_lower:
                    potential_values.append(term.upper())
            
            # Then check for all uppercase words (excluding the codelist name itself)
            for word in query.split():
                if word.isupper() and len(word) > 1 and word not in ["SDTM", "ADAM", "CDASH", "SEND"] and word != codelist:
                    potential_values.append(word)
            
            # If not found, look for words that might be potential values
            if not potential_values:
                words = query_lower.split()
                for i, word in enumerate(words):
                    # Words like "is X valid" or "is X a valid"
                    if word == "is" and i < len(words) - 2:
                        # Get next word and capitalize it as a potential term
                        next_word = words[i+1]
                        if next_word not in ["the", "a", "an", "there", "it"] and next_word != codelist.lower():
                            potential_values.append(next_word.upper())
                    
                    # Look for specific terms mentioned
                    if word in ["term", "value", "code"] and i > 0:
                        prev_word = words[i-1]
                        if prev_word not in ["the", "a", "an", "valid", "accepted"] and prev_word != codelist.lower():
                            potential_values.append(prev_word.upper())
            
            # If we have potential values, check if they exist in the output
            if potential_values:
                # Get distinct potential values
                potential_values = list(set(potential_values))
                
                # Extract extensibility info
                is_extensible = False
                for line in output.split('\n'):
                    if "Extensible=" in line:
                        is_extensible = "Extensible=Yes" in line
                        break
                
                # Get all terms from the output
                terms = []
                term_section_found = False
                for line in output.split('\n'):
                    if "TERM" in line and "Decoded Value" in line:
                        term_section_found = True
                        continue
                    if term_section_found and "------" in line:
                        continue
                    if term_section_found and line.strip() and not "Total" in line:
                        term_parts = line.strip().split()
                        if term_parts:
                            terms.append(term_parts[0])
                
                # Check each potential value against the terms list
                for value in potential_values:
                    if any(value in term for term in terms):
                        return f"Yes, '{value}' is a valid term in the {codelist} codelist.\n"
                    else:
                        if is_extensible:
                            return f"No, '{value}' is NOT a valid term in the {codelist} codelist. However, this codelist is extensible, so you could potentially use custom values with proper documentation. Valid terms currently include: {', '.join(terms)}.\n"
                        else:
                            return f"No, '{value}' is NOT a valid term in the {codelist} codelist, and this codelist is not extensible. You must choose one of the accepted values: {', '.join(terms)}.\n"
        
        # No specific question detected
        return None
    
    def run_codelist_tool(self, parameters):
        """
        Run the CDISC codelist tool with the extracted parameters.
        
        Parameters:
        -----------
        parameters : dict
            Dictionary containing parameters for the codelist tool
            
        Returns:
        --------
        str
            Output from the codelist tool
        """
        if not parameters.get("codelist_value"):
            return "Error: No codelist value was extracted from your query."
        
        # Build command line arguments
        cmd = ["python", "cdisc_codelist.py"]
        
        for key, value in parameters.items():
            if value is not None:
                cmd.append(f"--{key}")
                cmd.append(value)
        
        # Add no-clear option to preserve output
        cmd.append("--no-clear")
        
        print(f"\nRetrieving codelist information...")
        
        try:
            # Run the codelist tool and capture output
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            return f"Error running codelist tool: {e.stderr}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def process_query(self, query):
        """
        Process a natural language query end-to-end.
        
        Parameters:
        -----------
        query : str
            The natural language query about CDISC codelists
            
        Returns:
        --------
        str
            Raw output from the codelist tool with AI answer for specific questions
        """
        # Extract parameters from query
        parameters = self.extract_parameters(query)
        
        # If we have a valid codelist value, run the tool
        if parameters.get("codelist_value"):
            # Print the extracted parameters
            print("\nExtracted parameters:")
            for key, value in parameters.items():
                print(f"  {key}: {value}")
                
            # Run the codelist tool
            output = self.run_codelist_tool(parameters)
            
            # Check if there's a specific question to answer
            specific_answer = self.analyze_query_type(query, output)
            
            # Return specific answer + raw output
            if specific_answer:
                return specific_answer + "\n" + output
            else:
                return output
        else:
            return "I couldn't identify a specific CDISC codelist in your query. Please try again and specify which codelist you're interested in (e.g., AGEU, SEX, RACE, ETHNIC)."


def main():
    """Main function to run the assistant from command line."""
    parser = argparse.ArgumentParser(description='AI-powered CDISC Controlled Terminology assistant')
    parser.add_argument('--query', help='Natural language query about CDISC codelists')
    parser.add_argument('--api_key', help='OpenRouter API key (or set OPENROUTER_API_KEY environment variable)')
    
    args = parser.parse_args()
    
    try:
        assistant = CDISCAIAssistant(api_key=args.api_key)
        
        # If query is provided as argument, process it
        if args.query:
            result = assistant.process_query(args.query)
            print("\n" + result)
            return
        
        # Otherwise, start interactive mode
        print("\nCDISC AI Assistant")
        print("=================")
        print("Ask me about CDISC controlled terminology codelists.")
        print("Type 'exit' or 'quit' to end the session.")
        
        while True:
            print("\n")
            query = input("Your question: ")
            
            if query.lower() in ['exit', 'quit']:
                print("Goodbye!")
                break
                
            if not query.strip():
                continue
                
            result = assistant.process_query(query)
            print("\n" + result)
            
    except KeyboardInterrupt:
        print("\nSession terminated by user")
    except Exception as e:
        print(f"ERROR: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
