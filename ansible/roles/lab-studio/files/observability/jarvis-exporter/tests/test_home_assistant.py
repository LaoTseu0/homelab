import unittest
from unittest.mock import Mock

from jarvis_exporter.config import HomeAssistantConfig
from jarvis_exporter.home_assistant import HomeAssistantCollector


def completed_events(start_second, end_second):
    return [
        {
            "type": "run-start",
            "timestamp": f"2026-08-23T10:00:{start_second:02d}+00:00",
        },
        {
            "type": "run-end",
            "timestamp": f"2026-08-23T10:00:{end_second:02d}+00:00",
        },
    ]


class FakeWebSocket:
    def close(self):
        pass


class HomeAssistantCollectorTest(unittest.TestCase):
    def test_seeds_existing_runs_then_observes_only_new_runs(self):
        config = HomeAssistantConfig(
            enabled=True,
            websocket_url="ws://homeassistant/api/websocket",
            token="token",
            poll_interval_seconds=10,
            pipeline_ids=(),
        )
        metrics = Mock()
        collector = HomeAssistantCollector(config, metrics)
        collector._connect = Mock(return_value=FakeWebSocket())
        poll_number = 0

        def call(_websocket, command_type, **parameters):
            nonlocal poll_number
            if command_type == "assist_pipeline/pipeline/list":
                poll_number += 1
                return {"pipelines": [{"id": "pipeline-1", "name": "Jarvis"}]}
            if command_type == "assist_pipeline/pipeline_debug/list":
                run_ids = ["old-run"]
                if poll_number > 1:
                    run_ids.append("new-run")
                return {
                    "pipeline_runs": [
                        {"pipeline_run_id": run_id} for run_id in run_ids
                    ]
                }
            if command_type == "assist_pipeline/pipeline_debug/get":
                run_id = parameters["pipeline_run_id"]
                return {
                    "events": (
                        completed_events(0, 2)
                        if run_id == "old-run"
                        else completed_events(10, 13)
                    )
                }
            raise AssertionError(f"Commande inattendue : {command_type}")

        collector._call = Mock(side_effect=call)

        collector.collect_once()
        metrics.observe_assist.assert_not_called()

        collector.collect_once()
        metrics.observe_assist.assert_called_once()
        pipeline_id, pipeline_name, observation = metrics.observe_assist.call_args.args
        self.assertEqual("pipeline-1", pipeline_id)
        self.assertEqual("Jarvis", pipeline_name)
        self.assertEqual(3, observation.stages["pipeline"])


if __name__ == "__main__":
    unittest.main()
