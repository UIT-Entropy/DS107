from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class SessionTurn:
    question: str
    answer: str
    created_at: str


@dataclass(slots=True)
class AdvisorSession:
    session_id: str
    profile: dict[str, Any] = field(default_factory=dict)
    turns: list[SessionTurn] = field(default_factory=list)

    def recent_history(self, limit: int = 3) -> list[SessionTurn]:
        return self.turns[-limit:]

    def set_profile(self, profile: dict[str, Any]) -> None:
        cleaned = {key: value for key, value in profile.items() if value not in (None, "")}
        self.profile.update(cleaned)

    def add_turn(self, question: str, answer: str) -> None:
        self.turns.append(
            SessionTurn(
                question=question,
                answer=answer,
                created_at=datetime.now(timezone.utc).isoformat(),
            )
        )


def session_path(sessions_dir: Path, session_id: str) -> Path:
    safe_id = "".join(char for char in session_id if char.isalnum() or char in "-_")
    if not safe_id:
        raise ValueError("session_id khong hop le.")
    return sessions_dir / f"{safe_id}.json"


def session_to_dict(session: AdvisorSession) -> dict[str, Any]:
    return asdict(session)


def load_session(sessions_dir: Path, session_id: str) -> AdvisorSession:
    path = session_path(sessions_dir, session_id)
    if not path.exists():
        return AdvisorSession(session_id=session_id)

    data = json.loads(path.read_text(encoding="utf-8"))
    turns = [
        SessionTurn(
            question=str(turn.get("question", "")),
            answer=str(turn.get("answer", "")),
            created_at=str(turn.get("created_at", "")),
        )
        for turn in data.get("turns", [])
    ]
    return AdvisorSession(
        session_id=str(data.get("session_id", session_id)),
        profile=dict(data.get("profile", {})),
        turns=turns,
    )


def save_session(sessions_dir: Path, session: AdvisorSession) -> None:
    sessions_dir.mkdir(parents=True, exist_ok=True)
    path = session_path(sessions_dir, session.session_id)
    path.write_text(json.dumps(asdict(session), ensure_ascii=False, indent=2), encoding="utf-8")


def start_session(
    sessions_dir: Path,
    session_id: str,
    profile: dict[str, Any],
    overwrite: bool = False,
) -> AdvisorSession:
    path = session_path(sessions_dir, session_id)
    if path.exists() and not overwrite:
        session = load_session(sessions_dir, session_id)
    else:
        session = AdvisorSession(session_id=session_id)
    session.set_profile(profile)
    save_session(sessions_dir, session)
    return session


def list_sessions(sessions_dir: Path) -> list[dict[str, Any]]:
    if not sessions_dir.exists():
        return []

    rows = []
    for path in sorted(sessions_dir.glob("*.json")):
        session = load_session(sessions_dir, path.stem)
        created_at = session.turns[0].created_at if session.turns else ""
        updated_at = session.turns[-1].created_at if session.turns else ""
        rows.append(
            {
                "session_id": session.session_id,
                "disease": session.profile.get("disease") or session.profile.get("class_id") or "",
                "turn_count": len(session.turns),
                "created_at": created_at,
                "updated_at": updated_at,
                "path": str(path),
            }
        )
    return rows


def delete_session(sessions_dir: Path, session_id: str) -> bool:
    path = session_path(sessions_dir, session_id)
    if not path.exists():
        return False
    path.unlink()
    return True


def clear_sessions(sessions_dir: Path) -> int:
    if not sessions_dir.exists():
        return 0

    count = 0
    for path in sessions_dir.glob("*.json"):
        path.unlink()
        count += 1
    return count
