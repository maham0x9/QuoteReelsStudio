from app.config import get_config
from app.models import BackgroundOption, Project, Quote
from app.render.pipeline import RenderPipeline


def test_jobs_for_project_skips_quotes_without_background(tmp_path):
    cfg = get_config()
    pipe = RenderPipeline(cfg)
    p = Project(name="batch")
    q1 = Quote(text="one")
    q1.options.append(
        BackgroundOption(provider="pexels", video_id="1",
                         preview_url="", download_url="x", local_path="/tmp/clip.mp4")
    )
    q2 = Quote(text="two")  # no background
    p.quotes = [q1, q2]
    jobs = pipe.jobs_for_project(p, tmp_path / "out")
    assert len(jobs) == 1
    assert jobs[0].background_path == "/tmp/clip.mp4"
    assert jobs[0].canvas_size == (1080, 1920)
