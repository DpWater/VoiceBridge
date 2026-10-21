# Workflow state machine

```text
IDLE → RECORDING → TRANSCRIBING → [ENHANCING] → REVIEWING → DISPATCHING → COMPLETED
          │              │              │           │             │
          └──────────────┴──────────────┴───────────┴─────────────┴→ CANCELLED / FAILED
```

Every task receives a UUID. There is one worker and one active task; asynchronous callbacks compare their task ID before changing UI state. With enhancement disabled, transcription goes directly to review. If enhancement fails, the original transcription is retained for review.
