# CDISC AI Assistant

An AI-powered tool for retrieving and interpreting CDISC controlled terminology codelists through natural language queries.

![CDISC AI Assistant Web UI](https://i.imgur.com/placeholder.png)

## Overview

The CDISC AI Assistant combines the power of a CDISC controlled terminology retrieval tool with advanced AI capabilities to:

1. Retrieve standardized CDISC codelists across multiple standards (SDTM, ADaM, CDASH, SEND)
2. Interpret natural language queries about codelists
3. Provide enhanced responses about codelist extensibility and valid term membership
4. Present results through both a command-line interface and a web UI

This tool is designed to simplify access to CDISC controlled terminology for clinical data professionals, allowing them to quickly find and understand standardized terms.

## Features

- **Natural Language Query Processing**: Ask questions in plain English about CDISC codelists
- **Multi-Standard Support**: Access terminology from SDTM, ADaM, CDASH, and SEND
- **Advanced AI Interpretation**: Get specific answers about:
  - Codelist extensibility (Can I add my own terms?)
  - Term membership (Is X a valid term in this codelist?)
  - Comprehensive codelist information
- **Dual Interface**: Use via command-line or web browser
- **OpenRouter Integration**: Leverages the Mistral AI model for natural language understanding

## Installation

### Prerequisites

- Python 3.6 or higher
- An OpenRouter API key (for AI capabilities)

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/cdisc-ai-assistant.git
cd cdisc-ai-assistant
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Configure API Key

Create a `.env` file in the project root directory with your OpenRouter API key:

```
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

You can obtain an API key by signing up at [OpenRouter](https://openrouter.ai/).

## Usage

### Command-Line Interface

The command-line interface allows you to quickly query CDISC codelists:

```bash
python cdisc_ai_assistant.py --query "Is DECADE a valid term in the AGEU codelist?"
```

You can also run in interactive mode:

```bash
python cdisc_ai_assistant.py
```

### Web Interface

To start the web interface:

```bash
python simple_web.py
```

Then open a browser and navigate to:
```
http://localhost:5001
```

## Example Queries

Here are some examples of questions you can ask:

- "Show me the SEX codelist"
- "What are the valid terms in the AGEU codelist?"
- "Is the RACE codelist extensible?"
- "Is OTHER a valid term in the SEX codelist?"
- "Get DTYPE from ADaM standard"

## How It Works

The CDISC AI Assistant consists of three main components:

1. **CDISC Codelist Retrieval Tool** (`cdisc_codelist.py`): A Python implementation of a tool for retrieving CDISC controlled terminology, similar to the SAS macro GetCDISCCodelist

2. **AI Assistant** (`cdisc_ai_assistant.py`): Uses OpenRouter's Mistral AI model to:
   - Extract parameters from natural language queries
   - Run the codelist retrieval tool
   - Analyze the results to provide enhanced responses

3. **Web Interface** (`simple_web.py`): A Flask web application that provides a user-friendly chat interface

## Understanding the Responses

The AI assistant will provide:

1. A direct answer to specific questions (e.g., "Yes, 'OTHER' is a valid term in the RACE codelist")
2. Additional context for invalid terms:
   - For extensible codelists: "This term is not valid, but the codelist is extensible so you could use it with proper documentation"
   - For non-extensible codelists: "This term is not valid, and the codelist is not extensible. You must use one of these values: X, Y, Z"
3. The complete codelist output for reference

## Project Structure

```
cdisc-ai-assistant/
├── cdisc_codelist.py        # Core CDISC codelist retrieval tool
├── cdisc_ai_assistant.py    # AI-enhanced interface to the tool
├── simple_web.py            # Web UI implementation
├── templates/               # HTML templates for web UI
│   └── index.html           # Main chat interface
├── .env                     # Environment variables (API key)
├── requirements.txt         # Python dependencies
└── README.md                # This documentation
```

## FAQ

### Q: Do I need an API key?
A: Yes, the AI capabilities require an OpenRouter API key. The base codelist retrieval functionality will work without it, but you'll lose the natural language processing features.

### Q: What CDISC standards are supported?
A: The tool supports SDTM, ADaM, CDASH, and SEND standards.

### Q: How do I add support for new CDISC versions?
A: Update the `DEFAULT_VERSIONS` dictionary in `cdisc_codelist.py` with the new version dates.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- CDISC for providing standardized controlled terminology for clinical research
- OpenRouter for API access to powerful language models

---

Created with ❤️ for the clinical data standards community
