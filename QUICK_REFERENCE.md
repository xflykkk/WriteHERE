# WriteHERE LLM Calling Patterns - Quick Reference

## At a Glance

### LLM Call Counts
- **Story (4K words)**: 15-20 calls
- **Report (8K words)**: 130-160 calls

### Token Consumption
- **Story**: 65K tokens total (~$0.40 with GPT-4o)
- **Report**: 163K tokens total (~$1.80 with GPT-4o)

### Recursion Depth
- **Story**: 3-4 levels (natural termination)
- **Report**: 3 levels (force_atom_layer=3)
- **Global**: Max 10,000 steps, practical limit 3,000

---

## LLM Calls by Task Type

| Task Type | Calls | Input Tokens | Output Tokens | Model Temp |
|-----------|-------|--------------|---------------|-----------|
| COMPOSITION (Write) | 1-2 | 3-8K | 500-2K | 0.3 |
| REASONING (Think) | 1-2 | 3-8K | 300-1K | 0.3 |
| RETRIEVAL (Search) | 20-30 | 100K+ | 5K | mini |
| PLANNING (Plan) | 1-2 | 1.5-3K | 100-500 | 0.1 |

---

## Two-Phase Planning Mechanism

### Phase 1: Atom Judgment (1 LLM call)
- Question: Can this task be further decomposed?
- Output: "atomic" or "complex"
- Retries: Up to 10

### Phase 2: Recursive Planning (conditional, 1 LLM call)
- Only if Phase 1 returns "complex"
- Output: JSON DAG with sub_tasks
- Retries: Up to 10

---

## Task Decomposition Example

```
Root Task (8,000 words)
├── Level 1: 3 tasks
│   ├── Search task
│   ├── Think task
│   └── Write task (8,000 words)
│       ├── Level 2: ~15 tasks (5 per parent)
│       │   └── Level 3: ~75 tasks (forced atomic)
```

**Result**: ~100 tasks total for one report section

---

## Token Estimation

### Prompt Component Sizes

**Fixed (~1-3K tokens)**:
- System message: 500-2,000
- Task instruction: 200-500
- Output format: 300-800

**Variable (~2-11K tokens)**:
- Task goal: 20-200
- Previous content: 500-5,000
- Plan context: 500-2,000
- Dependencies: 500-3,000
- Candidate plan: 200-1,000

**Total Range**:
- Minimal: 1.5-3K tokens
- Medium: 3-8K tokens
- Large: 8-20K tokens

---

## Cost Breakdown

### Pricing (per 1M tokens)

| Model | Input | Output |
|-------|-------|--------|
| GPT-4o | $2.50 | $10.00 |
| GPT-4o-mini | $0.15 | $0.60 |
| Claude | $3.00 | $15.00 |
| o1 | $0.55 | $2.19 |
| Gemini | $0.25 | $0.75 |

### Cost Per 1,000 Words

- **Story**: $0.10/1K (GPT-4o)
- **Report**: $0.23/1K (GPT-4o)
- **Report** (mini): $0.02/1K (GPT-4o-mini)

---

## Configuration Files

### Model Config
**Location**: `recursive/model_config.yaml`

**Quick Setup**:
```bash
# Use preset (economy is 30x cheaper)
python engine.py --preset economy --mode report
```

**Available Presets**:
- `premium`: Claude 3.7 + GPT-4o
- `balanced`: GPT-4o for all
- `economy`: GPT-4o-mini for all (90% cost reduction)
- `gemini`: Gemini models
- `claude`: Claude models

---

## Logging and Metrics

### Token Tracking
- Location: `recursive/llm/llm.py` (lines 356-386)
- Logged at: DEBUG level
- Output: `engine.log` in project folder

### Output Files
- `engine.log`: Execution trace
- `nodes.json`: Task graph structure
- `memory.jsonl`: Article + search results
- `report.md`: Final report

### Cache
- LLM cache: `llm.Cache()`
- Search cache: `search.Cache()`
- Web page cache: `web_page.Cache()`

---

## Recursion Limits

### Story Mode
- No hardcoded limit
- Natural termination at atomic tasks
- Typical: 3-4 levels

### Report Mode
- `force_atom_layer: 3` (line 454, engine.py)
- All tasks at layer >= 3 forced atomic
- Prevents excessive recursion

### Global
- Max steps: 10,000 iterations
- Practical limit: 3,000 steps
- Abort condition: `if step > 3000`

---

## Key Implementation Files

| Component | Location | Key Lines |
|-----------|----------|-----------|
| LLM Proxy | `recursive/llm/llm.py` | 66-401 |
| Token Tracking | `recursive/llm/llm.py` | 356-386 |
| Execution Engine | `recursive/engine.py` | 24-166 |
| Planning Agent | `recursive/agent/agents/regular.py` | 135-256 |
| Graph Execution | `recursive/graph.py` | 129-656 |
| Task Decomposition | `recursive/agent/agents/regular.py` | 24-122 |

---

## Optimization Tips

### To Reduce Token Costs (30-40% savings)
1. Use GPT-4o-mini for planning tasks
2. Truncate old dependency results
3. Sample context paragraphs (keep first + last)
4. Use economy preset

### To Reduce LLM Calls (20% savings)
1. Stop planning if well-formed (no retries)
2. Terminate search after 2 turns
3. Cache planning results across tasks

### To Improve Speed
1. Already parallelizes search (8 workers)
2. Could parallelize writing of independent tasks

---

## Heterogeneous Task Types

### Three Core Types

1. **COMPOSITION ("write")**
   - Actual content generation
   - 1 LLM call per atomic task
   - Output: 500-2,000 tokens

2. **REASONING ("think")**
   - Analysis and planning
   - 1 LLM call per task
   - Output: 300-1,000 tokens

3. **RETRIEVAL ("search")**
   - Information gathering (report mode)
   - 20-30 calls per task (including selector + summarizer)
   - Output: 5,000+ tokens

---

## Context Passed to Tasks

All tasks receive these prompt parameters:

```
✓ to_run_root_question      # Original goal
✓ to_run_article            # Previously written content
✓ to_run_full_plan          # Task hierarchy
✓ to_run_outer_graph_dependent    # Parent dependencies
✓ to_run_same_graph_dependent     # Peer dependencies
✓ to_run_candidate_plan     # Reference planning
✓ to_run_candidate_think    # Design conclusions
✓ to_run_target_write_tasks # Related write tasks
✓ to_run_global_writing_task      # Full context
✓ today_date                # Current date
```

---

## Statistics Per 1,000 Words

### Story
- Calls: 3-5
- Tokens: 16,250
- Cost: $0.10

### Report
- Calls: 16-20
- Tokens: 20,375
- Cost: $0.23

---

## Maximum Retry Counts

| Component | Max Retries |
|-----------|-------------|
| Atom judgment | 10 |
| Planning | 10 |
| Execution | 50 |
| Search API | 5 |

---

## Temperature Settings

| Task | Temperature | Purpose |
|------|-------------|---------|
| Composition | 0.3 | Balanced creativity |
| Reasoning | 0.3 | Balanced analysis |
| Planning | 0.1 | Low variance, consistency |
| o1 models | 1.0 | Fixed (no control) |

---

## Reporting and Analysis

### Generated Documents
1. **LLM_CALLING_PATTERNS_ANALYSIS.md** (589 lines)
   - Comprehensive technical analysis
   - Implementation details
   - Code references

2. **LLM_ANALYSIS_SUMMARY.txt** (400+ lines)
   - Executive summary
   - Key findings
   - Recommendations

3. **QUICK_REFERENCE.md** (this file)
   - Quick lookup
   - Key statistics
   - Configuration guide

---

## Common Tasks

### View Full Analysis
```bash
cat LLM_CALLING_PATTERNS_ANALYSIS.md
```

### Check Token Tracking
```bash
grep "Usage:" engine.log
```

### Check Task Graph
```bash
cat nodes.json | jq '.topological_task_queue | length'
```

### Estimate Cost Before Run
```
Formula: (input_tokens + output_tokens) * model_price / 1,000,000
Example: (135,000 + 28,000) * ($2.50/1M + $10/1M) = ~$1.80
```

---

## Summary

- **Story writing uses 15-20 LLM calls** with planning and design phases
- **Report writing uses 130-160 LLM calls** dominated by search (100+)
- **Two-phase planning**: Atom judgment → Decomposition
- **Recursion depth**: 3-4 levels for story, 3 forced for report
- **Token consumption**: 65K-163K per document
- **All tokens and costs are tracked** in real-time logs

---

For detailed analysis, see: `LLM_CALLING_PATTERNS_ANALYSIS.md`
