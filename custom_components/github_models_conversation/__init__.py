"""The GitHub Models Conversation integration."""

from __future__ import annotations

import openai

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.httpx_client import get_async_client

from .const import GITHUB_MODELS_BASE_URL, LOGGER

PLATFORMS = [Platform.CONVERSATION]

type CopilotConfigEntry = ConfigEntry[openai.AsyncOpenAI]


async def async_setup_entry(hass: HomeAssistant, entry: CopilotConfigEntry) -> bool:
    """Set up GitHub Models Conversation from a config entry."""
    client = openai.AsyncOpenAI(
        api_key=entry.data[CONF_API_KEY],
        base_url=GITHUB_MODELS_BASE_URL,
        http_client=get_async_client(hass),
    )

    try:
        await client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[{"role": "user", "content": "hi"}],
            max_tokens=1,
            timeout=10.0,
        )
    except openai.AuthenticationError as err:
        LOGGER.error("Invalid GitHub token: %s", err)
        return False
    except openai.OpenAIError as err:
        raise ConfigEntryNotReady(err) from err

    entry.runtime_data = client

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    return True


async def _async_update_listener(
    hass: HomeAssistant, entry: CopilotConfigEntry
) -> None:
    """Handle options update by reloading the entry."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(
    hass: HomeAssistant, entry: CopilotConfigEntry
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
