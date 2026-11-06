# AI Engineering

AI Engineering is a discipline focused on building applications that incorporate artificial intelligence as part of the system.

## Large Language Models

Large Language Models (LLMs) are machine learning models trained on vast amounts of text data. LLMs can be used for a wide variety of tasks such as question answering, summarization, classification, and code generation.

## Retrieval-Augmented Generation

Retrieval-Augmented Generation (RAG) is a technique that combines information retrieval with generative AI.

In a RAG system, documents are first broken down into smaller pieces or chunks. Each chunk is then converted into a vector embedding.

When a user submits a question, the system searches for the most relevant chunks based on similarity. Those chunks are then provided to the LLM as context.

With this approach, the LLM can generate answers based on a specific knowledge base without requiring the model to be retrained.

## AI Agents

An AI Agent is a system that enables an LLM to make decisions and invoke tools to accomplish tasks.

Examples of tools an agent can use include calculators, file readers, databases, web search, and APIs.

An agent typically operates using a decision loop:

1. Receive the task from the user.
2. Analyze the task.
3. Select an action or tool.
4. Execute the tool.
5. Read and interpret the result.
6. Repeat the process if necessary.
7. Provide the final answer.

## Local AI

Local AI runs AI models on your own machine using runtimes such as Ollama.

Benefits of local AI include better privacy, no dependency on cloud APIs, and the ability to experiment independently with AI Engineering workflows.
