from advisor.core.session import AdvisorSession, load_session, save_session


def test_session_round_trip(tmp_path):
    session = AdvisorSession(session_id="field-1")
    session.add_turn("Cây bị vàng lá?", "Cần kiểm tra rễ và vết bệnh.")

    save_session(tmp_path, session)
    loaded = load_session(tmp_path, "field-1")

    assert loaded.session_id == "field-1"
    assert loaded.turns[0].question == "Cây bị vàng lá?"
    assert loaded.recent_history(limit=1)[0].answer == "Cần kiểm tra rễ và vết bệnh."
