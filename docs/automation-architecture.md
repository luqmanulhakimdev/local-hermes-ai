# AI Automation Agent Architecture

## 1. Overview

The AI Automation Agent uses a Planner-Executor architecture.

The Planner converts user instructions into structured task plans. The Executor validates and runs each step using tools registered in the Tool Registry.

The LLM is responsible for planning, while Python controls actual tool execution.

## 2. Core Components

### Automation Agent

- Receives user requests.
- Coordinates the planner and executor.
- Returns execution results.

### Planner

- Converts natural language instructions into structured task plans.
- Produces JSON-compatible output.
- Does not execute tools directly.

### Plan Validator

- Validates task structure.
- Checks required fields and argument types.
- Rejects unknown tools.
- Enforces the maximum step limit.

### Tool Registry

- Stores available tool definitions.
- Provides an allowlist of executable tools.
- Exposes tool metadata and execution functions.

### Executor

- Executes validated steps sequentially.
- Resolves references to previous step outputs.
- Handles execution errors.
- Stops execution when a step fails.

### Logger

- Records task IDs and step IDs.
- Records execution status and timestamps.
- Stores error information for failed steps.

## 3. Execution Flow

1. Receive a user request.
2. Generate a task plan using the LLM.
3. Parse and validate the plan.
4. Verify that all requested tools are registered.
5. Execute steps sequentially.
6. Resolve outputs from previous steps when needed.
7. Record each step's status.
8. Return the final task result.

## 4. Task Data Model

A task contains:
- Task ID
- Description
- List of steps
- Overall execution status

Each step contains:
- Step ID
- Tool name
- Arguments
- Execution status
- Output or error information

## 5. Safety Controls

- Only registered tools may be executed.
- Tool arguments must be validated.
- Maximum of 5 steps per task.
- File access must remain within permitted directories.
- No unrestricted shell execution.
- Destructive and external actions require explicit confirmation.
- Failed steps stop the current task.
- Previous step outputs are treated as data, not executable instructions.

## 6. Initial Tool Set

- read_file
- list_files
- summarize_text
- save_note
- search_notes
- calculator
- get_current_time

## 7. Execution Strategy

The initial implementation uses sequential execution.

Parallel execution, background scheduling, and external service integrations are deferred until the basic execution engine is stable.

## 8. Testing Strategy

Automated tests will cover:
- Task and step model validation.
- Planner output parsing.
- Unknown tool rejection.
- Invalid argument rejection.
- Maximum step enforcement.
- Sequential execution.
- Step output references.
- Execution failures and logging.