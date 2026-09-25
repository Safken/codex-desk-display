# Dashboard API v1

Both endpoints are read-only, served over trusted-LAN HTTP:

- `GET /api/status`: browser data plus service-reported date buckets and last attempt.
- `GET /api/display`: compact device payload (under 16 KiB required by firmware).
- `GET /healthz`: process liveness only, not upstream freshness.

No account login, API key, email, internal account hash, or transcript is returned.
Schema version is `1`. Numeric unavailable values are `null`, never invented zeroes.
Times are Unix seconds in UTC; `timezone` supplies the local calendar-day boundary.
`weekly.period_date_label` contains `MM/DD to MM/DD` in that timezone. Its start
is inferred as seven days before `resets_at`, the reported weekly reset endpoint;
it is independent of the collector's first observed reading. Token totals remain
observed/partial, even when the heading names the complete weekly window.

| Field | Meaning |
|---|---|
| `server_time` | Response-generation time, used with monotonic elapsed time for device countdowns |
| `state` | `fresh`, `stale`, or `unavailable` for weekly data |
| `updated_at`, `age_seconds` | Last successful weekly reading |
| `weekly` | `used_percent`, `remaining_percent`, `resets_at`, `reset_seconds`, `reset_local_label` (e.g. `9/24 @ 6:14pm`, using the collector's configured timezone and the reset date's daylight-saving offset) |
| `credits` | Optional Codex credit `balance` and `unlimited`; missing balance is null, not zero. Uses weekly reading freshness. |
| `today` | Local `date`, observed `points`, observed `tokens`, `observed_seconds`, `partial` |
| `period` | Current reset-window observed totals and `average_points_per_day` |
| `runway` | Estimated `seconds` or null, `reason`, optional `sample_hours`, `points_per_day`, `beyond_reset` |
| `lifetime_tokens` | Service-reported lifetime counter; coverage unverified |
| `tokens_updated_at`, `tokens_fresh` | Independent token freshness |
| `days` | Up to eight local-date rows for the current allowance period, newest first |
| `token_status` | Sanitized availability label from the optional token read |
| `demo` | True for explicitly synthetic preview data |
| `poll_seconds` | Upstream collection interval |
| `stale_seconds` | Freshness limit; clients also age data locally |

The display polls the local API every thirty seconds; Ubuntu polls the upstream
account every five minutes. A reachable dashboard does not imply successful
upstream collection. The device must age timestamps locally if polling stops.
After the reset timestamp passes, retain the old value as stale until a new
authoritative reading arrives; do not assume 100% remaining.

`/api/status` adds `last_attempt` (`at`, `status`) and `reported_daily_tokens`
(`date`, `tokens`, `updated`) with an explicit scope description.
The service ignores query parameters; no collection, login, purchase, or reset
can be triggered through HTTP. A new account identity starts a separate
calculation segment. A device must reject incompatible schema versions.
