"""CLI entry point for Local Hermes AI integration."""

import argparse
import json
import sys
import uuid

from src.automation.rag_context import RAGContextRetriever
from src.automation_agent import AutomationAgent
from src.hermes.config import HermesConfig
from src.hermes.health import check_hermes
from src.hermes.protocol import HermesRequest
from src.hermes.service import HermesService


def main():
    parser = argparse.ArgumentParser(
        description="Local Hermes AI - Hermes Integration Interface"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Run health check for local Hermes installation and Ollama",
    )
    parser.add_argument(
        "--run",
        type=str,
        help="Run an automation task through the Hermes service bridge",
    )
    parser.add_argument(
        "--rag",
        action="store_true",
        help="Enable RAG context retrieval for the automation task",
    )
    parser.add_argument(
        "--status",
        type=str,
        help="Query status of an existing task by Task ID",
    )
    parser.add_argument(
        "--resume",
        type=str,
        help="Resume an interrupted task by Task ID",
    )

    args = parser.parse_args()

    config = HermesConfig()

    if args.check:
        report = check_hermes(config)
        print("Hermes Health Report:")
        print(json.dumps(report, indent=2))
        sys.exit(0 if report["status"] == "ok" else 1)

    rag_retriever = RAGContextRetriever() if args.rag else None
    agent = AutomationAgent(rag_retriever=rag_retriever)
    service = HermesService(agent=agent, config=config)

    if args.run:
        req = HermesRequest(
            request_id=str(uuid.uuid4()),
            operation="run_automation",
            message=args.run,
            arguments={"use_rag": args.rag},
        )
        resp = service.handle_request(req)
        print(f"Status: {resp.status}")
        print(f"Message: {resp.message}")
        if resp.task_id:
            print(f"Task ID: {resp.task_id}")
        if resp.data:
            print(f"Data: {json.dumps(resp.data, indent=2)}")
        if resp.error:
            print(f"Error: {resp.error}")
        sys.exit(0 if resp.status == "completed" else 1)

    if args.status:
        req = HermesRequest(
            request_id=str(uuid.uuid4()),
            operation="get_task_status",
            message=args.status,
            arguments={"task_id": args.status},
        )
        resp = service.handle_request(req)
        print(json.dumps(resp.data or {"status": resp.status, "message": resp.message}, indent=2))
        sys.exit(0 if resp.status == "completed" else 1)

    if args.resume:
        req = HermesRequest(
            request_id=str(uuid.uuid4()),
            operation="resume_task",
            message=args.resume,
            arguments={"task_id": args.resume},
        )
        resp = service.handle_request(req)
        print(f"Status: {resp.status}")
        print(f"Message: {resp.message}")
        if resp.data:
            print(f"Data: {json.dumps(resp.data, indent=2)}")
        if resp.error:
            print(f"Error: {resp.error}")
        sys.exit(0 if resp.status == "completed" else 1)

    parser.print_help()


if __name__ == "__main__":
    main()
