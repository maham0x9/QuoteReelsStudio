from PIL import Image

from app.models import TextLayer
from app.render.overlay import render_text_layer


def test_render_text_layer_returns_canvas_size():
    layer = TextLayer(text="Hello world", font_size=80, x=0.1, y=0.4,
                      width=0.8, height=0.2)
    img = render_text_layer(layer, (1080, 1920))
    assert isinstance(img, Image.Image)
    assert img.size == (1080, 1920)


def test_render_text_layer_handles_empty_text():
    layer = TextLayer(text="", font_size=64)
    img = render_text_layer(layer, (1080, 1920))
    assert img.size == (1080, 1920)
    # fully transparent
    assert img.getextrema()[3] == (0, 0)
