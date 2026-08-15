# Snake Game (Python + C++ engine)

A classic snake game with a **C++ rendering engine** exposed to Python via `ctypes`.

## Requirements

- Python 3.8+
- pygame

```bash
pip install -e .
python game.py
```

## Build

The C++ engine (`engine.cpp`) is compiled to `libengine.so`:

```bash
python setup.py build_ext --inplace
```

## Layout

- `game.py` — main game loop and UI
- `engine.cpp` / `libengine.so` — native acceleration
