from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest

from metrics import Store, calculate, epoch
from discovery import daily_tokens

NOW = epoch('2026-09-23T03:00:00Z')


def reading(ts, used=20, lifetime=1000, account='a', reset=None):
    return dict(ts=ts, used=used, lifetime=lifetime, token_ts=ts,
                account=account, reset=reset or NOW+2*86400)


def stats(rows, now=NOW):
    return calculate(rows, rows[-1] if rows else None, now, 'America/Los_Angeles')


class MetricsTests(unittest.TestCase):
    def test_period_dates_use_full_seven_day_window_in_local_timezone(self):
        for timestamp, expected in [('2026-09-25T01:14:00Z', '09/17 to 09/24'),
                                    ('2027-01-03T08:05:00Z', '12/27 to 01/03'),
                                    ('2026-11-03T08:05:00Z', '10/27 to 11/03')]:
            result = stats([reading(NOW, reset=epoch(timestamp))])
            self.assertEqual(result['weekly']['period_date_label'], expected)

    def test_reset_label_uses_configured_timezone_at_reset(self):
        for timestamp, expected in [('2026-09-25T01:14:00Z', '9/24 @ 6:14pm'),
                                    ('2026-12-25T08:05:00Z', '12/25 @ 12:05am'),
                                    ('2026-12-25T20:05:00Z', '12/25 @ 12:05pm')]:
            self.assertEqual(stats([reading(NOW, reset=epoch(timestamp))])['weekly']['reset_local_label'], expected)
        rows = [reading(NOW, reset=epoch('2026-09-25T01:14:00Z'))]
        self.assertEqual(calculate(rows, rows[-1], NOW, 'UTC')['weekly']['reset_local_label'], '9/25 @ 1:14am')

    def test_credits_persist_without_schema_change_and_clear_on_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            store = Store(Path(directory)/'usage.sqlite')
            sample = {'status': 'ok', 'account_fingerprint': 'a',
                      'weekly_observed_at': '2026-09-23T03:00:00Z',
                      'weekly': {'used_percent': 100, 'resets_at': '2026-09-25T03:00:00Z'},
                      'credits': {'balance': 123.75, 'unlimited': False}}
            store.record(sample, NOW)
            self.assertEqual(Store(store.path).status(NOW)['credits']['balance'], 123.75)
            store.record({'status': 'collector_error'}, NOW+1)
            self.assertEqual(store.status(NOW+1)['credits']['balance'], 123.75)
            sample['account_fingerprint'] = 'b'
            sample.pop('credits')
            store.record(sample, NOW)
            self.assertIsNone(store.status(NOW)['credits'])

    def test_first_sample_is_not_zero_usage(self):
        result = stats([reading(NOW)])
        self.assertIsNone(result['today']['points'])
        self.assertIsNone(result['today']['tokens'])
        self.assertIsNone(result['runway']['seconds'])

    def test_observed_delta_and_lifetime(self):
        result = stats([reading(NOW-300, 20, 1000), reading(NOW, 22, 1400)])
        self.assertEqual(result['today']['points'], 2)
        self.assertEqual(result['today']['tokens'], 400)
        self.assertEqual(result['lifetime_tokens'], 1400)
        self.assertTrue(result['today']['partial'])

    def test_gap_and_counter_drop_are_not_consumption(self):
        result = stats([reading(NOW-3600, 20, 2000), reading(NOW, 25, 2500)])
        self.assertIsNone(result['period']['tokens'])
        result = stats([reading(NOW-300, 20, 2000), reading(NOW, 10, 1500)])
        self.assertIsNone(result['period']['points'])
        self.assertIsNone(result['period']['tokens'])

    def test_token_correction_does_not_affect_allowance(self):
        result = stats([reading(NOW-300, 20, 2000), reading(NOW, 22, 1500)])
        self.assertEqual(result['today']['points'], 2)
        self.assertIsNone(result['today']['tokens'])

    def test_midnight_boundary_is_not_assigned_to_today(self):
        midnight = epoch('2026-09-23T07:00:00Z')
        result = stats([reading(midnight-60, 20), reading(midnight+60, 22, 2000)], midnight+60)
        self.assertIsNone(result['today']['points'])
        self.assertEqual(result['period']['points'], 2)

    def test_dst_fallback_day_is_one_local_date(self):
        times = [epoch('2026-11-01T08:59:00Z'), epoch('2026-11-01T09:01:00Z')]
        rows = [reading(t, 20+i, 1000+i*100, reset=times[-1]+86400) for i,t in enumerate(times)]
        self.assertEqual(stats(rows, times[-1])['today']['points'], 1)

    def test_reset_and_account_switch_break_history(self):
        rows = [reading(NOW-300, 80, reset=NOW+500), reading(NOW, 2)]
        self.assertIsNone(stats(rows)['period']['points'])
        rows = [reading(NOW-300, 20, account='a'), reading(NOW, 30, account='b')]
        self.assertIsNone(stats(rows)['period']['points'])

    def test_reset_timestamp_jitter_preserves_usage(self):
        rows = [reading(NOW-300, 20, 1000, reset=NOW+86400),
                reading(NOW, 21, 1200, reset=NOW+86401)]
        self.assertEqual(stats(rows)['today']['points'], 1)
        self.assertEqual(stats(rows)['today']['tokens'], 200)

    def test_reset_change_never_joins_noncontiguous_windows(self):
        rows = [reading(NOW-600, 20, 1000),
                reading(NOW-300, 21, 1100, reset=NOW+86400),
                reading(NOW, 22, 1200)]
        self.assertIsNone(stats(rows)['today']['points'])

    def test_runway_minimum_and_estimate(self):
        rows = [reading(NOW-6*3600+i*300, 20+i/12, 1000+i*100) for i in range(73)]
        result = stats(rows)
        self.assertAlmostEqual(result['runway']['points_per_day'], 24)
        self.assertEqual(result['runway']['seconds'], 74*3600)
        self.assertTrue(result['runway']['beyond_reset'])
        self.assertIsNone(stats(rows[1:])['runway']['seconds'])

    def test_stale_and_expired_windows(self):
        rows = [reading(NOW-1000)]
        self.assertEqual(stats(rows)['state'], 'stale')
        rows = [reading(NOW, reset=NOW-1)]
        self.assertEqual(stats(rows)['state'], 'stale')
        self.assertEqual(stats(rows)['weekly']['reset_seconds'], 0)

    def test_zero_pace_is_not_infinite(self):
        rows = [reading(NOW-6*3600+i*300) for i in range(73)]
        result = stats(rows)
        self.assertIsNone(result['runway']['seconds'])
        self.assertEqual(result['runway']['reason'], 'no_measured_consumption')

    def test_missing_tokens_never_become_zero(self):
        result = stats([reading(NOW-300, lifetime=None), reading(NOW, lifetime=None)])
        self.assertIsNone(result['lifetime_tokens'])
        self.assertIsNone(result['today']['tokens'])

    def test_daily_source_buckets_are_strict_and_separate(self):
        self.assertEqual(daily_tokens({'dailyUsageBuckets':[{'startDate':'2026-09-22','tokens':0}]}),
                         [{'date':'2026-09-22','tokens':0}])
        self.assertIsNone(daily_tokens({'dailyUsageBuckets':[{'startDate':'2026-02-30','tokens':2}]}))
        self.assertIsNone(daily_tokens({'dailyUsageBuckets':[{'startDate':'2026-09-22','tokens':True}]}))

    def test_retention_prunes_on_failed_collection(self):
        with tempfile.TemporaryDirectory() as folder:
            store = Store(Path(folder)/'history.sqlite')
            with store.connect() as db:
                db.executemany('INSERT INTO readings VALUES (?,?,?,?,?,?)', [
                    (NOW-371*86400,'a',1,NOW+86400,100,NOW-371*86400),
                    (NOW-369*86400,'a',2,NOW+86400,200,NOW-369*86400)])
            store.record({'status':'app_server_timeout'},now=NOW)
            with store.connect() as db:
                self.assertEqual(db.execute('SELECT count(*) FROM readings').fetchone()[0],1)
                self.assertEqual(db.execute('SELECT used FROM readings').fetchone()[0],2)

    def test_sqlite_restart_failure_and_redaction(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'test.sqlite'
            store = Store(path)
            sample = {'status':'ok','account_fingerprint':'PRIVATE_ID',
                      'weekly_observed_at':datetime.fromtimestamp(NOW,timezone.utc).isoformat(),
                      'tokens_observed_at':datetime.fromtimestamp(NOW,timezone.utc).isoformat(),
                      'weekly':{'used_percent':89,'resets_at':datetime.fromtimestamp(NOW+86400,timezone.utc).isoformat()},
                      'token_summary':{'lifetimeTokens':8_000_000_000}, 'token_status':'reported_scope_unverified'}
            store.record(sample, now=NOW)
            Store(path).record({'status':'app_server_timeout'}, now=NOW+300)
            result = Store(path).status(now=NOW+301)
            self.assertEqual(result['weekly']['remaining_percent'], 11)
            self.assertEqual(result['updated_at'], NOW)
            self.assertEqual(result['last_attempt']['status'], 'app_server_timeout')
            self.assertNotIn('PRIVATE_ID', json.dumps(result))


if __name__ == '__main__':
    unittest.main()
