"""
Minimal LangChain example with EcoTrace.

Tracks the carbon footprint of every LLM call, including batched calls.
Uses LangChain's built-in fake LLM, so it runs offline with no API key.
Swap in any real model (ChatOpenAI, ChatAnthropic, ChatOllama, ...) the same way.

Requires: langchain-core
"""

from langchain_core.language_models.fake import FakeListLLM

from ecotrace.callbacks import EcoTraceLangChainCallback


def main() -> None:
    """Run a few LLM calls while EcoTrace measures each one."""
    cb = EcoTraceLangChainCallback(
        project_name="langchain-demo",
        output_file="langchain_emissions.csv",
        verbose=True,
    )
    llm = FakeListLLM(responses=["Paris", "Berlin", "Tokyo"])

    llm.invoke("Capital of France?", config={"callbacks": [cb]})
    llm.batch(["Capital of Germany?", "Capital of Japan?"], config={"callbacks": [cb]})

    for record in cb.records:
        print(f"{record['model']:<12} {record['duration_s']:.4f}s  {record['emissions_g']:.8f} gCO2")
    print(cb.summary())


if __name__ == "__main__":
    main()
