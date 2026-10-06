import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from rainyun.scheduler import cron_runner
from rainyun.scheduler.runner import AccountRenewResult, AccountRunResult


class CronExitStatusTests(unittest.TestCase):
    def checkin(self, success=True, status="signed"):
        return AccountRunResult("test", "test", success, status, message="test result")

    def renew(self, success=True, has_api_key=True):
        return AccountRenewResult("test", "test", has_api_key, [], [], success)

    def run_task(self, checkins, renewals, notify_error=None):
        store = Mock()
        store.load.return_value = SimpleNamespace(
            accounts=[SimpleNamespace(enabled=True)], settings=SimpleNamespace()
        )
        runner = Mock()
        runner.run.return_value = checkins
        runner.run_renew.return_value = renewals
        with (
            patch.object(cron_runner, "ensure_file_handler"),
            patch.object(cron_runner, "_acquire_lock", return_value=-1),
            patch.object(cron_runner, "DataStore", return_value=store),
            patch.object(cron_runner, "MultiAccountRunner", return_value=runner),
            patch.object(cron_runner.Config, "from_account", return_value=Mock()),
            patch.object(cron_runner, "configure"),
            patch.object(cron_runner, "send", side_effect=notify_error) as send,
        ):
            status = cron_runner.main()
        send.assert_called_once()
        runner.run_renew.assert_called_once()
        return status, send.call_args.args[1]

    def test_success_returns_zero(self):
        status, _ = self.run_task([self.checkin()], [self.renew()])
        self.assertEqual(status, 0)

    def test_failed_checkin_returns_one_and_sends_summary(self):
        status, content = self.run_task([self.checkin(False, "failed")], [self.renew()])
        self.assertEqual(status, 1)
        self.assertIn("失败", content)

    def test_partial_checkin_failure_returns_one(self):
        status, _ = self.run_task([self.checkin(), self.checkin(False, "failed")], [])
        self.assertEqual(status, 1)

    def test_already_signed_returns_zero(self):
        status, content = self.run_task([self.checkin(status="already_signed")], [])
        self.assertEqual(status, 0)
        self.assertIn("已签到", content)

    def test_failed_renew_check_returns_one(self):
        status, _ = self.run_task([self.checkin()], [self.renew(False)])
        self.assertEqual(status, 1)

    def test_missing_api_key_is_a_successful_skip(self):
        status, _ = self.run_task([self.checkin()], [self.renew(False, False)])
        self.assertEqual(status, 0)

    def test_notify_failure_does_not_hide_checkin_failure(self):
        status, _ = self.run_task([self.checkin(False, "failed")], [], RuntimeError("offline"))
        self.assertEqual(status, 1)

    def test_notify_failure_does_not_fail_successful_checkin(self):
        status, _ = self.run_task([self.checkin()], [], RuntimeError("offline"))
        self.assertEqual(status, 0)

    def test_no_enabled_accounts_returns_zero(self):
        with (
            patch.object(cron_runner, "ensure_file_handler"),
            patch.object(cron_runner, "_acquire_lock", return_value=-1),
            patch.object(cron_runner, "DataStore") as store,
            patch.object(cron_runner, "MultiAccountRunner") as runner,
            patch.object(cron_runner, "send") as send,
        ):
            store.return_value.load.return_value = SimpleNamespace(accounts=[])
            runner.return_value.run.return_value = []
            runner.return_value.run_renew.return_value = []
            self.assertEqual(cron_runner.main(), 0)
        send.assert_not_called()


if __name__ == "__main__":
    unittest.main()
