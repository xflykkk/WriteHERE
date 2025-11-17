# WriteHERE LLM Calling Patterns and Token Consumption Analysis

## Executive Summary

WriteHERE is a heterogeneous recursive planning framework for long-form writing that uses LLMs as core components. The system performs dynamic task decomposition and integrates three fundamental task types: **Planning**, **Composition (Writing)**, and **Retrieval/Reasoning** (in report mode). This analysis reveals the LLM call patterns, token consumption metrics, and recursion mechanisms.

---

## 1. LLM Call Architecture

### 1.1 Core LLM Integration

**LLM Provider**: `/home/user/WriteHERE/recursive/llm/llm.py` (OpenAIApiProxy)

The system supports multiple providers:
- OpenAI (GPT-4o, GPT-4o-mini, o1)
- Anthropic (Claude 3.5 Sonnet, Claude 3.7 Sonnet)
- Google Gemini (2.5 Pro, 2.0 Flash)
- OpenRouter (multi-provider access)

**Key Features**:
- Automatic caching of LLM responses
- Token counting and cost estimation
- Retry mechanism with exponential backoff (up to 100 retries)
- Support for multiple model backends in a single run

### 1.2 Token Tracking and Pricing

**Current Implementation** (lines 356-386 in `llm.py`):

```python
input_tokens_key = 'prompt_tokens' if is_gpt else 'input_tokens'
output_tokens_key = 'completion_tokens' if is_gpt else 'output_tokens'

# Pricing per million tokens (as of current config)
Pricing Table:
- GPT-4o: $2.50/1M input, $10.00/1M output
- GPT-4o-mini: $0.150/1M input, $0.600/1M output
- Claude: $3.0/1M input, $15.0/1M output
- o1: $0.55/1M input, $2.19/1M output
- Gemini: $0.25/1M input, $0.75/1M output
```

**Cost Calculation**:
```
price = (input_tokens / 1_000_000) * price_per_1M_input + 
        (output_tokens / 1_000_000) * price_per_1M_output
```

---

## 2. Task Type Classification and LLM Calls

### 2.1 Three Core Task Types

From `recursive/engine.py`, the system uses:

```python
"task_type2tag": {
    "COMPOSITION": "write",      # Writing tasks
    "REASONING": "think",        # Analysis/reasoning tasks
    "RETRIEVAL": "search",       # Search tasks
}
```

### 2.2 LLM Calls Per Task Type

#### **COMPOSITION (Writing) Tasks**
File: `/recursive/agent/agents/regular.py` (SimpleExcutor)

**Planning Phase**: ✗ No LLM call (DummyRandomUpdateAgent)

**Execution Phase**: 1 LLM call per atomic writing task
- **Prompt**: Combines:
  - System message + task goal
  - Previous writing content (`to_run_article`)
  - Task dependencies results
  - Word count requirements
- **Model**: Primary model (GPT-4o, Claude, etc.)
- **Temperature**: 0.3 (higher creativity)
- **Max tokens**: 4096

**Atom Update Phase**: 1 LLM call per composition task (if `update_diff=True`)
- Sends: Previous goals + new dependencies
- Returns: Goal updates
- Temperature: 0.1 (lower variance)

**Final Aggregation**: 1 LLM call (concatenates all subtask results)

**Total per Composition Task**: 1-2 LLM calls (execute + optional update)

#### **REASONING (Analysis) Tasks**
File: `recursive/agent/agents/regular.py` (FinalAggregateAgent)

**Execution Phase**: 1 LLM call per reasoning task
- **Prompt**: Full planning context + task goal
- **Parse output**: Extracts thinking + result
- **Mode**: Direct LLM execution

**Final Aggregation**: 1 LLM call (only if mode="llm", otherwise concatenation)

**Total per Reasoning Task**: 1-2 LLM calls

#### **RETRIEVAL (Search) Tasks** (Report Mode Only)
File: `/recursive/executor/agents/claude_fc_react.py` (SearchAgent)

**Multi-turn Search Agent**:
- **Max turns**: 4 (configured in engine.py)
- **LLM calls per turn**: 1-2
  - 1 for planning search queries
  - 1 for merging results (if llm_merge=True)

**Search Result Selection**:
- **Selector Model**: gpt-4o-mini (separate from main model)
- **LLM calls**: 1 per web page selected (batched in parallel)
- **Workers**: Up to 8 parallel selector workers

**Search Result Summarization**:
- **Summarizer Model**: gpt-4o-mini (separate)
- **LLM calls**: 1 per web page summarized
- **Workers**: Up to 8 parallel summarizer workers

**Total per Retrieval Task**: 4-20+ LLM calls
- 4-8 for search planning (up to 4 turns)
- 5-20 for selecting top search results
- 5-20 for summarizing selected results
- 1 for merging (optional)

---

## 3. Planning and Task Decomposition Mechanism

### 3.1 Multi-Agent Planning System

**Planning Trigger**: `UpdateAtomPlanningAgent.forward()` (lines 136-256)

The system uses a **two-phase planning approach**:

#### **Phase 1: Atom Judgment** (1 LLM call)
```python
atom_llm_result = get_llm_output(node, self, memory, "atom")
```

**Purpose**: Determine if a task is atomic (cannot be decomposed further)

**Prompt Template**: Varies by task type:
- `ReportAtom` / `ReportAtomWithUpdate` (report mode)
- `StoryWritingNLWriteAtomEN` (story mode)

**Output Parsing**:
```python
succ = (atom_llm_result["atom_result"].strip() in ("atomic", "complex"))
```

**Retry Logic**: Up to 10 retries if not in valid format

#### **Phase 2: Recursive Planning** (1 LLM call, conditional)
```python
if atom_llm_result["atom_result"] == "complex":
    plan_llm_result = get_llm_output(node, self, memory, "planning")
```

**Purpose**: Generate sub-task DAG if task is complex

**Prompt Templates**:
- `ReportPlanning` (report mode)
- `StoryWritingNLPlanningEN` (story mode)

**Planning Guidelines** (from prompts):
- **Sub-tasks per level**: 3-5 (guideline), max 8
- **Task types**: write + search + think
- **Dependencies**: DAG structure with explicit dependencies
- **Recursion**: Continue until all tasks are atomic

**Output Format**: JSON with structure:
```json
{
  "id": "1",
  "task_type": "write|think|search",
  "goal": "task description",
  "dependency": ["1", "2"],
  "length": "500-2000 words (write only)",
  "sub_tasks": [...]
}
```

**Retry Logic**: Up to 10 retries for planning if parsing fails

### 3.2 Graph Execution Engine

**Engine**: `GraphRunEngine` (recursive/engine.py)

**Execution Loop**:
```python
for step in range(10000):  # Max 10,000 steps
    if step > 3000:
        logger.error("Step > 3000, break")  # Hard limit
        break
    
    node = find_need_next_step_nodes(single=True)
    if node is None:  # All done
        break
    
    action_name, result = node.next_action_step(memory)
    forward_exam(root_node, verbose)  # Update graph status
```

**Key Metrics**:
- **Max steps**: 10,000 iterations
- **Practical limit**: 3,000 steps (hardcoded abort threshold)
- **Node statuses**: NOT_READY → READY → PLAN_DONE → DOING → FINAL_TO_FINISH → NEED_POST_REFLECT → FINISH

---

## 4. Recursion Depth and Task Decomposition Limits

### 4.1 Recursion Depth Control

**Depth Limits**:

1. **Story Mode**: No explicit hardcoded depth limit
   - System naturally terminates when tasks become atomic
   - Typical depth: 3-4 levels

2. **Report Mode**: 
   - **Force Atom Layer**: `force_atom_layer: 3`
   - **Configuration** (line 454 in engine.py):
     ```python
     "force_atom_layer": 3  # >= 3, force to atom and skip atom judgement
     ```
   - At layer 3+, all tasks are forced to be atomic

### 4.2 Task Decomposition Patterns

**Observed from Examples** (write_planning.py):

**Report Writing Example** (DeepSeek biography):
- Root level: 1 write task
- Level 1: 3 subtasks (search, think, write)
- Level 2: 5-10 subtasks per parent
- Level 3: 2-5 subtasks (atomic tasks)

**Story Writing Example** (Europa suspense story):
- Root level: 1 write task
- Level 1: 4 think tasks (design elements)
- Level 2: 3-5 think subtasks per parent
- Level 3: 1 write task (final composition)

**Maximum Branching**: Observed ~5 subtasks per task at each level

### 4.3 Task Count Estimation

For a typical report writing task:

```
Level 0: 1 task (root)
Level 1: 3 tasks (1 search, 1 think, 1 write)
Level 2: 15 tasks (5 per parent)
Level 3: 75 tasks (5 per parent, forced atomic)

Total: ~94 tasks per major writing topic
```

For a full 8,000-word report with 3-4 major sections:
```
Total tasks: ~250-300 nodes in task graph
```

---

## 5. LLM Call Count Analysis

### 5.1 Story Mode (Fiction Writing)

**Configuration**: No retrieval/search tasks

**Typical Flow for 4,000-word story**:

1. **Initial Planning**: 2 LLM calls
   - 1 for atom judgment on root
   - 1 for planning decomposition

2. **Level 1-2 Planning** (design tasks): 
   - ~4 think tasks × 2 calls each = 8 calls
   - (1 atom + 1 planning per complex task)

3. **Level 2-3 Writing**:
   - ~4-6 write tasks × 1 call each = 4-6 calls
   - (execution only, no atom/planning for atomic tasks)

4. **Post-Reflection**: 
   - 1-2 calls for final aggregation

**Total LLM Calls**: 15-20 calls per 4,000-word story

**Estimated Tokens**:
- Input: ~50,000 tokens (prompts + context)
- Output: ~15,000 tokens (4,000 words of writing + planning)
- **Total**: ~65,000 tokens per story

### 5.2 Report Mode (Technical Writing)

**Configuration**: Includes retrieval, reasoning, and composition

**Typical Flow for 8,000-word report on trending topic**:

1. **Planning Phase** (per section):
   - 2 calls per section = 8 calls (4 sections)

2. **Search Phase** (per retrieval task):
   - ~2 search tasks per section
   - 4 turns × 2 calls per turn = 8 calls per search task
   - **Selector calls**: ~12 pages × 8 workers = batch selections
   - **Summarizer calls**: ~12 pages × 8 workers = batch summaries
   - Per search: ~20-30 calls
   - **Total search**: 4 tasks × 25 calls = 100 calls

3. **Reasoning Phase** (per reasoning task):
   - ~2 reasoning tasks per section
   - 1 call per task = 8 calls

4. **Composition Phase** (per writing task):
   - ~8-10 write tasks
   - 1 call per task = 8-10 calls

5. **Aggregation**: 4-6 calls (per major section)

**Total LLM Calls**: 130-160 calls per 8,000-word report

**Estimated Tokens**:
- **Search phrases**: ~50,000 tokens
- **Reasoning**: ~30,000 tokens
- **Writing**: ~25,000 tokens
- **Planning**: ~30,000 tokens
- **Total input**: ~135,000 tokens
- **Total output**: ~28,000 tokens (8,000 words + metadata)
- **Total**: ~163,000 tokens per report

---

## 6. Caching and Optimization

### 6.1 Cache Architecture

**Supported Caches** (recursive/memory.py):
```python
caches = {
    "search": Cache(),      # Web search results
    "llm": Cache(),         # LLM responses
    "web_page": Cache()     # Downloaded web pages
}
```

**LLM Cache** (llm.py):
```python
if not overwrite_cache:
    cache_result = llm_cache.get_cache(cache_name, call_args_dict)
    if cache_result is not None:
        return cache_result
```

**Cache Key**: Based on call arguments (model, messages, etc.)

### 6.2 Retry with Cache Invalidation

```python
cnt = 0
while not succ and retry_cnt < 50:
    llm_result = get_llm_output(
        node, self, memory, "execute", 
        overwrite_cache=(retry_cnt > 0)  # Invalidate on retry
    )
```

---

## 7. Heterogeneous Task Integration

### 7.1 Memory Context Building

**Memory Module** (recursive/memory.py):

```python
def collect_node_run_info(node):
    memory_info = {
        "upper_graph_precedents": [],   # Dependencies from parent levels
        "same_graph_precedents": []     # Dependencies from same level
    }
```

**Context Passed to Prompts**:
- `to_run_article`: Previously written content
- `to_run_full_plan`: Full task hierarchy
- `to_run_outer_graph_dependent`: Results from dependency tasks
- `to_run_same_graph_dependent`: Results from same-level dependencies
- `to_run_candidate_plan`: Reference planning from previous attempts
- `to_run_candidate_think`: Design conclusions from planning phase

### 7.2 Prompt Template System

**Base Classes**: `PromptTemplate` (recursive/agent/prompts/base.py)

**Available Prompt Variants**:
- **Report Mode**: 
  - `ReportPlanning`
  - `ReportAtom` / `ReportAtomWithUpdate`
  - `ReportReasoner`
  - `ReportWriter`
  - `SearchAgentPrompt`
  - `MergeSearchResult`

- **Story Mode**:
  - `StoryWritingNLPlanningEN`
  - `StoryWritingNLWriteAtomEN` / `StoryWritingNLWriteAtomWithUpdateEN`
  - `StoryWrtingNLReasonerEN`
  - `StoryWrtingNLWriterEN`

---

## 8. Token Estimation Framework

### 8.1 Prompt Component Sizes (Estimated)

**Fixed Components**:
- System message: 500-2,000 tokens
- Task instruction: 200-500 tokens
- Output format specification: 300-800 tokens

**Variable Components**:
- Task goal: 20-200 tokens
- Previous article content: 500-5,000 tokens (varies)
- Full plan context: 500-2,000 tokens
- Dependency results: 500-3,000 tokens
- Candidate plan/think: 200-1,000 tokens

**Typical Input Token Range**:
```
Minimal: 1,500 - 3,000 tokens (simple atomic task)
Medium: 3,000 - 8,000 tokens (standard task with context)
Large: 8,000 - 20,000 tokens (complex task with full context)
```

### 8.2 Output Token Estimation

**By Task Type**:
- **Planning output**: 200-500 tokens (JSON plan structure)
- **Atom judgment**: 50-100 tokens (single word + reasoning)
- **Writing output**: 500-2,000 tokens per 500-word chunk
- **Reasoning output**: 300-1,000 tokens
- **Search planning**: 200-500 tokens per turn

### 8.3 Cost Estimation Tool

**Implementation** (llm.py, lines 383):
```python
price = (input_tokens / 1_000_000) * ip + (output_tokens / 1_000_000) * op
logger.debug(f"{model}: {input_tokens} input, {output_tokens} output, ${price:.4f}")
```

**Cost per Model (for typical report)**:
- GPT-4o: ~$1.50-2.00 per 8,000-word report
- GPT-4o-mini: ~$0.15-0.25 (30x cheaper)
- Claude 3.5: ~$1.00-1.50
- o1: ~$0.50-0.80 (lower token count but expensive)

---

## 9. Metrics and Logging

### 9.1 Integrated Logging

**Logger Setup**:
```python
from loguru import logger

custom_format = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>"
log_id = logger.add(f"{folder}/engine.log", format=custom_format)
```

**Logged Information**:
1. **Step counter**: Every 1-3000 steps
2. **Node selection**: Which node is executing
3. **Action execution**: Planning, execution, aggregation
4. **LLM calls**: 
   - Messages passed to LLM
   - Model used
   - Token counts (debug level)
   - Pricing
5. **Parse results**: JSON extraction results
6. **Retries**: Parse failures and retry counts

### 9.2 Output Files

**Per execution**:
- `engine.log`: Full execution trace
- `nodes.json`: Task graph structure and results
- `nodes.pkl`: Pickled task graph (for recovery)
- `memory.jsonl`: Article content and search results
- `report.md`: Final report output

### 9.3 Token Usage Summary

Currently, token counts are logged at DEBUG level:
```python
if self.verbose:
    logger.debug(f"{model} Usage: {data.get('usage', {})}")
    logger.debug(f"{model}: {input_tokens} input, {output_tokens} output, ${price:.4f}")
```

**Enhancement Opportunity**: 
- Aggregate token counts to a summary file
- Provide token cost breakdown by task type
- Compare actual vs. estimated costs

---

## 10. Key Findings Summary

### LLM Call Volumes

| Mode | Writing | Planning | Search | Reasoning | Total |
|------|---------|----------|--------|-----------|-------|
| Story (4K words) | 4-6 | 8 | 0 | 0 | 15-20 |
| Report (8K words) | 8-10 | 8 | 100+ | 8 | 130-160 |

### Token Consumption

| Metric | Story | Report |
|--------|-------|--------|
| Input tokens | ~50K | ~135K |
| Output tokens | ~15K | ~28K |
| Total tokens | ~65K | ~163K |
| Cost (GPT-4o) | ~$0.40 | ~$1.80 |
| Cost (GPT-4o-mini) | ~$0.04 | ~$0.18 |

### Recursion Depth

- **Story mode**: 3-4 levels (natural termination)
- **Report mode**: 3 levels (forced atom layer)
- **Max tasks per run**: 250-300 for reports, 50-100 for stories

### Planning Efficiency

- **Atom judgment**: Determines task atomicity in 1 LLM call
- **Planning**: Generates DAG with 3-8 subtasks
- **Caching**: Prevents redundant LLM calls via result memoization

---

## 11. Configuration Files and Model Support

### Model Configuration (`model_config.yaml`)

**Default Models**:
- Story: GPT-4o
- Report: GPT-4o
- Selector: GPT-4o-mini
- Summarizer: GPT-4o-mini

**Available Presets**:
- `premium`: Claude 3.7 + GPT-4o for reports
- `balanced`: GPT-4o for both
- `economy`: GPT-4o-mini for all
- `gemini`: Gemini models
- `claude`: Claude models

**Temperature Settings**:
- Composition (writing): 0.3
- Reasoning (analysis): 0.3
- Planning (decomposition): 0.1

---

## 12. Recommendations for Token Optimization

1. **Implement token budgets** per task type
2. **Add sampling** for large dependency contexts (truncate old results)
3. **Optimize prompt templates** to remove redundant instructions
4. **Use cheaper models** for selector/summarizer tasks
5. **Implement early termination** for well-formed outputs
6. **Cache planning results** across similar tasks
7. **Add token usage analytics** dashboard

---

## Conclusion

WriteHERE employs a sophisticated multi-agent system with careful orchestration of LLM calls. The heterogeneous task decomposition generates 15-20 calls for stories and 130-160 calls for reports, with total token consumption of 65K-163K tokens depending on mode and complexity. The system provides extensive logging and caching mechanisms, with configurable model selection and automatic cost tracking.

