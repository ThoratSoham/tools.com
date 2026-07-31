# Contributing to tools.com

First off, thanks for considering contributing! This project is a collection of simple, no-nonsense tools for content creators — transcript extraction, YouTube downloading, background removal, and more. All skill levels welcome, and yes, **vibe coding / AI-assisted contributions are totally fine** — just make sure you understand and test what you submit.

## Ways to Contribute

- 🐛 **Report bugs** — open an issue with steps to reproduce
- ✨ **Suggest features** — new tools creators might need
- 🔧 **Fix issues** — check the [Issues tab](https://github.com/ThoratSoham/tools.com/issues) for open tasks
- 🆕 **Build new tools** — e.g. YouTube video downloader, background remover
- 📝 **Improve docs** — README clarity, setup instructions, comments

## Getting Started

1. **Fork** the repo and clone your fork:
   ```
   git clone https://github.com/<your-username>/tools.com.git
   cd tools.com
   ```
2. **Set up the project** following the [README setup steps](README.md#setup) (Python venv, ffmpeg, dependencies).
3. **Create a branch** for your change:
   ```
   git checkout -b feature/short-description
   ```
   Use prefixes like `feature/`, `fix/`, or `docs/` to keep things clear.

## Making Changes

- Keep changes focused — one feature or fix per PR.
- Follow the existing project structure (Flask backend in `app.py`, frontend in `index.html`).
- Test your changes locally before submitting (`python3 app.py` and try the flow end-to-end).
- If you're adding a new tool, try to keep it consistent with how the transcript tool is structured (simple endpoint, temp files cleaned up after processing).
- No hard style guide yet — just keep code readable and comment tricky bits.

## Submitting a Pull Request

1. Commit your changes with a clear message:
   ```
   git commit -m "Add: short description of what changed"
   ```
2. Push to your fork:
   ```
   git push origin feature/short-description
   ```
3. Open a PR against the `main` branch of this repo.
4. In your PR description, briefly explain:
   - What the change does
   - How you tested it
   - Any known limitations

## Reporting Bugs / Requesting Features

Open an issue and include:
- What you expected vs. what happened (for bugs)
- Steps to reproduce, if applicable
- Your OS and Python version (for setup-related bugs)

## Code of Conduct

Be respectful, be patient with beginners, and keep discussions constructive. No gatekeeping — everyone starts somewhere.

## Questions?

Open an issue with the `question` label, or start a discussion. Happy to help onboard anyone who's interested!
