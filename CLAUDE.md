# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

WriteHERE is a framework for long-form writing using heterogeneous recursive planning. The system breaks down complex writing tasks (stories, technical reports) into a hierarchical task graph with three task types: **RETRIEVAL** (search/gather info), **REASONING** (think/analyze), and **COMPOSITION** (write content). Tasks are recursively decomposed and executed through a state machine architecture.

## Architecture

### Core Components

**Task Graph System** (`recursive/graph.py`)
- `Graph`: Manages task nodes and dependencies with topological sorting
- `AbstractNode`: Base class for all task nodes with status state machine
- `RegularDummyNode`: Concrete implementation with plan/execute lifecycle
- `TaskStatus`: Enum defining node states (NOT_READY, READY, DOING, FINISH, etc.)
- `NodeType`: Either PLAN_NODE (decomposes into subtasks) or EXECUTE_NODE (atomic task)

**Engine** (`recursive/engine.py`)
- `GraphRunEngine`: Main execution engine that iterates through task graph
- Saves/loads execution state to resume interrupted tasks
- `forward_one_step_untill_done()`: Main execution loop

**Memory System** (`recursive/memory.py`)
- `Memory`: Manages context and retrieved information across task execution
- `InfoNode`: Stores retrieved information chunks

**Task Execution** (`recursive/executor/`)
- `actions/`: Built-in actions (web search, browser interaction)
- `agents/`: Agent implementations (Claude with function calling)
- `schema.py`: Return types and status codes

**Agent System** (`recursive/agent/`)
- `agents/`: Different agent implementations per task type
- `prompts/`: Prompts for planning, execution, reflection
- `proxy.py`: Routes tasks to appropriate agents

### Task Lifecycle

1. **NOT_READY** → Wait for dependencies
2. **READY** → Execute plan() for PLAN_NODE or execute() for EXECUTE_NODE
3. **PLAN_DONE** → Run prior_reflect() validation
4. **DOING** → Execute internal subtasks
5. **FINAL_TO_FINISH** → Run final_aggregate() to combine results
6. **NEED_POST_REFLECT** → Run post-reflection validation
7. **FINISH** → Task complete

## Development Commands

### Environment Setup

**Initial setup (recommended)**:
```bash
./setup_env.sh  # Creates venv and installs dependencies
```

**Alternative setup**:
```bash
python -m venv venv
source venv/bin/activate
pip install -v -e .
pip install -r backend/requirements.txt  # If using web interface
```

**Anaconda users**:
```bash
./run_with_anaconda.sh  # Creates 'writehere' conda environment
```

### API Configuration

Create `recursive/api_key.env` with:
```
OPENAI=your_openai_key
CLAUDE=your_anthropic_key
SERPAPI=your_serpapi_key
GEMINI=your_google_key
OPENROUTER=your_openrouter_key
```

### Running the Engine

**Story generation**:
```bash
cd recursive
python engine.py --filename ../test_data/meta_fiction.jsonl \
                 --output-filename ./project/story/output.jsonl \
                 --done-flag-file ./project/story/done.txt \
                 --model gpt-4o \
                 --mode story
```

**Report generation**:
```bash
cd recursive
python engine.py --filename ../test_data/qa_test.jsonl \
                 --output-filename ./project/qa/result.jsonl \
                 --done-flag-file ./project/qa/done.txt \
                 --model claude-3-sonnet \
                 --mode report
```

**Supported models**: `gpt-4o`, `claude-3-sonnet`, `gemini-2.5-pro-preview-03-25`

**Backend options**: `--engine-backend` (openai, anthropic, google)

### Web Interface

**Start backend + frontend**:
```bash
./start.sh  # Backend on port 5001, frontend on port 3000
./start.sh --backend-port 8080 --frontend-port 8000  # Custom ports
```

**Manual backend start**:
```bash
cd backend
python server.py --port 5001
```

**Manual frontend start**:
```bash
cd frontend
npm install
npm start  # or PORT=8000 npm start
```

**Test backend**:
```bash
cd backend
python test_api.py --port 5001
```

### Testing

**Run tests**:
```bash
pytest
```

**Test scripts**:
```bash
cd recursive
./test_run_story.sh    # Story generation test
./test_run_report.sh   # Report generation test
```

## Code Patterns

### Task Types

The system uses three fundamental task types defined in config:
- **RETRIEVAL**: Search web, gather information (e.g., "search for historical facts")
- **REASONING**: Analyze, think, plan (e.g., "analyze character motivations")
- **COMPOSITION**: Write content (e.g., "write opening paragraph")

### Adding New Nodes

Nodes are created through planning. The planner returns JSON with:
```python
{
    "id": 1,
    "task_type": "search|think|write",
    "goal": "description",
    "dependency": [0],  # IDs of parent tasks
    "length": "500 words",  # For write tasks
}
```

### State Machine Actions

Each node has action methods called by the state machine:
- `plan()`: Decompose into subtasks
- `update()`: Update based on completed dependencies
- `execute()`: Execute atomic task
- `prior_reflect()`: Validate plan before execution
- `final_aggregate()`: Combine subtask results
- `planning_post_reflect()`: Validate aggregated results
- `execute_post_reflect()`: Validate execution results

### Agent Integration

Agents are selected via `agent_proxy.proxy(action_name)` which maps to specific agent implementations in `recursive/executor/agents/`.

## Key Files

- `recursive/engine.py` - Main execution engine
- `recursive/graph.py` - Task graph and node implementations
- `recursive/memory.py` - Context management
- `backend/server.py` - Flask REST API with WebSocket
- `frontend/src/` - React visualization interface

## Installation Notes

- Package is installed in editable mode: `pip install -e .`
- Python 3.6+ required
- Node.js 14+ required for frontend
- The package name is `recursive` (from setup.cfg)

## Common Issues

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for environment setup issues, dependency conflicts, and port binding problems.
