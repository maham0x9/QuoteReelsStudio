from app.models import BackgroundOption, Project, Quote, TextLayer, VideoSettings


def test_project_round_trip():
    q = Quote(text="Stay hungry, stay foolish.")
    q.text_layer.text = q.text
    q.video.duration = 10.0
    q.options.append(BackgroundOption(provider="pexels", video_id="1",
                                      preview_url="", download_url="x"))
    p = Project(name="Demo", quotes=[q])
    d = p.to_dict()
    p2 = Project.from_dict(d)
    assert p2.name == "Demo"
    assert p2.quotes[0].text == q.text
    assert p2.quotes[0].text_layer.text == q.text
    assert p2.quotes[0].options[0].provider == "pexels"
    assert p2.quotes[0].video.duration == 10.0


def test_text_layer_defaults_serialize():
    layer = TextLayer(text="hi")
    layer2 = TextLayer.from_dict(layer.to_dict())
    assert layer2 == layer


def test_video_settings_defaults_serialize():
    v = VideoSettings(duration=12, music_path="x.mp3")
    v2 = VideoSettings.from_dict(v.to_dict())
    assert v2 == v
