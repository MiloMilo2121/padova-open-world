# Padova 2 multiplayer preview

This is an isolated development preview. It does not deploy or modify the live game.
Requires Node 24 and npm. From the repository root:

```sh
npm ci
npm run server
# Second terminal:
npm run dev -- --port 5174 --strictPort
```

Open http://127.0.0.1:5174, select **Play with friends**, use
`ws://127.0.0.1:8787` and the same room code on each client. Room codes contain
3–12 letters/digits. Up to 32 cars share a room. Leaving returns to single-player.
The current online mode supports the MiTo-inspired car; on-foot play, missions,
traffic and police are not yet authoritative multiplayer systems.

`npm run test:load` opens 32 real TCP/WebSocket clients for 20 seconds. It fails
on premature disconnects, unbounded input backlog, insufficient snapshots or a
server tick p99 above 16.67 ms. Results go to `docs/multiplayer-load.json`.
This is a loopback test, not proof of internet latency or rendering performance.

## Server configuration

- `HOST`: defaults to `127.0.0.1` (local only).
- `PORT`: defaults to `8787`.
- `ALLOWED_ORIGINS`: comma-separated exact browser origins. Defaults permit the
  documented local development/preview URLs.
- `GET /health`: protocol, room count and player count.
- `GET /metrics`: recent tick timing, players and bytes sent in active rooms.

For a later separate internet preview, place the server behind a TLS reverse
proxy, use a `wss://` endpoint and set the exact preview origin. Do not point the
existing live site at this server. Room codes are discovery identifiers, not
passwords; this preview has no account authentication. The process limits itself
to 128 players, 16 rooms, 32 per room, bounded messages and outbound buffering.
No hosting resource or public server has been provisioned by this change.

## Protocol and authority

Clients send only input and sequence/ack fields. Server-owned movement uses the
same collision and driving modules as client prediction, at 60 Hz. Snapshots run
at 20 Hz, with full-precision self state, packed remote state, spatial interest
filtering and a maximum 487-byte payload for 32 cars. Full snapshots are currently
sent: acknowledged-baseline delta compression remains future work.

The client replays unacknowledged input and decays visual corrections over 120 ms.
Remote interpolation uses a 125 ms buffer and Hermite position interpolation.
Automated tests cover missing/delayed snapshots; public-network trials, long
sessions and player-versus-player collision tuning remain qualification work.
