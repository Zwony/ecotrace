# LangChain Integration

### Hardware Energy, Latency, and Operational Carbon Instrumentation for LLM Workloads

---

!!! success "Officially Cataloged Integration"
    EcoTrace is an officially cataloged callback provider in the [LangChain Provider Directory](https://docs.langchain.com/oss/python/integrations/providers/all_providers). Native support is verified across all `langchain-core` execution targets.

---

## Overview

The `EcoTraceLangChainCallback` provides thread-safe, process-scoped hardware telemetry for LangChain chains, autonomous agents, and chat models. 

Unlike traditional token-only profilers, EcoTrace directly interfaces with physical hardware interfaces (Intel/AMD RAPL, NVIDIA NVML, Apple Silicon Energy Model) to measure:

- **Exact Energy Consumed:** Real-time Joules ($J$) and Watt-hours ($Wh$) drawn during model execution.
- **Physical Latency:** Microsecond-resolution execution duration per invocation.
- **Operational Carbon Footprint:** Calibrated grams of $CO_2$ ($gCO_2$) based on localized power grid emission factors.
- **Token Usage Alignment:** Captures prompt, completion, and total token statistics reported by provider responses.

---

## Installation

Install EcoTrace alongside your preferred LangChain dependencies:

```bash
pip install ecotrace langchain-core
```

For GPU acceleration telemetry (NVIDIA NVML):

```bash
pip install ecotrace[gpu]
```

---

## Quick Start

### 1. Basic Chat Model Profiling

Attach `EcoTraceLangChainCallback` directly to the `config` dictionary of any runnable invocation:

```python
from langchain_openai import ChatOpenAI
from ecotrace.callbacks import EcoTraceLangChainCallback

# Initialize handler
callback = EcoTraceLangChainCallback(project_name="customer-support-rag")

# Initialize your model
llm = ChatOpenAI(model="gpt-4o", temperature=0)

# Execute query with callback attached
response = llm.invoke(
    "Analyze the energy efficiency of vector indexing.",
    config={"callbacks": [callback]}
)

# Inspect telemetry
print(f"Emissions: {callback.total_emissions_g:.6f} gCO2")
print(f"Total Energy: {callback.total_energy_kwh * 1000:.4f} Wh")
```

---

## In-Depth Examples

### 2. Multi-Step Chains (LCEL)

In a standard LangChain Expression Language (LCEL) pipeline, passing the callback to the outer chain automatically records metrics for every component:

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from ecotrace.callbacks import EcoTraceLangChainCallback

callback = EcoTraceLangChainCallback(project_name="lcel-pipeline")

prompt = ChatPromptTemplate.from_template("Translate the following sentence to French: {text}")
model = ChatOpenAI(model="gpt-4o-mini")
parser = StrOutputParser()

chain = prompt | model | parser

result = chain.invoke(
    {"text": "Sustainable software engineering minimizes compute overhead."},
    config={"callbacks": [callback]}
)

# Inspect individual execution records
for record in callback.records:
    print(f"Run ID: {record['run_id']}")
    print(f"Model: {record['model_name']}")
    print(f"Duration: {record['duration_s']:.3f}s")
    print(f"Emissions: {record['emissions_g']:.6f} gCO2")
```

---

### 3. Autonomous Agents & Multi-Turn Tool Use

When running autonomous agents with iterative tool calling, EcoTrace isolates LLM inference cycles from background system noise:

```python
from langchain.agents import create_react_agent, AgentExecutor
from ecotrace.callbacks import EcoTraceLangChainCallback

callback = EcoTraceLangChainCallback(project_name="react-agent")

# Pass callback to agent executor
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

response = agent_executor.invoke(
    {"input": "Find the latest renewable energy stats and summarize them."},
    config={"callbacks": [callback]}
)

# Access aggregate metrics across all turns
summary = callback.get_summary()
print(f"Total Invocations: {summary['total_runs']}")
print(f"Total Carbon: {summary['total_emissions_g']:.6f} gCO2")
```

---

## Configuration & Attributes

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `project_name` | `str` | `"langchain"` | Logical project identifier for metric aggregation. |
| `region_code` | `str` | Auto-detected | ISO country code for regional grid carbon intensity (e.g., `"US"`, `"DE"`, `"TR"`). |
| `api_key` | `str` | `None` | Optional API key for streaming to the EcoTrace cloud dashboard. |

### Accessing Collected Telemetry

The callback instance exposes the following real-time properties:

- `callback.total_emissions_g` (`float`): Cumulative carbon footprint in grams of $CO_2$.
- `callback.total_energy_kwh` (`float`): Total electrical energy consumed in Kilowatt-hours ($kWh$).
- `callback.records` (`List[Dict]`): Detailed log of each invocation containing `run_id`, `model_name`, `duration_s`, `emissions_g`, and `token_usage`.
- `callback.reset()`: Resets all counters and clears stored records for the next test batch.

---

## Defensive Isolation & Production Safety

`EcoTraceLangChainCallback` is engineered for zero blast-radius production deployments:

1. **Non-Blocking Telemetry:** Hardware measurement failures (e.g. constrained container permissions) are captured safely and logged at `DEBUG` level. They will **never** throw unhandled exceptions or interrupt user-facing model calls.
2. **Thread Safety:** Invocations across concurrent threads or asynchronous tasks are isolated using internal mutex synchronization.

