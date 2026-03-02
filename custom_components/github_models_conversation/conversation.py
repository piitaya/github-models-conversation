"""Conversation entity for GitHub Models Conversation."""

from __future__ import annotations

from typing import Literal

import openai

from homeassistant.components import conversation
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import MATCH_ALL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import CopilotConfigEntry
from .const import (
    CONF_CHAT_MODEL,
    CONF_MAX_TOKENS,
    CONF_PROMPT,
    CONF_TEMPERATURE,
    CONF_TOP_P,
    DOMAIN,
    LOGGER,
    RECOMMENDED_CHAT_MODEL,
    RECOMMENDED_MAX_TOKENS,
    RECOMMENDED_TEMPERATURE,
    RECOMMENDED_TOP_P,
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: CopilotConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up conversation entity."""
    async_add_entities([GitHubModelsConversationEntity(config_entry)])


def _convert_chat_log_to_messages(
    chat_log: conversation.ChatLog,
) -> list[dict]:
    """Convert Home Assistant ChatLog content to OpenAI message format."""
    messages = []
    for content in chat_log.content:
        if isinstance(content, conversation.SystemContent):
            messages.append({"role": "system", "content": content.content})
        elif isinstance(content, conversation.UserContent):
            messages.append({"role": "user", "content": content.content})
        elif isinstance(content, conversation.AssistantContent):
            if content.content:
                messages.append({"role": "assistant", "content": content.content})
    return messages


class GitHubModelsConversationEntity(conversation.ConversationEntity):
    """GitHub Models conversation entity."""

    _attr_has_entity_name = True
    _attr_name = None

    def __init__(self, entry: CopilotConfigEntry) -> None:
        """Initialize the entity."""
        self._entry = entry
        self._attr_unique_id = entry.entry_id
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "GitHub",
            "model": "GitHub Models",
            "entry_type": "service",
        }

    @property
    def supported_languages(self) -> list[str] | Literal["*"]:
        """Return supported languages (all)."""
        return MATCH_ALL

    async def async_added_to_hass(self) -> None:
        """Register as conversation agent when added to HA."""
        await super().async_added_to_hass()
        conversation.async_set_agent(self.hass, self._entry, self)

    async def async_will_remove_from_hass(self) -> None:
        """Unregister as conversation agent when removed."""
        conversation.async_unset_agent(self.hass, self._entry)
        await super().async_will_remove_from_hass()

    async def _async_handle_message(
        self,
        user_input: conversation.ConversationInput,
        chat_log: conversation.ChatLog,
    ) -> conversation.ConversationResult:
        """Process a user message and return the AI response."""
        options = self._entry.options

        try:
            await chat_log.async_provide_llm_data(
                user_input.as_llm_context(DOMAIN),
                user_llm_hass_api=None,
                user_llm_prompt=options.get(CONF_PROMPT),
                user_extra_system_prompt=user_input.extra_system_prompt,
            )
        except conversation.ConverseError as err:
            return err.as_conversation_result()

        messages = _convert_chat_log_to_messages(chat_log)

        client: openai.AsyncOpenAI = self._entry.runtime_data

        model = options.get(CONF_CHAT_MODEL, RECOMMENDED_CHAT_MODEL)
        temperature = options.get(CONF_TEMPERATURE, RECOMMENDED_TEMPERATURE)
        top_p = options.get(CONF_TOP_P, RECOMMENDED_TOP_P)
        max_tokens = options.get(CONF_MAX_TOKENS, RECOMMENDED_MAX_TOKENS)

        try:
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
            )
        except openai.AuthenticationError as err:
            LOGGER.error("Authentication error: %s", err)
            raise conversation.ConverseError(
                "Authentication failed. Please check your GitHub token."
            ) from err
        except openai.RateLimitError as err:
            LOGGER.error("Rate limit exceeded: %s", err)
            raise conversation.ConverseError(
                "Rate limit exceeded. Please try again later."
            ) from err
        except openai.OpenAIError as err:
            LOGGER.error("API error: %s", err)
            raise conversation.ConverseError(
                "An error occurred communicating with GitHub Models."
            ) from err

        assistant_message = response.choices[0].message.content or ""

        chat_log.async_add_assistant_content_without_tools(
            conversation.AssistantContent(
                agent_id=user_input.agent_id,
                content=assistant_message,
            )
        )

        return conversation.async_get_result_from_chat_log(user_input, chat_log)
