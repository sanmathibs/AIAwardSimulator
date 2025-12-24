# AI Award Interpreter

Transform Fair Work Awards into System Configurations automatically using AI.

## Overview

This tool analyzes new or updated Fair Work awards and automatically generates compatible configurations for your existing wage calculation system.

### One-Time Setup (Done Once)

Before processing awards, the system requires these baseline templates to be stored:

1. **📄 Baseline Config Template** (`data/baseline_config.json`)
   - Your existing JSON configuration (e.g., Workpac_Input.json)
   - Defines how rules are currently configured
   - Contains: Shifts, PayComponents, AwardVariation, Allowances, etc.

2. **🐍 Python Script Template** (Reference only)
   - Your existing Python wage calculation script (e.g., WorkpacNonCoal+Clerks_PYscript.py)
   - Used for understanding calculation logic
   - Not directly modified by the tool

3. **📐 Internal Rule Model** (`models/__init__.py` - AwardSpec)
   - Standard format for representing any award
   - Contains: OrdinaryHours, OvertimeRules, PenaltyRates, Allowances, BreakRules, PublicHolidayRules
   - AI extracts new awards into this consistent format

Once these baselines are configured, you can process unlimited awards against them.

---

## Features

- 🔍 **Automatic Award Parsing**: Fetches and parses awards from fwc.gov.au
- 🤖 **AI-Powered Rule Extraction**: Uses GPT-4 to extract wage calculation rules
- 📊 **Gap Analysis**: Identifies config-only vs code-required changes
- 🎯 **Smart Ambiguity Detection**: Flags items needing human clarification
- 📦 **Automatic Config Generation**: Generates updated JSON configurations
- 🔧 **Patch Plan Generation**: Suggests Python code modifications
- 💰 **Cost Tracking**: Monitors OpenAI API costs per session

## Installation

1. **Clone or download this project**

2. **Install dependencies**:
   ```bash
   cd ai_award_interpreter
   pip install -r requirements.txt
   ```

3. **Create `.env` file** in the `ai_award_interpreter` directory:
   ```env
   api_key=your_openai_api_key_here
   ```

4. **Copy baseline configuration**:
   Copy your existing `Workpac_Input.json` to `data/baseline_config.json`:
   ```bash
   cp ../Workpac_Input.json data/baseline_config.json
   ```

## Usage

1. **Start the app**:
   ```bash
   streamlit run app.py
   ```

2. **Open in browser**: http://localhost:8501

3. **Process an award**:
   - Enter award URL (e.g., `https://awards.fairwork.gov.au/MA000028.html`)
   - Click "Start Analysis"
   - Wait for processing (2-5 minutes)
   - Resolve any ambiguities
   - Review outputs
   - Download updated JSON config

## Example Awards

- **Horticulture Award**: https://awards.fairwork.gov.au/MA000028.html
- **Clerks Award**: https://awards.fairwork.gov.au/MA000002.html
- **Mining Award**: https://awards.fairwork.gov.au/MA000027.html

## Cost Estimates

- Typical award: $0.40 - $0.65 per run
- Monthly budget: $100 (150-250 awards)
- Cost tracking displayed in UI

## Output Files

Each session generates:

1. **updated_config.json**: New JSON configuration
2. **patch_plan.md**: Python modification suggestions
3. **gap_report.json**: Detailed gap analysis
4. **award_spec.json**: Extracted award specification

All files stored in: `sessions/sess-YYYYMMDD-HHMMSS-XXXXXX/`

## Project Structure

```
ai_award_interpreter/
├── app.py                      # Streamlit UI
├── config.py                   # Configuration
├── requirements.txt            # Dependencies
│
├── core/
│   └── orchestrator.py         # Main workflow
│
├── ingestion/
│   ├── award_fetcher.py        # Fetch from Fair Work
│   ├── html_parser.py          # Parse HTML
│   ├── clause_chunker.py       # Chunk clauses
│   └── vector_store.py         # ChromaDB interface
│
├── extraction/
│   └── rule_extractor.py       # LLM rule extraction
│
├── analysis/
│   └── gap_analyzer.py         # Gap analysis
│
├── generation/
│   ├── json_generator.py       # JSON config generation
│   └── patch_generator.py      # Patch plan generation
│
├── models/
│   └── __init__.py             # Data models
│
├── utils/
│   ├── openai_client.py        # OpenAI wrapper
│   └── prompt_templates.py     # LLM prompts
│
├── data/
│   └── baseline_config.json    # Your current config
│
└── sessions/                   # Session outputs
```

## Troubleshooting

### Error: "api_key not found in environment variables"
- Ensure `.env` file exists in `ai_award_interpreter` directory
- Check that `.env` contains: `api_key=sk-...`

### Error: "Failed to fetch award"
- Check internet connection
- Verify award URL is correct and accessible
- Try a different award URL

### High costs
- Each award costs $0.40-$0.65
- Cost is tracked and displayed in UI
- Budget limit set to $100/month in config

### Extraction errors
- Some awards may have non-standard HTML structure
- Check `sessions/*/clauses.json` to verify parsing
- Report issues with specific award URLs

## Future Enhancements

- [ ] Version tracking (compare award versions)
- [ ] Edit extracted rules before applying
- [ ] Automated testing generation
- [ ] Batch processing
- [ ] PDF award support
- [ ] Code auto-patching (risky!)

## Support

For issues or questions, refer to the design document: `AI_AWARD_INTERPRETER_DESIGN.md`

## License

Internal development tool - not for redistribution.
