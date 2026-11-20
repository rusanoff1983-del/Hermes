# Antigravity Direct — profile-local multi-account provider

## Multi-account routing

- Each connected Google account gets its own provider row in the existing model picker: `Antigravity Direct · Основной`, `Antigravity Direct · Второй`, etc. The primary provider ID stays `antigravity-direct`; other IDs are `antigravity-direct-a<32 hex digits>`.
- Provider IDs are immutable routing identity; display labels can change. Every client binds one account, so simultaneous sessions cannot switch each other's account. Plain/legacy model IDs under `antigravity-direct` always route to `primary`; missing/unknown accounts fail, never fall back to another account.
- Reviewed model catalogs are scoped per provider; every row includes the full maintained fallback catalog for the desktop's cold/no-network picker. Fallback catalog entries are candidates, not proof of availability for an individual account.
- Optional explicit model assertion `MODEL@ag:ACCOUNT_ID` must match the selected provider. Malformed tags, mismatched account IDs and unsupported model IDs fail closed.
- The versioned account store is `plugin-data/antigravity-direct/accounts.dpapi`, encrypted with current-user Windows DPAPI. Legacy `credential.dpapi` migrates to `primary`/`Основной` on first local read; legacy encrypted file is preserved for rollback until primary logout. Corrupt/new-format stores never silently fall back to the legacy file.
- Atomic writes and Windows OS byte-range locking coordinate migration, writes and refresh across processes. Refresh updates only the selected credential, preserves project identity, and preserves refresh tokens when Google omits a replacement.
- Google userinfo `sub` identifies accounts. Login under an existing label with a different Google identity, or the same identity under another label, is rejected without overwriting credentials. A migrated primary identity is verified using its own token before adding another account. Labels are never used as credential paths or routing keys.

### Commands (do not run until ready to log in)

```text
hermes auth add antigravity-direct --label "Второй" --no-browser --timeout 600
hermes auth status antigravity-direct
hermes auth logout antigravity-direct-a<account-id-hex>
```

`--no-browser` prints the actual Google OAuth URL and never auto-opens a browser. Open that URL in the browser containing the desired Google account. The callback listener is still local port 51121; only one pending login can use it. URL printing contains PKCE/state/client ID but not the client secret or tokens. `hermes auth add` also registers the account-specific nonsecret pool marker; it does not change the active provider/model.

Local commands with the managed Hermes Python interpreter:

```text
python direct.py accounts
python direct.py rename --account a<32 hex digits> --label "Рабочий"
```

Rename preserves the provider ID. Restart the desktop backend/application after adding an account or renaming it so loaded provider rows and cached picker names refresh. No core, config.yaml, global model or other profile changes are required. Only accounts that have actually completed login appear; this implementation does not create a fake second account.

### Verification

`python -m unittest discover -s <plugin-directory> -p "test_*.py" -v` runs existing protocol tests plus synthetic account fixtures using real Windows DPAPI and real two-process refresh locking. Tests cover token/project isolation, bound-client transport routing, duplicate identities, migrated-primary safeguards, unknown/malformed routing, rename/logout, no-browser URL/CLI-hook forwarding, and cold fallback catalogs. OAuth/network transport is mocked in these tests; no real second-account OAuth is started by tests. `hermes plugins validate <plugin-directory>` checks manifest/import/security. Real login, second-account inventory and desktop click-through still require separate verification.

## Earlier single-account verification record


Location: user-state plugins/antigravity-direct; core and agy provider unchanged.

## Verified locally
- `hermes plugins validate <this directory>`: Validation passed, security scan safe.
- Historical test count above predates multi-account tests; use the current suite for verification.
- `direct.py status`: public OAuth configuration and wire library available, not signed in before launch.
- `hermes auth add antigravity-direct`: launched, reports waiting for Google login.

## Current next step / blocker
Browser OAuth completed successfully; encrypted credential and routing marker persisted.
Verified live `direct.py probe` returned `OK`.
Verified full Hermes one-shot returned `HERMES_DIRECT_OK` using:
`hermes chat --provider antigravity-direct -m gemini-3.8-flash-low -q 'Reply exactly HERMES_DIRECT_OK. Do not use tools.' --oneshot -Q --ignore-rules --ignore-user-config --max-turns 1 --run-budget 120 --source tool`
Session receipt: 20261001_211241_f6829b.
Current default/model unchanged. Live two-request tool roundtrip passed: echo_test called with verified argument, native assistant replay retained, final reply `DIRECT_TOOL_OK` (`probe_tools.py`). Remaining: desktop login control, progressive streaming, Claude/other models and measured comparison against agy.

## Scope and limitations
- Maintained text/function-tool catalog covers Gemini, Claude and GPT-OSS; per-account availability must be verified live. Images/video/search are not implemented.
- Direct Cloud Code Assist transport uses @cortexkit/antigravity-auth-core exactly 2.2.0, as used by DSH 0.1.4-rc.5. Node helper is protocol transport, not agy CLI or an autonomous agent.
- Streams are buffered before producing OpenAI-compatible chunks, not progressive.
- No desktop button yet. CLI browser entry is real, not a placeholder notification.
- Tokens now stored in `accounts.dpapi` with legacy migration, as described above; Hermes pools contain only nonsecret per-account routing markers.
- Refresh now uses an OS cross-process account-store lock (verified with two synthetic processes). Cancellation propagation remains hardening work.
- No foreign-app token migration, no default/fallback project, no automatic onboarding.
- Direct unofficial API may reject/change. Live account and latency comparison remain unverified.
- Imported MIT dependency license: node_modules/@cortexkit/antigravity-auth-core/LICENSE. Protocol reference https://github.com/suntianc/dsh-antigravity-auth . No upstream source copied into production files.

Failed prior generated provider/UI were quarantined under backups/antigravity-direct-rejected.

## Commands
`hermes auth add antigravity-direct` — open browser, wait callback, exchange token, discover own project, persist encrypted credential, add routing marker.
`hermes auth status antigravity-direct` — local presence only, not live health.
`hermes auth logout antigravity-direct` — delete local credential and routing marker; no remote revoke.
`direct.py probe` under managed Hermes Python — actual model probe, requires login.

## Transport deadline regression verification (2026-10-14)

Adapter-only fix: response-header and body-idle waits are now 120 seconds,
Node total deadline 300 seconds, Python helper deadline 330 seconds. The
header wait includes backend inference/prefill, not merely network RTT.
Hermes run-budget/stale watchdogs can still end a call sooner; use an explicit
sufficient one-shot budget when diagnosing. No core, config, model, routing,
account identity, OAuth, DPAPI, or native replay changes were made for this fix.

Transport failures now expose only allowlisted class/code/phase and numeric
elapsed time. Raw exception text, stack, stderr, tokens, project IDs, prompts,
and native signatures are not logged by these diagnostics. Codes distinguish
connect/header/idle/total/process timeout, resets, malformed helper/response,
and response-size limit. Existing HTTP status handling is unchanged.

Live evidence, both accounts, same recorded Gemini high request:
- Replayed the read-only request dump ending `170125_447842.json`: 186
  messages, 653,403-byte adapted payload, actual backend prompt 102,881 tokens.
  These were actual historical messages/tools/native signatures, not a
  synthetic stress fixture. No returned tool was executed.
- Before: both accounts failed with `HEADER_TIMEOUT`, phase `headers`, zero
  response bytes, at 30,135/30,138 ms.
- After: HTTP 200; headers arrived at 47,007/49,911 ms. The unchanged request
  itself ended `MAX_TOKENS` without visible text: transport repair does not
  imply that every historical continuation generates an answer.
- A separately labeled replay variant appended a harmless no-tool marker
  instruction and used a 32,768-token output budget. It returned exactly
  `LONG_CONTEXT_REPLY_OK`, `stop`, with 102,917 prompt tokens; 187 messages,
  653,614-byte payload. This is not claimed as an exact replay.
- Full Hermes one-shot, second provider
  `antigravity-direct-ab728cbd2a0344c5c8f1ed496865478ce`, same high model:
  all 240 requested numbered Unicode lines verified, 14,400 output characters,
  3,119 completion tokens, session `20261014_172629_02503b`, exit 0.
- Live harmless echo roundtrips passed on both accounts with native
  `thoughtSignature` present/replayed and final `DIRECT_TOOL_OK`.
- Offline suite: 35 tests (including real DPAPI/cross-process account tests,
  Node injected transport errors, secret-redaction sentinels, timeout hierarchy,
  and byte-split UTF-8). Manifest/import/security validation passed.

Receipts, backups, and scripts are under the active profile's
`cache/scratch/ag-transport-1791958287/`: `before.json`, `after.json`,
`long-context-variant.json`, `hermes-result.json`, `live.json`,
`unit-tests-final.txt`. Original failed provider-id typo probes are retained there as
excluded verification-command failures, not transport failures.

Progressive streaming is **not** implemented: responses are still buffered,
with an 8 MiB decoded response limit. Cancellation propagation remains a
limitation. An already-imported Python provider needs a desktop/backend restart
to pick up its new process deadline and diagnostic code; this repair does not
autonomously restart an active chat. Fresh CLI runs use the new code.

---

## What's new in 0.3.0 (2026-11-21)

### 1. Authorization taken from the Antigravity IDE itself
The plugin no longer relies on its own OAuth grant. It reads the live session from
Windows Credential Manager (`gemini:antigravity`) — the one registered by the Antigravity
IDE — and refreshes it with the IDE's own `client_id`/`client_secret`. Nothing to log in
by hand, the token does not expire.

For accounts that are ineligible for third-party OAuth clients (Google returns
`Client is not eligible for Gemini Code Assist for individuals`), this is the way in.

### 2. Token refresh goes through the VPS proxy
`ANTIGRAVITY_PROXY` (CONNECT proxy, e.g. `http://10.66.66.1:3128`) is used both for API
calls and for the token refresh. Direct requests to Google from some ISPs get cut with
`tls: bad record MAC`, and some regions get `User location is not supported`.

### 3. `systemInstruction` limit workaround (the main cause of 429)
Google Cloud Code Assist rejects a `systemInstruction` longer than roughly 2500 characters
with `429 RESOURCE_EXHAUSTED`, even though the same request with a short prompt returns
200. A real agent prompt (rules + memory + tool descriptions) is ~33 KB, so every request
failed while probes passed.

Fix: when the combined system instructions exceed 1500 characters they are packed into the
first user message as `<system_instructions>...</system_instructions>` and the
`systemInstruction` field is not sent at all.

### 4. 429 is retried instead of failing the turn
A 429 is treated as a burst-window limit: the plugin waits 8 s, 16 s and 30 s and retries,
and only raises after ~54 s. The user gets an answer instead of an error.

> The `client_id`/`client_secret` used for the token refresh are the Antigravity IDE's own
> desktop-OAuth credentials — they ship inside the IDE binary itself, so they are not a private
> secret. They can be overridden with `ANTIGRAVITY_IDE_CLIENT_ID` / `ANTIGRAVITY_IDE_CLIENT_SECRET`.
