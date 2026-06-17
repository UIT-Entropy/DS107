from advisor.core.session import (
    AdvisorSession,
    clear_sessions,
    delete_session,
    list_sessions,
    save_session,
    start_session,
)


def test_session_management_helpers(tmp_path):
    session = AdvisorSession(session_id="ruong-a")
    session.add_turn("Hỏi gì?", "Trả lời.")
    save_session(tmp_path, session)

    rows = list_sessions(tmp_path)
    assert rows[0]["session_id"] == "ruong-a"
    assert rows[0]["turn_count"] == 1

    assert delete_session(tmp_path, "ruong-a") is True
    assert delete_session(tmp_path, "ruong-a") is False

    save_session(tmp_path, session)
    assert clear_sessions(tmp_path) == 1
    assert list_sessions(tmp_path) == []


def test_start_session_stores_yolo_profile(tmp_path):
    session = start_session(
        tmp_path,
        "ruong-a",
        {
            "source": "yolo",
            "disease": "rầy nâu",
            "class_id": "brown_plant_hopper",
            "confidence": 0.91,
        },
    )

    assert session.profile["source"] == "yolo"
    assert session.profile["disease"] == "rầy nâu"
    assert list_sessions(tmp_path)[0]["disease"] == "rầy nâu"
