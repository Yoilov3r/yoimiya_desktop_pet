from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageFilter


PROJECT = Path(__file__).resolve().parents[1]
OUTPUT = PROJECT / "assets" / "reaction_cards"
SOURCES = (
    (
        Path(r"C:\Users\yoimiya\Desktop\GPT creations\0dc47c42-1368-4c89-b0af-d060f808c2ca.png"),
        "collection2",
    ),
    (
        Path(r"C:\Users\yoimiya\Desktop\GPT creations\3fc95a0f-5612-4269-bef2-d6e66831073b.png"),
        "collection3",
    ),
)


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    count = 0
    for source_path, prefix in SOURCES:
        source = Image.open(source_path).convert("RGB")
        width, height = source.size
        panel_width = width / 3
        panel_height = height / 3
        for row in range(3):
            for column in range(3):
                left = round(column * panel_width) + 3
                top = round(row * panel_height) + 3
                right = round((column + 1) * panel_width) - 3
                bottom = round((row + 1) * panel_height) - 3
                panel = source.crop((left, top, right, bottom))
                panel = panel.resize((480, 480), Image.Resampling.LANCZOS)
                panel = panel.filter(
                    ImageFilter.UnsharpMask(radius=0.9, percent=52, threshold=3)
                )
                count += 1
                panel.save(
                    OUTPUT / f"{prefix}_{row * 3 + column + 1:02d}.png",
                    optimize=True,
                )
    print(f"Generated {count} borderless reaction cards.")


if __name__ == "__main__":
    main()
