from argparse import Namespace

from advisor.cli import run_sessions
from advisor.config import load_config
from advisor.core.session import load_session


def test_sessions_start_accepts_class_id_only(tmp_path, capsys):
    config = load_config(sessions_dir=tmp_path)
    args = Namespace(
        session_command="start",
        session_id="ruong-a",
        class_id="brown_plant_hopper",
        disease="",
        confidence=0.91,
        image="",
        crop_stage="",
        location="",
        notes="",
        source="yolo",
        overwrite=False,
        json=False,
    )

    run_sessions(args, config)

    session = load_session(tmp_path, "ruong-a")
    assert session.profile["class_id"] == "brown_plant_hopper"
    assert session.profile["disease"] == "rầy nâu"
    assert "Class ID: brown_plant_hopper" in capsys.readouterr().out
