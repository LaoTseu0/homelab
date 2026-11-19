import unittest

from jarvis_exporter.assist import analyze_pipeline_events


def event(event_type: str, second: int, data=None):
    return {
        "type": event_type,
        "timestamp": f"2026-08-23T10:00:{second:02d}+00:00",
        "data": data,
    }


class AnalyzePipelineEventsTest(unittest.TestCase):
    def test_extracts_privacy_safe_stage_durations(self):
        observation = analyze_pipeline_events(
            [
                event("run-start", 0),
                event("stt-start", 1),
                event("stt-vad-start", 2),
                event("stt-vad-end", 4),
                event("stt-end", 5, {"stt_output": {"text": "secret"}}),
                event("intent-start", 5),
                event("intent-progress", 6, {"chat_log_delta": "secret"}),
                event("intent-end", 7),
                event("tts-start", 7, {"tts_input": "secret"}),
                event("tts-end", 8),
                event("run-end", 9),
            ]
        )

        self.assertTrue(observation.complete)
        self.assertEqual("success", observation.status)
        self.assertEqual(9, observation.stages["pipeline"])
        self.assertEqual(2, observation.stages["speech"])
        self.assertEqual(1, observation.stages["stt_after_speech"])
        self.assertEqual(2, observation.stages["intent"])
        self.assertEqual(1, observation.stages["intent_first_progress"])
        self.assertNotIn("secret", repr(observation))

    def test_reports_error_code_without_message(self):
        observation = analyze_pipeline_events(
            [
                event("run-start", 0),
                event("error", 1, {"code": "intent-failed", "message": "secret"}),
                event("run-end", 2),
            ]
        )

        self.assertEqual("error", observation.status)
        self.assertEqual(("intent-failed",), observation.error_codes)
        self.assertNotIn("secret", repr(observation))

    def test_incomplete_run_is_not_ready_for_collection(self):
        observation = analyze_pipeline_events([event("run-start", 0)])
        self.assertFalse(observation.complete)


if __name__ == "__main__":
    unittest.main()

