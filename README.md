# MiddleClick Terminal 🖱️

A lightweight, high-performance Python utility for macOS that maps a **three-finger trackpad tap** to a **middle mouse click**.

Built using the private `MultitouchSupport.framework` for raw trackpad access and `CoreGraphics` for precise mouse event synthesis.

## Features
- **Zero Configuration**: Just run and tap.
- **Gesture Filtering**: Intelligently distinguishes between a tap and a 3-finger swipe (so you don't lose your system gestures).
- **Extremely Lightweight**: Near-zero CPU and RAM usage.
- **Native Performance**: Uses raw system calls for minimal latency.

## Prerequisites
- **macOS** (Tested on Monterey, Ventura, Sonoma, and Sequoia).
- **Python 3** (Standard on macOS).
- **Accessibility Permissions**: Required to inject mouse events.

## Installation & Usage

1.  **Download the script**:
    ```bash
    curl -O https://raw.githubusercontent.com/nullpratham/middleclickTerminal/main/middleclick.py
    ```

2.  **Run the script**:
    ```bash
    python3 middleclick.py
    ```

3.  **Grant Permissions**:
    - The first time you run it, macOS will ask for **Accessibility** permissions. 
    - Go to **System Settings > Privacy & Security > Accessibility** and toggle the switch for your terminal (e.g., Terminal or iTerm2).

4.  **Try it out**:
    Quickly tap three fingers on your trackpad.

## Credits
Originally developed as part of a native macOS utility research.
