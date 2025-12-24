# 🚀 AI Award Interpreter - Quick Start Guide

## Step-by-Step Setup

### 1. Navigate to the app directory
```powershell
cd d:\TestingSpace\award\ai_award_interpreter
```

### 2. Install dependencies
```powershell
pip install -r requirements.txt
```

### 3. Create your .env file
```powershell
# Copy the example
Copy-Item .env.example .env

# Then edit .env and add your OpenAI API key
# api_key=sk-your-actual-key-here
```

### 4. Run the app
```powershell
streamlit run app.py
```

### 5. Open in browser
The app will automatically open at: **http://localhost:8501**

---

## First Award to Try

**Horticulture Award 2020**
```
https://awards.fairwork.gov.au/MA000028.html
```

1. Paste the URL into the input field
2. Click "Start Analysis"
3. Wait 2-5 minutes for processing
4. Review results
5. Download outputs

---

## What You'll Get

After processing, you'll receive:

1. **📄 Updated JSON Config** - Ready to use with your Python script
2. **🔧 Patch Plan** - High-level guidance for Python changes
3. **📊 Gap Report** - Detailed analysis of differences
4. **📚 Award Spec** - Structured award specification

---

## Expected Costs

- **Per Award**: $0.40 - $0.65
- **Monthly Budget**: $100 (150-250 awards)
- Cost is tracked and displayed in the UI

---

## Troubleshooting

### Issue: "api_key not found"
**Solution**: Create `.env` file with your OpenAI API key

### Issue: "Module not found"
**Solution**: Run `pip install -r requirements.txt`

### Issue: "Award fetch failed"
**Solution**: Check internet connection and try a different award URL

---

## Next Steps

1. Process the Horticulture Award (provided above)
2. Review the generated outputs
3. Try with your specific award
4. Compare outputs with your current configuration
5. Apply changes to your system

---

## Support

- **Design Doc**: See `AI_AWARD_INTERPRETER_DESIGN.md`
- **README**: See `README.md` for full documentation
- **Issues**: Check the troubleshooting section above

---

**Built with**: Streamlit + GPT-4 + ChromaDB  
**Version**: 1.0 (Phase 1 Complete)
