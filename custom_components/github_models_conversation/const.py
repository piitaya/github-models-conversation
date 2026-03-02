"""Constants for the GitHub Models Conversation integration."""

import logging

DOMAIN = "github_models_conversation"
LOGGER = logging.getLogger(__name__)

GITHUB_MODELS_BASE_URL = "https://models.github.ai/inference"

CONF_RECOMMENDED = "recommended"
CONF_PROMPT = "prompt"
CONF_CHAT_MODEL = "chat_model"
CONF_MAX_TOKENS = "max_tokens"
CONF_TEMPERATURE = "temperature"
CONF_TOP_P = "top_p"

RECOMMENDED_CHAT_MODEL = "openai/gpt-4o-mini"
RECOMMENDED_MAX_TOKENS = 1024
RECOMMENDED_TEMPERATURE = 1.0
RECOMMENDED_TOP_P = 1.0
