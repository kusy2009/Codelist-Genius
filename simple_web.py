#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CDISC AI Assistant - Minimal Web Interface
A very simple web interface that directly calls the command-line script
"""

import os
import subprocess
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/query', methods=['POST'])
def process_query():
    """Process a query by calling the command-line script"""
    data = request.json
    query = data.get('query', '')
    
    if not query:
        return jsonify({'response': 'Please provide a query about CDISC codelists.'})
    
    try:
        # Use subprocess to run the command-line script
        # This is the most reliable approach as we know the command-line script works
        cmd = ['python', 'cdisc_ai_assistant.py', '--query', query]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        # Return the stdout as the response
        return jsonify({'response': result.stdout})
    except Exception as e:
        return jsonify({'response': f'Error: {str(e)}'})

if __name__ == '__main__':
    # Run on port 5001 to avoid conflict with any existing server
    app.run(host='0.0.0.0', port=5001, debug=True)
