# Config Generator Options

The AI Award Interpreter now supports two different approaches for generating JSON configurations from award specifications.

## 1. Rule-Based Generator (Default)
**File:** `generation/json_generator.py`  
**Class:** `ConfigGenerator`

### How It Works
- Uses deterministic Python logic to transform award specifications into JSON configurations
- Directly maps AwardSpec fields to JSON structure using predefined templates
- Fast and predictable

### Advantages
- ⚡ **Fast**: No LLM API calls during config generation
- 💰 **Cost-effective**: Zero additional OpenAI costs
- 🎯 **Deterministic**: Same input always produces same output
- 🐛 **Easy to debug**: Pure Python logic, can step through with debugger
- ✅ **Reliable**: No dependency on LLM availability or quality

### Disadvantages
- 🔒 **Less flexible**: Requires code changes to handle new edge cases
- 📏 **Template-based**: Limited to predefined configuration patterns
- 🤔 **Manual mapping**: Someone needs to understand both award rules and JSON structure

### When to Use
- Production environments where consistency is critical
- Cost-sensitive applications
- Awards that fit well into standard patterns
- When you need fast, reliable results

---

## 2. LLM-Based Generator (Optional)
**File:** `generation/json_generator_llm.py`  
**Class:** `ConfigGeneratorLLM`

### How It Works
- Uses OpenAI's structured outputs with Pydantic models
- Sends award specification and baseline examples to GPT-4
- LLM generates complete JSON configuration following the schema
- Validates output against Pydantic models

### Advantages
- 🧠 **Intelligent**: Can handle complex, unusual award structures
- 🔄 **Adaptive**: May find better mappings than hardcoded rules
- 📝 **Context-aware**: Understands award language and intent
- 🆕 **Flexible**: Can handle new award patterns without code changes
- 🔍 **Self-documenting**: Prompt explains the entire structure

### Disadvantages
- 🐌 **Slower**: Additional LLM API call (~5-10 seconds)
- 💸 **More expensive**: Extra $0.02-0.05 per generation
- 🎲 **Non-deterministic**: May vary slightly between runs
- 🔌 **Requires API**: Depends on OpenAI availability
- 🐛 **Harder to debug**: LLM reasoning is not directly observable

### When to Use
- Complex awards that don't fit standard patterns
- Prototyping or experimentation
- When accuracy is more important than speed
- Awards with unusual rule combinations

---

## How to Switch Between Generators

### In Code
```python
from core.orchestrator import Orchestrator

# Use rule-based generator (default)
orchestrator = Orchestrator(use_llm_generator=False)

# Use LLM-based generator
orchestrator = Orchestrator(use_llm_generator=True)
```

### In Streamlit UI
1. Enter award URL
2. Check the "🤖 Use LLM Generator" checkbox to use AI-based generation
3. Leave unchecked for rule-based generation (default)
4. Click "🚀 Start Analysis"

---

## Cost Comparison

### Rule-Based Generator
```
Embedding:     ~$0.01
Extraction:    ~$0.05  (single structured call)
Gap Analysis:  ~$0.03
Generation:    $0.00   (no LLM call)
Patch Plan:    ~$0.02
────────────────────────
Total:         ~$0.11 per award
```

### LLM-Based Generator
```
Embedding:     ~$0.01
Extraction:    ~$0.05  (single structured call)
Gap Analysis:  ~$0.03
Generation:    ~$0.03  (LLM-based)
Patch Plan:    ~$0.02
────────────────────────
Total:         ~$0.14 per award
```

**Difference:** LLM generator adds ~$0.03 (27% increase)

---

## Performance Comparison

### Rule-Based Generator
- Config generation: **Instant** (<100ms)
- Total pipeline: ~10-15 seconds

### LLM-Based Generator
- Config generation: **5-10 seconds** (LLM call)
- Total pipeline: ~15-25 seconds

---

## Recommendations

### Use Rule-Based Generator When:
- ✅ Processing standard awards (most Fair Work awards)
- ✅ Running in production with high volume
- ✅ Cost optimization is important
- ✅ Consistency/auditability is required
- ✅ Fast response time is needed

### Use LLM-Based Generator When:
- ✅ Award has unique/complex structure
- ✅ Rule-based output needs refinement
- ✅ Exploring new award patterns
- ✅ Prototyping or testing
- ✅ Accuracy matters more than speed/cost

### Hybrid Approach
You can also use both:
1. Start with rule-based generator for speed
2. If gaps are detected, re-run with LLM generator
3. Compare outputs and choose the better one

---

## Technical Details

### Pydantic Models (LLM Generator)
The LLM generator uses strict Pydantic schemas:
- `AwardVariationConfig`: Main award settings
- `AwardVariationRate`: Individual rate configurations
- `RateProperty`: Rate property flags
- `ShiftRule`: Shift-specific rules
- `CompleteConfig`: Root configuration object

This ensures:
- Type safety
- Automatic validation
- Structured LLM outputs
- Schema enforcement

### Prompt Engineering
The LLM prompt includes:
- Complete award specification
- Baseline configuration examples
- Detailed generation instructions
- Naming conventions and constraints
- Field-by-field guidance

---

## Future Improvements

### Potential Enhancements:
1. **Hybrid Generator**: Combine rule-based + LLM for best of both
2. **Confidence Scoring**: LLM rates its own output confidence
3. **Validation Layer**: Compare rule-based vs LLM outputs, flag discrepancies
4. **Caching**: Cache LLM generations for identical award specs
5. **Fine-tuned Model**: Train custom model on award→config mappings

---

## Conclusion

Both generators produce valid JSON configurations. Choose based on your priorities:
- **Speed + Cost**: Rule-based (default)
- **Flexibility + Intelligence**: LLM-based (optional)

The system is designed to make switching seamless, so you can experiment and choose what works best for your use case.
