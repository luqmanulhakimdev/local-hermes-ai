import unittest

from src.hermes.errors import InvalidRequestError
from src.hermes.protocol import HermesRequest, HermesRequestStatus, HermesResponse


class TestHermesProtocol(unittest.TestCase):
    def test_valid_request(self):
        req = HermesRequest(
            request_id="req-123",
            operation="run_automation",
            message="Calculate 2 + 2",
            arguments={"use_rag": False},
        )
        self.assertEqual(req.request_id, "req-123")
        self.assertEqual(req.operation, "run_automation")
        self.assertEqual(req.message, "Calculate 2 + 2")
        self.assertEqual(req.arguments, {"use_rag": False})

    def test_empty_request_id_raises_error(self):
        with self.assertRaises(InvalidRequestError):
            HermesRequest(request_id="", operation="run_automation", message="test")

    def test_invalid_operation_raises_error(self):
        with self.assertRaises(InvalidRequestError):
            HermesRequest(request_id="req-1", operation="arbitrary_command", message="test")

    def test_empty_message_raises_error(self):
        with self.assertRaises(InvalidRequestError):
            HermesRequest(request_id="req-1", operation="run_automation", message="")

    def test_valid_response(self):
        res = HermesResponse(
            request_id="req-123",
            status=HermesRequestStatus.COMPLETED,
            message="Task finished successfully",
            task_id="task-456",
            data={"result": 4},
        )
        self.assertEqual(res.request_id, "req-123")
        self.assertEqual(res.status, HermesRequestStatus.COMPLETED)
        self.assertEqual(res.task_id, "task-456")
        self.assertIsNone(res.error)

    def test_invalid_response_status_raises_error(self):
        with self.assertRaises(ValueError):
            HermesResponse(
                request_id="req-123",
                status="unknown_status",
                message="Done",
            )


if __name__ == "__main__":
    unittest.main()
