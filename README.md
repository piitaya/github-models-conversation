# GitHub Models Conversation

A [Home Assistant](https://www.home-assistant.io/) custom integration that adds a conversation agent powered by [GitHub Models](https://github.com/marketplace/models).

## Installation

### HACS (recommended)

1. Add this repository as a custom repository in [HACS](https://hacs.xyz/)
2. Search for "GitHub Models" and install it
3. Restart Home Assistant

### Manual

1. Copy the `custom_components/github_models_conversation` folder into your `custom_components` directory
2. Restart Home Assistant

## Configuration

1. Go to **Settings** > **Devices & Services** > **Add Integration**
2. Search for **GitHub Models**
3. Enter your GitHub personal access token
   - **Fine-grained tokens (recommended)** — more secure, requires the `models:read` permission
   - **Classic tokens** — work without any additional scope
4. Go to **Settings** > **Voice assistants** and select **GitHub Models** as the conversation agent

## Options

| Option | Description | Default |
|--------|-------------|---------|
| System Prompt | Instructions for the AI (supports HA templates) | - |
| Model | The AI model to use | `openai/gpt-4o-mini` |
| Temperature | Controls randomness (0-2) | `1.0` |
| Top P | Alternative to temperature (0-1) | `1.0` |
| Max Tokens | Maximum tokens in the response | `1024` |

## Note

GitHub Models is intended for learning, experimentation, and proof-of-concept purposes. Usage is rate-limited. See [GitHub Models documentation](https://docs.github.com/en/github-models) for details.
