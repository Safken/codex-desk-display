"""Persistence and conservative, observation-based usage calculations."""
from datetime import datetime, timezone
import json
import sqlite3
import time
from zoneinfo import ZoneInfo
from contextlib import contextmanager


def epoch(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()


class Store:
    def __init__(self, path):
        self.path = str(path)
        with self.connect() as db:
            db.executescript('''
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS readings(
                    ts REAL PRIMARY KEY, account TEXT NOT NULL, used REAL NOT NULL,
                    reset INTEGER NOT NULL, lifetime INTEGER, token_ts REAL);
                CREATE INDEX IF NOT EXISTS readings_window ON readings(account,reset,ts);
                CREATE TABLE IF NOT EXISTS daily_tokens(
                    account TEXT, day TEXT, tokens INTEGER, updated REAL,
                    PRIMARY KEY(account,day));
                CREATE TABLE IF NOT EXISTS state(key TEXT PRIMARY KEY, value TEXT);
            ''')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def record(self, result, now=None):
        now = time.time() if now is None else now
        with self.connect() as db:
            status = result.get("status", "collector_error")
            # Callers are the normalized probe; never persist raw upstream responses.
            db.execute('INSERT OR REPLACE INTO state VALUES (?,?)',
                       ('attempt', json.dumps({'at': now, 'status': status})))
            if status == 'ok' and result.get('weekly') and result.get('account_fingerprint'):
                w = result['weekly']
                summary = result.get('token_summary') or {}
                ts = epoch(result['weekly_observed_at'])
                db.execute('INSERT OR REPLACE INTO state VALUES (?,?)',
                           ('credits', json.dumps({'account': result['account_fingerprint'],
                            'ts': ts, 'value': result.get('credits')})))
                token_ts = epoch(result['tokens_observed_at']) if result.get('tokens_observed_at') else None
                lifetime = summary.get('lifetimeTokens')
                if type(lifetime) is not int or not 0 <= lifetime < 2**63:
                    lifetime = None
                db.execute('INSERT OR REPLACE INTO readings VALUES (?,?,?,?,?,?)',
                           (ts, result['account_fingerprint'], w['used_percent'],
                            int(epoch(w['resets_at'])), lifetime, token_ts))
                for bucket in result.get('daily_tokens') or []:
                    db.execute('INSERT OR REPLACE INTO daily_tokens VALUES (?,?,?,?)',
                               (result['account_fingerprint'], bucket['date'], bucket['tokens'], now))
                db.execute('INSERT OR REPLACE INTO state VALUES (?,?)',
                           ('token_status', json.dumps(result.get('token_status', 'unavailable'))))
            db.execute('DELETE FROM readings WHERE ts < ?', (now - 370 * 86400,))
            db.execute('DELETE FROM daily_tokens WHERE updated < ?', (now - 370 * 86400,))

    def status(self, now=None, tz='UTC', stale_seconds=900, poll_seconds=300):
        now = time.time() if now is None else now
        with self.connect() as db:
            latest = db.execute('SELECT * FROM readings ORDER BY ts DESC LIMIT 1').fetchone()
            state = {r['key']: json.loads(r['value']) for r in db.execute('SELECT * FROM state')}
            rows = []
            buckets = []
            if latest:
                rows = [dict(r) for r in db.execute(
                    'SELECT * FROM readings WHERE ts >= ? ORDER BY ts', (now - 8*86400,))]
                buckets = [dict(r) for r in db.execute(
                    'SELECT day AS date,tokens,updated FROM daily_tokens WHERE account=? ORDER BY day DESC LIMIT 7',
                    (latest['account'],))]
            result = calculate(rows, dict(latest) if latest else None, now, tz, stale_seconds, poll_seconds)
            result['last_attempt'] = state.get('attempt')
            credit_state = state.get('credits') or {}
            result['credits'] = (credit_state.get('value') if latest
                and credit_state.get('account') == latest['account']
                and credit_state.get('ts') == latest['ts'] else None)
            result['token_status'] = state.get('token_status', 'unavailable')
            result['reported_daily_tokens'] = buckets
            result['reported_daily_scope'] = 'Service date buckets; timezone and coverage unverified'
            return result


def calculate(rows, latest, now, tz, stale_seconds=900, poll_seconds=300):
    zone = ZoneInfo(tz)
    local_day = lambda ts: datetime.fromtimestamp(ts, zone).date().isoformat()
    result = {'schema_version': 1, 'server_time': now, 'timezone': tz,
              'source': 'Codex App Server', 'weekly': None, 'today': None,
              'period': None, 'runway': {'seconds': None, 'reason': 'collecting_history'},
              'lifetime_tokens': None, 'tokens_updated_at': None, 'tokens_fresh': False, 'days': [],
              'state': 'unavailable', 'updated_at': None, 'age_seconds': None}
    if not latest:
        return result
    age = max(0, now - latest['ts'])
    stale = age > stale_seconds or now >= latest['reset'] or latest['ts'] > now + 60
    result.update(state='stale' if stale else 'fresh', updated_at=latest['ts'], age_seconds=age)
    reset_local = datetime.fromtimestamp(latest['reset'], zone)
    start_local = datetime.fromtimestamp(latest['reset'] - 7*86400, zone)
    reset_label = (f"{reset_local.month}/{reset_local.day} @ "
                   f"{reset_local.hour % 12 or 12}:{reset_local.minute:02d}"
                   f"{'am' if reset_local.hour < 12 else 'pm'}")
    result['weekly'] = {'used_percent': latest['used'], 'remaining_percent': 100-latest['used'],
                        'resets_at': latest['reset'], 'reset_seconds': max(0, latest['reset']-now),
                        'reset_local_label': reset_label,
                        'period_date_label': f'{start_local:%m/%d} to {reset_local:%m/%d}'}
    # A new account never inherits previous account history. The latest continuous
    # identity segment also prevents mixing a switch-away-and-back interval.
    start = len(rows)-1
    while start > 0 and rows[start-1]['account'] == latest['account']:
        start -= 1
    rows = rows[start:] if rows else []
    tokens = [r for r in rows if r['lifetime'] is not None]
    if tokens:
        result['lifetime_tokens'] = tokens[-1]['lifetime']
        result['tokens_updated_at'] = tokens[-1]['token_ts'] or tokens[-1]['ts']
        result['tokens_fresh'] = 0 <= now-result['tokens_updated_at'] <= stale_seconds
    # Upstream reset timestamps can jitter by a second between polls. Keep
    # the latest contiguous window, allowing small timestamp rounding drift.
    window_start = len(rows)-1
    while window_start > 0 and abs(rows[window_start-1]['reset']-latest['reset']) <= 120:
        window_start -= 1
    window = rows[window_start:] if rows else []
    days = {}
    for r in window:
        day = local_day(r['ts'])
        days.setdefault(day, {'date': day, 'points': None, 'tokens': None,
                              'observed_seconds': 0, 'partial': True})
    period_tokens = None
    period_points = None
    period_seconds = 0
    tail = []
    for previous, current in zip(window, window[1:]):
        gap = current['ts']-previous['ts']
        valid = 0 < gap <= stale_seconds and current['used'] >= previous['used']
        if not valid:
            tail = []
            continue
        if not tail:
            tail = [previous]
        tail.append(current)
        delta = current['used']-previous['used']
        period_points = (period_points or 0) + delta
        period_seconds += gap
        token_delta = None
        if previous['lifetime'] is not None and current['lifetime'] is not None:
            token_gap = (current['token_ts'] or current['ts']) - (previous['token_ts'] or previous['ts'])
            if 0 < token_gap <= stale_seconds and current['lifetime'] >= previous['lifetime']:
                token_delta = current['lifetime']-previous['lifetime']
                period_tokens = (period_tokens or 0)+token_delta
        # Do not attribute a midnight-crossing interval to either local day.
        day = local_day(current['ts'])
        if day == local_day(previous['ts']):
            item = days[day]
            item['points'] = (item['points'] or 0)+delta
            item['observed_seconds'] += gap
            if token_delta is not None and local_day(current['token_ts'] or current['ts']) == local_day(previous['token_ts'] or previous['ts']) == day:
                item['tokens'] = (item['tokens'] or 0)+token_delta
    # Always label sums as observed, not reconstructed whole-day totals.
    result['days'] = list(sorted(days.values(), key=lambda d: d['date'], reverse=True))[:8]
    result['today'] = days.get(local_day(now), {'date': local_day(now), 'points': None,
                                              'tokens': None, 'observed_seconds': 0, 'partial': True})
    result['period'] = {'tokens': period_tokens, 'points': period_points,
                        'observed_seconds': period_seconds, 'partial': True,
                        'average_points_per_day': period_points/(period_seconds/86400) if period_seconds else None}
    tail = [r for r in tail if r['ts'] >= now-86400]
    if stale:
        result['runway']['reason'] = 'stale_data'
    elif latest['used'] == 100:
        result['runway'] = {'seconds': 0, 'reason': 'exhausted'}
    elif len(tail) >= 2 and tail[-1]['ts']-tail[0]['ts'] >= 6*3600:
        span = tail[-1]['ts']-tail[0]['ts']
        consumed = tail[-1]['used']-tail[0]['used']
        if consumed > 0:
            seconds = (100-latest['used']) * span/consumed
            result['runway'] = {'seconds': round(seconds), 'reason': 'estimate',
                                'points_per_day': consumed*86400/span,
                                'sample_hours': round(span/3600, 1),
                                'beyond_reset': seconds > latest['reset']-now}
        else:
            result['runway']['reason'] = 'no_measured_consumption'
    return result
