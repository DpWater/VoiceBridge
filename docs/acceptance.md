# Acceptance and test plan

Automated tests cover configuration persistence, PCM WAV construction, workflow transitions, overlapping task rejection, cancellation, and an ASR→LLM mock integration.

Manual acceptance still required on each supported OS:

- grant microphone permission and record a Chinese/English mixed instruction;
- install a licensed faster-whisper model and confirm real transcription;
- configure a user-owned LLM key and verify faithful correction;
- check review editing, copy, Escape cancellation, and clipboard output;
- only after implementation, test global shortcut and GUI automation with OS accessibility permissions.

No mock test is evidence that macOS/Windows audio, model inference, or global shortcuts work on a given machine.
