"""Tests for health score calculation."""

from agentdoctor.core.models import CheckResult, CheckSeverity, CheckStatus, HealthScore


class TestHealthScore:
    def test_initial_state(self):
        score = HealthScore()
        assert score.score == 100
        assert score.passed == 0
        assert score.warnings == 0
        assert score.errors == 0
        assert score.is_healthy

    def test_pass_increments_passed(self):
        score = HealthScore()
        score.add_result(
            CheckResult(
                id="TEST_OK",
                category="test",
                name="Test",
                status=CheckStatus.PASS,
                severity=CheckSeverity.LOW,
                summary="OK",
            )
        )
        assert score.passed == 1
        assert score.score == 100

    def test_info_increments_info(self):
        score = HealthScore()
        score.add_result(
            CheckResult(
                id="TEST_INFO",
                category="test",
                name="Test",
                status=CheckStatus.INFO,
                severity=CheckSeverity.LOW,
                summary="Info",
            )
        )
        assert score.info == 1
        assert score.score == 100

    def test_warning_low_penalty(self):
        score = HealthScore()
        score.add_result(
            CheckResult(
                id="TEST_WARN",
                category="test",
                name="Test",
                status=CheckStatus.WARNING,
                severity=CheckSeverity.LOW,
                summary="Low warning",
            )
        )
        assert score.warnings == 1
        assert score.score == 95  # 100 - 5

    def test_warning_medium_penalty(self):
        score = HealthScore()
        score.add_result(
            CheckResult(
                id="TEST_WARN",
                category="test",
                name="Test",
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                summary="Medium warning",
            )
        )
        assert score.warnings == 1
        assert score.score == 90  # 100 - 10

    def test_warning_high_penalty(self):
        score = HealthScore()
        score.add_result(
            CheckResult(
                id="TEST_WARN",
                category="test",
                name="Test",
                status=CheckStatus.WARNING,
                severity=CheckSeverity.HIGH,
                summary="High warning",
            )
        )
        assert score.warnings == 1
        assert score.score == 85  # 100 - 15

    def test_error_low_penalty(self):
        score = HealthScore()
        score.add_result(
            CheckResult(
                id="TEST_ERR",
                category="test",
                name="Test",
                status=CheckStatus.ERROR,
                severity=CheckSeverity.LOW,
                summary="Low error",
            )
        )
        assert score.errors == 1
        assert score.score == 95

    def test_error_medium_penalty(self):
        score = HealthScore()
        score.add_result(
            CheckResult(
                id="TEST_ERR",
                category="test",
                name="Test",
                status=CheckStatus.ERROR,
                severity=CheckSeverity.MEDIUM,
                summary="Medium error",
            )
        )
        assert score.errors == 1
        assert score.score == 90

    def test_error_high_penalty(self):
        score = HealthScore()
        score.add_result(
            CheckResult(
                id="TEST_ERR",
                category="test",
                name="Test",
                status=CheckStatus.ERROR,
                severity=CheckSeverity.HIGH,
                summary="High error",
            )
        )
        assert score.errors == 1
        assert score.score == 85

    def test_error_critical_penalty(self):
        score = HealthScore()
        score.add_result(
            CheckResult(
                id="TEST_ERR",
                category="test",
                name="Test",
                status=CheckStatus.ERROR,
                severity=CheckSeverity.CRITICAL,
                summary="Critical error",
            )
        )
        assert score.errors == 1
        assert score.score == 75  # 100 - 25

    def test_multiple_penalties(self):
        score = HealthScore()
        score.add_result(
            CheckResult(
                id="TEST1",
                category="test",
                name="Test",
                status=CheckStatus.ERROR,
                severity=CheckSeverity.HIGH,
                summary="Error 1",
            )
        )
        score.add_result(
            CheckResult(
                id="TEST2",
                category="test",
                name="Test",
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                summary="Warning 1",
            )
        )
        score.add_result(
            CheckResult(
                id="TEST3",
                category="test",
                name="Test",
                status=CheckStatus.PASS,
                severity=CheckSeverity.LOW,
                summary="Pass",
            )
        )
        assert score.score == 75  # 100 - 15 (error high) - 10 (warning medium)
        assert score.passed == 1
        assert score.warnings == 1
        assert score.errors == 1
        assert not score.is_healthy

    def test_score_clamped_at_zero(self):
        score = HealthScore()
        for i in range(20):
            score.add_result(
                CheckResult(
                    id=f"TEST_{i}",
                    category="test",
                    name="Test",
                    status=CheckStatus.ERROR,
                    severity=CheckSeverity.CRITICAL,
                    summary=f"Error {i}",
                )
            )
        assert score.score == 0

    def test_is_healthy(self):
        score = HealthScore()
        assert score.is_healthy
        score.add_result(
            CheckResult(
                id="TEST",
                category="test",
                name="Test",
                status=CheckStatus.ERROR,
                severity=CheckSeverity.HIGH,
                summary="Error",
            )
        )
        assert not score.is_healthy

    def test_details_populated(self):
        score = HealthScore()
        score.add_result(
            CheckResult(
                id="TEST",
                category="test",
                name="Test",
                status=CheckStatus.ERROR,
                severity=CheckSeverity.HIGH,
                summary="Test error",
            )
        )
        assert len(score.details) == 1
        assert "ERROR HIGH" in score.details[0]
        assert "Test error" in score.details[0]

    def test_skipped_increments_skipped(self):
        score = HealthScore()
        score.add_result(
            CheckResult(
                id="TEST_SKIP",
                category="test",
                name="Test",
                status=CheckStatus.SKIPPED,
                severity=CheckSeverity.LOW,
                summary="Skipped",
            )
        )
        assert score.skipped == 1
        assert score.score == 100
