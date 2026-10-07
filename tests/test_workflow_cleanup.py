import json
from pathlib import Path
import shutil
import subprocess
import textwrap
import unittest


NODE_HARNESS = r"""
const fs = require('fs');
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const calls = { get: [], list: [], deleted: [], messages: [] };
const actions = {
  getWorkflowRun: async (args) => {
    calls.get.push(args);
    return {data: {workflow_id: 42}};
  },
  listWorkflowRuns: () => {},
  deleteWorkflowRun: async (args) => {
    calls.deleted.push(args.run_id);
    if (input.errorStatus) throw Object.assign(new Error('delete failed'), {status: input.errorStatus});
  },
};
const github = {
  rest: {actions},
  paginate: async (method, args) => {
    if (method !== actions.listWorkflowRuns) throw new Error('unexpected endpoint');
    calls.list.push(args);
    return input.runs;
  },
};
const context = {repo: {owner: 'owner', repo: 'repo'}, runId: 99};
const core = {info: (message) => calls.messages.push(message)};
const clock = {now: () => Date.parse('2026-10-07T00:00:00Z'), parse: Date.parse};
const AsyncFunction = Object.getPrototypeOf(async function() {}).constructor;
(async () => {
  try {
    await new AsyncFunction('github', 'context', 'core', 'process', 'Date', input.script)(
      github, context, core, {env: {ACTIONS_RETENTION_DAYS: input.days}}, clock
    );
  } catch (error) {
    calls.error = error.message;
  }
  console.log(JSON.stringify(calls));
})();
"""


@unittest.skipUnless(shutil.which("node"), "Node.js is needed to check github-script")
class WorkflowCleanupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        workflow = Path(__file__).resolve().parents[1] / ".github/workflows/rainyun.yml"
        content = workflow.read_text(encoding="utf-8")
        cls.script = textwrap.dedent(content.split("          script: |\n", 1)[1])

    def run_cleanup(self, runs, days="7", error_status=None):
        result = subprocess.run(
            [shutil.which("node"), "-e", NODE_HARNESS],
            input=json.dumps({"script": self.script, "runs": runs, "days": days, "errorStatus": error_status}),
            text=True, capture_output=True, check=True,
        )
        return json.loads(result.stdout)

    def run_record(self, run_id=1, created_at="2026-09-01T00:00:00Z", status="completed"):
        return {"id": run_id, "created_at": created_at, "status": status}

    def test_deletes_only_old_completed_runs(self):
        result = self.run_cleanup([
            self.run_record(),
            self.run_record(2, "2026-10-06T00:00:00Z"),
            self.run_record(3, status="in_progress"),
            self.run_record(4, status="queued"),
            self.run_record(99),
        ])
        self.assertEqual(result["deleted"], [1])

    def test_retention_boundary_is_preserved(self):
        result = self.run_cleanup([
            self.run_record(1, "2026-09-30T00:00:00Z"),
            self.run_record(2, "2026-09-29T23:59:59Z"),
        ])
        self.assertEqual(result["deleted"], [2])

    def test_uses_paginated_current_workflow_endpoint(self):
        result = self.run_cleanup([])
        self.assertEqual(result["get"][0]["run_id"], 99)
        self.assertEqual(result["list"], [{
            "owner": "owner", "repo": "repo", "workflow_id": 42,
            "status": "completed", "per_page": 100,
        }])

    def test_invalid_retention_stops_before_api_calls(self):
        for days in ("0", "-1", "1.5", "", "invalid"):
            with self.subTest(days=days):
                result = self.run_cleanup([self.run_record()], days=days)
                self.assertIn("positive integer", result["error"])
                self.assertEqual(result["get"], [])
                self.assertEqual(result["deleted"], [])

    def test_invalid_date_is_preserved(self):
        result = self.run_cleanup([self.run_record(created_at="invalid")])
        self.assertEqual(result["deleted"], [])

    def test_concurrent_deletion_404_is_tolerated(self):
        result = self.run_cleanup([self.run_record()], error_status=404)
        self.assertNotIn("error", result)
        self.assertIn("already deleted", result["messages"][0])

    def test_permissions_error_is_reported(self):
        result = self.run_cleanup([self.run_record()], error_status=403)
        self.assertIn("delete failed", result["error"])

    def test_empty_history_succeeds(self):
        result = self.run_cleanup([])
        self.assertEqual(result["deleted"], [])
        self.assertIn("Deleted 0", result["messages"][0])
