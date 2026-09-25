from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock, patch

from metrics import Store
from monitor import collect


class StopAfter:
    def __init__(self, count):
        self.count = count
        self.waits = []

    def is_set(self):
        return len(self.waits) >= self.count

    def wait(self, seconds):
        self.waits.append(seconds)


class CollectorTests(unittest.TestCase):
    def test_outage_backoff_stale_recovery_and_restart(self):
        start = 1893456000
        clock = [start]
        def sample(used, tokens):
            stamp = datetime.fromtimestamp(clock[0], timezone.utc).isoformat()
            return dict(status='ok', account_fingerprint='private-fixture',
                        weekly_observed_at=stamp, tokens_observed_at=stamp,
                        weekly=dict(used_percent=used, resets_at=datetime.fromtimestamp(start+86400, timezone.utc).isoformat()),
                        token_summary=dict(lifetimeTokens=tokens))
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'history.sqlite'
            store = Store(path)
            store.record(sample(20, 1000), now=start)
            clock[0] += 1800
            stop = StopAfter(2)
            with patch('monitor.probe', new=AsyncMock(side_effect=[RuntimeError('SECRET'), {'status':'app_server_timeout'}])), patch('metrics.time.time', side_effect=lambda: clock[0]):
                collect(store, dict(codex='fake',poll_seconds=300), stop)
            self.assertEqual(stop.waits, [600,1200])
            outage = store.status(now=clock[0])
            self.assertEqual(outage['state'], 'stale')
            self.assertEqual(outage['updated_at'], start)
            self.assertEqual(outage['lifetime_tokens'], 1000)
            self.assertFalse(outage['tokens_fresh'])
            self.assertNotIn('SECRET', str(outage))
            with patch('monitor.probe', new=AsyncMock(return_value=sample(25, 2000))), patch('metrics.time.time', side_effect=lambda: clock[0]):
                recovered_stop = StopAfter(1)
                collect(store, dict(codex='fake',poll_seconds=300), recovered_stop)
            recovered = Store(path).status(now=clock[0])
            self.assertEqual(recovered['state'], 'fresh')
            self.assertEqual(recovered_stop.waits, [300])
            self.assertEqual(recovered['weekly']['used_percent'], 25)
            self.assertIsNone(recovered['today']['tokens'])  # Outage gap is not invented usage.
            self.assertEqual(recovered['lifetime_tokens'], 2000)

    def test_backoff_is_bounded(self):
        stop = StopAfter(8)
        with patch('monitor.probe',new=AsyncMock(return_value={'status':'app_server_timeout'})):
            from unittest.mock import Mock
            collect(Mock(),dict(codex='fake',poll_seconds=600),stop)
        self.assertEqual(stop.waits,[1200,2400,3600,3600,3600,3600,3600,3600])
