"""Constants for the GitHub Models Conversation integration."""

import logging

from homeassistant.const import CONF_LLM_HASS_API
from homeassistant.helpers import llm

DOMAIN = "github_models_conversation"
LOGGER = logging.getLogger(__name__)

GITHUB_MODELS_BASE_URL = "https://models.github.ai/inference"

CONF_PROMPT = "prompt"
CONF_CHAT_MODEL = "chat_model"
CONF_MAX_TOKENS = "max_tokens"
CONF_TEMPERATURE = "temperature"
CONF_TOP_P = "top_p"
CONF_RECOMMENDED = "recommended"

DEFAULT_CONVERSATION_NAME = "GitHub Models Conversation"

RECOMMENDED_CHAT_MODEL = "openai/gpt-4o-mini"
RECOMMENDED_MAX_TOKENS = 1024
RECOMMENDED_TEMPERATURE = 1.0
RECOMMENDED_TOP_P = 1.0

RECOMMENDED_CONVERSATION_OPTIONS: dict = {
    CONF_RECOMMENDED: True,
    CONF_LLM_HASS_API: [llm.LLM_API_ASSIST],
    CONF_PROMPT: llm.DEFAULT_INSTRUCTIONS_PROMPT,
}
