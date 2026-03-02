"""Config flow for GitHub Models Conversation."""

from __future__ import annotations

from typing import Any

import openai
import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.httpx_client import get_async_client
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    SelectSelector,
    SelectSelectorConfig,
    TemplateSelector,
)

from .const import (
    CONF_CHAT_MODEL,
    CONF_MAX_TOKENS,
    CONF_PROMPT,
    CONF_RECOMMENDED,
    CONF_TEMPERATURE,
    CONF_TOP_P,
    DOMAIN,
    GITHUB_MODELS_BASE_URL,
    LOGGER,
    RECOMMENDED_CHAT_MODEL,
    RECOMMENDED_MAX_TOKENS,
    RECOMMENDED_TEMPERATURE,
    RECOMMENDED_TOP_P,
)

RECOMMENDED_OPTIONS = {
    CONF_RECOMMENDED: True,
    CONF_CHAT_MODEL: RECOMMENDED_CHAT_MODEL,
    CONF_MAX_TOKENS: RECOMMENDED_MAX_TOKENS,
    CONF_TEMPERATURE: RECOMMENDED_TEMPERATURE,
    CONF_TOP_P: RECOMMENDED_TOP_P,
}


async def validate_api_key(hass: HomeAssistant, api_key: str) -> None:
    """Validate the API key by making a minimal chat completion."""
    client = openai.AsyncOpenAI(
        api_key=api_key,
        base_url=GITHUB_MODELS_BASE_URL,
        http_client=get_async_client(hass),
    )
    await client.chat.completions.create(
        model=RECOMMENDED_CHAT_MODEL,
        messages=[{"role": "user", "content": "hi"}],
        max_tokens=1,
        timeout=10.0,
    )


class GitHubModelsConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for GitHub Models Conversation."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> GitHubModelsOptionsFlow:
        """Get the options flow for this handler."""
        return GitHubModelsOptionsFlow(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step: collect GitHub token."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                await validate_api_key(self.hass, user_input[CONF_API_KEY])
            except openai.AuthenticationError:
                errors["base"] = "invalid_auth"
            except openai.APIConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:
                LOGGER.exception("Unexpected error during validation")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title="GitHub Models",
                    data=user_input,
                    options=RECOMMENDED_OPTIONS,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_API_KEY): str,
                }
            ),
            errors=errors,
        )


class GitHubModelsOptionsFlow(OptionsFlow):
    """Handle options flow for GitHub Models Conversation."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry
        self._models: list[str] | None = None

    async def _fetch_models(self) -> list[str]:
        """Fetch available models from GitHub Models catalog API."""
        if self._models is not None:
            return self._models

        session = async_get_clientsession(self.hass)
        headers = {
            "Authorization": f"Bearer {self._config_entry.data[CONF_API_KEY]}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        try:
            resp = await session.get(
                "https://models.github.ai/catalog/models",
                headers=headers,
                timeout=10,
            )
            resp.raise_for_status()
            data = await resp.json()
            self._models = sorted(
                model["id"]
                for model in data
                if "text" in model.get("supported_input_modalities", [])
                and "text" in model.get("supported_output_modalities", [])
            )
        except Exception:
            LOGGER.exception("Failed to fetch models from catalog")
            self._models = [RECOMMENDED_CHAT_MODEL]

        if not self._models:
            self._models = [RECOMMENDED_CHAT_MODEL]

        return self._models

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            if user_input.get(CONF_RECOMMENDED):
                return self.async_create_entry(
                    data={
                        CONF_RECOMMENDED: True,
                        CONF_CHAT_MODEL: RECOMMENDED_CHAT_MODEL,
                        CONF_MAX_TOKENS: RECOMMENDED_MAX_TOKENS,
                        CONF_TEMPERATURE: RECOMMENDED_TEMPERATURE,
                        CONF_TOP_P: RECOMMENDED_TOP_P,
                    },
                )
            return await self.async_step_advanced()

        current = self._config_entry.options

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_PROMPT,
                        description={
                            "suggested_value": current.get(CONF_PROMPT),
                        },
                    ): TemplateSelector(),
                    vol.Required(
                        CONF_RECOMMENDED,
                        default=current.get(CONF_RECOMMENDED, True),
                    ): bool,
                }
            ),
        )

    async def async_step_advanced(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage advanced options."""
        if user_input is not None:
            if CONF_PROMPT in self._config_entry.options:
                user_input[CONF_PROMPT] = self._config_entry.options[CONF_PROMPT]
            return self.async_create_entry(data=user_input)

        models = await self._fetch_models()
        current = self._config_entry.options

        return self.async_show_form(
            step_id="advanced",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_CHAT_MODEL,
                        default=current.get(CONF_CHAT_MODEL, RECOMMENDED_CHAT_MODEL),
                    ): SelectSelector(
                        SelectSelectorConfig(
                            options=models,
                            mode="dropdown",
                            sort=True,
                        )
                    ),
                    vol.Required(
                        CONF_TEMPERATURE,
                        default=current.get(
                            CONF_TEMPERATURE, RECOMMENDED_TEMPERATURE
                        ),
                    ): NumberSelector(
                        NumberSelectorConfig(min=0.0, max=2.0, step=0.05),
                    ),
                    vol.Required(
                        CONF_TOP_P,
                        default=current.get(CONF_TOP_P, RECOMMENDED_TOP_P),
                    ): NumberSelector(
                        NumberSelectorConfig(min=0.0, max=1.0, step=0.05),
                    ),
                    vol.Required(
                        CONF_MAX_TOKENS,
                        default=current.get(
                            CONF_MAX_TOKENS, RECOMMENDED_MAX_TOKENS
                        ),
                    ): int,
                }
            ),
        )
