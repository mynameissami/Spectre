# Contributing to S.P.E.C.T.R.E. Engine OS

First off, thank you for considering contributing to S.P.E.C.T.R.E. Engine OS! It's people like you that make open-source platforms powerful and secure.

## 🤝 How Can I Contribute?

### Reporting Bugs
This section guides you through submitting a bug report. Following these guidelines helps maintainers and the community understand your report, reproduce the behavior, and find related reports.
*   **Use the GitHub issue search** — check if the issue has already been reported.
*   Check if the issue has been fixed — try to reproduce it using the latest `main` branch.
*   Include your OS, Python version, and PySide6 version.
*   Provide a clear and descriptive title for the issue to identify the problem.

### Suggesting Enhancements
*   **Use the GitHub issue search** — check if the enhancement has already been suggested.
*   Provide a clear and descriptive title for the issue.
*   Provide a step-by-step description of the suggested enhancement in as many details as possible.
*   Explain why this enhancement would be useful to most users.

### Pull Requests
1.  Fork the repo and create your branch from `main`.
2.  If you've added code that should be tested, add tests.
3.  If you've changed APIs, update the documentation.
4.  Ensure the test suite passes.
5.  Make sure your code lints (we use `flake8` and `black` for formatting).
6.  Issue that pull request!

## 🛠️ Development Setup

1.  Clone your fork of the repository:
    ```bash
    git clone https://github.com/your-username/spectre-os.git
    cd spectre-os
    ```
2.  Set up a Python virtual environment:
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```
3.  Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4.  If working on the hardware integration, install the Arduino IDE and ESP32 board manager. Load `esp32/spectre_edge_sensor.ino` onto your microcontroller.

## 📝 Code Style
*   We use standard Python PEP 8 conventions.
*   Please format your code using `black` before submitting a PR.
*   Use type hints wherever possible to maintain code readability and reliability.

## ⚖️ Disclaimer
Contributions to offensive cyber security modules (MITM, Deauth, Flooding) must be strictly intended for educational and authorized network security auditing purposes. Malicious features or code intended to cause unauthorized damage will be rejected.

Thank you for contributing!
