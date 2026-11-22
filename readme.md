# Kinetic Kombat

A real-time, motion-controlled 2D fighting game built in Python using **Pygame**, **OpenCV**, and **MediaPipe**. Players control their fighter physically in front of a standard webcam using punches, kicks, and blocks—with a live picture-in-picture skeleton overlay and keyboard fallbacks.

## Features
- **Real-Time Skeletal Tracking:** Uses MediaPipe Pose (`model_complexity=0`) with frame downscaling for responsive edge performance.
- **Trigonometric Pose Engine:** Calculates joint angles (`math.atan2`) and relative landmark heights to classify punches, kicks, and guards with mutually exclusive state checks to reduce false positives.
- **2D Combat & CPU AI:** Includes hitbox collision detection, block damage reduction, randomized CPU opponent behavior, health bars, start/game-over loops with replay support, and `.wav` sound effects.
- **Keyboard Fallbacks:** Supports keyboard controls alongside webcam input for quick testing or play without a camera.

## Project Structure
```text
kinetic-kombat/
├── game.py
├── requirements.txt
├── .gitignore
└── assets/
    ├── bg.jpg
    ├── sprites/
    │   ├── player1/
    │   │   ├── idle/0.png
    │   │   ├── punch/0.png
    │   │   ├── kick/0.png
    │   │   └── block/0.png
    │   └── player2/
    │       ├── idle/0.png
    │       ├── punch/0.png
    │       ├── kick/0.png
    │       └── block/0.png
    └── sfx/
        ├── attack.wav
        ├── win.wav
        └── lose.wav
```

## Installation & Setup
1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/kinetic-kombat.git
   cd kinetic-kombat
   ```
2. **Create and activate a virtual environment (recommended):**
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # macOS/Linux:
   source .venv/bin/activate
   ```
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Run the game:**
   ```bash
   python game.py
   ```

## Controls

### Webcam Motions
- **Guard (Block):** Raise both wrists near/above shoulder height (`rw.y < rs.y + 30` and `lw.y < ls.y + 30`).
- **Punch:** Extend your right arm (`elbow_angle > 150°`) with your right wrist above hip level (`rw.y < rh.y`), then retract below `100°` to reset.
- **Kick:** Raise your right ankle closer to hip height (`ra.y - rh.y < 120` px), then lower it back down to reset.

### Keyboard Controls
- **Start / Replay:** `SPACE`
- **Quit Menu:** `ESC`
- **Move Left / Right:** `A` / `D`
- **Punch / Kick / Block:** `J` / `K` / `L`

## Tech Stack
- **Python**
- **Pygame** (game loop, rendering, hitboxes, UI, `.wav` audio)
- **OpenCV** (`cv2`) (webcam capture, mirroring, resizing, color conversion)
- **MediaPipe** (33-landmark pose estimation)
- **NumPy & Math** (frame array conversion and angle calculations)