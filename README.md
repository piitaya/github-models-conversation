# GitHub Models Conversation

> **Experimental** — This integration is a proof of concept and has not been heavily tested.

A [Home Assistant](https://www.home-assistant.io/) custom integration that adds a conversation agent and AI task entity powered by [GitHub Models](https://github.com/marketplace/models).

## Features

- **Conversation agent** — Chat with AI models, control Home Assistant via tool calling
- **AI task agent** — Structured data generation with attachment/vision support
- **Model catalog** — Automatically fetches available models from the GitHub Models API
- **Recommended settings** — One-click setup with sensible defaults, or customize model parameters

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
4. A default conversation agent and AI task agent are created automatically
5. Go to **Settings** > **Voice assistants** and select **GitHub Models Conversation** as the conversation agent

You can add more conversation agents or AI task agents from the integration page.

## Options

### Conversation agent

| Option | Description | Default |
|--------|-------------|---------|
| Instructions | System prompt for the AI (supports HA templates) | Default HA instructions |
| Control Home Assistant | LLM APIs to expose (tool calling) | Assist |
| Recommended | Use recommended model settings | Enabled |

### Advanced settings (when recommended is disabled)

| Option | Description | Default |
|--------|-------------|---------|
| Model | The AI model to use | `openai/gpt-4o-mini` |
| Temperature | Controls randomness (0-2) | `1.0` |
| Top P | Alternative to temperature (0-1) | `1.0` |
| Max Tokens | Maximum tokens in the response | `1024` |

### AI task agent

Same advanced model settings as conversation agents. No system prompt or LLM API options.

## Free tier

GitHub Models comes with a **free tier** — no payment required. Any GitHub account can use it with a personal access token.

Rate limits for the free tier (Copilot Free):

| Tier | Requests/min | Requests/day | Tokens/request | Concurrent |
| --- | --- | --- | --- | --- |
| **Low models** | 15 | 150 | 8k in / 4k out | 5 |
| **High models** | 10 | 50 | 8k in / 4k out | 2 |
| **Embedding models** | 15 | 150 | 64k | 5 |

These limits are subject to change. See the [GitHub Models rate limits documentation](https://docs.github.com/en/github-models/use-github-models/prototyping-with-ai-models#rate-limits) for the latest details.
