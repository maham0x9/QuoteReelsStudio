from pathlib import Path

from app.config import AppConfig
from app.models import Project, Quote
from app.store import ProjectStore, TemplateStore


def _cfg(tmp_path: Path) -> AppConfig:
    cfg = AppConfig()
    cfg.projects_dir = str(tmp_path / "projects")
    cfg.cache_dir = str(tmp_path / "cache")
    return cfg


def test_project_store_save_load_recent(tmp_path):
    cfg = _cfg(tmp_path)
    store = ProjectStore(cfg)
    p = Project(name="My Reels", quotes=[Quote(text="hello")])
    path = store.save(p)
    assert path.exists()
    loaded = store.load(path)
    assert loaded.name == "My Reels"
    assert loaded.quotes[0].text == "hello"
    assert any(e["id"] == p.id for e in store.recent())


def test_template_store_seeds_defaults(tmp_path):
    cfg = _cfg(tmp_path)
    store = TemplateStore(cfg)
    presets = store.list()
    assert len(presets) >= 1
    assert any("Bold" in p.name for p in presets)
