"""Config flow for GitHub Models Conversation."""

from __future__ import annotations

from typing import Any

import openai
import voluptuous as vol

from homeassistant.config_entries import (
    SOURCE_USER,
    ConfigEntry,
    ConfigEntryState,
    ConfigFlow,
    ConfigFlowResult,
    ConfigSubentryFlow,
    SubentryFlowResult,
)
from homeassistant.const import CONF_API_KEY, CONF_LLM_HASS_API, CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import llm
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.httpx_client import get_async_client
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    SelectOptionDict,
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
    DEFAULT_AI_TASK_NAME,
    DEFAULT_CONVERSATION_NAME,
    DOMAIN,
    GITHUB_MODELS_BASE_URL,
    LOGGER,
    RECOMMENDED_AI_TASK_OPTIONS,
    RECOMMENDED_CHAT_MODEL,
    RECOMMENDED_CONVERSATION_OPTIONS,
    RECOMMENDED_MAX_TOKENS,
    RECOMMENDED_TEMPERATURE,
    RECOMMENDED_TOP_P,
)


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

    @classmethod
    @callback
    def async_get_supported_subentry_types(
        cls, config_entry: ConfigEntry
    ) -> dict[str, type[ConfigSubentryFlow]]:
        """Return subentries supported by this handler."""
        return {
            "conversation": ConversationFlowHandler,
            "ai_task_data": ConversationFlowHandler,
        }

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step: collect GitHub token."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._async_abort_entries_match(user_input)
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
                    subentries=[
                        {
                            "subentry_type": "conversation",
                            "data": RECOMMENDED_CONVERSATION_OPTIONS,
                            "title": DEFAULT_CONVERSATION_NAME,
                            "unique_id": None,
                        },
                        {
                            "subentry_type": "ai_task_data",
                            "data": RECOMMENDED_AI_TASK_OPTIONS,
                            "title": DEFAULT_AI_TASK_NAME,
                            "unique_id": None,
                        },
                    ],
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


class ConversationFlowHandler(ConfigSubentryFlow):
    """Handle subentry flow for conversation agents."""

    def __init__(self) -> None:
        """Initialize the subentry flow."""
        self.options: dict[str, Any] = {}
        self._models: list[str] | None = None

    @property
    def _is_new(self) -> bool:
        """Return if this is a new subentry."""
        return self.source == SOURCE_USER

    async def _fetch_models(self) -> list[str]:
        """Fetch available models from GitHub Models catalog API."""
        if self._models is not None:
            return self._models

        entry = self._get_entry()
        session = async_get_clientsession(self.hass)
        headers = {
            "Authorization": f"Bearer {entry.data[CONF_API_KEY]}",
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

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Handle creation of a new subentry."""
        if self._subentry_type == "ai_task_data":
            self.options = RECOMMENDED_AI_TASK_OPTIONS.copy()
        else:
            self.options = RECOMMENDED_CONVERSATION_OPTIONS.copy()
        return await self.async_step_init(user_input)

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Handle reconfiguration of a conversation agent."""
        self.options = dict(self._get_reconfigure_subentry().data)
        return await self.async_step_init(user_input)

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Manage subentry configuration."""
        if self._get_entry().state != ConfigEntryState.LOADED:
            return self.async_abort(reason="entry_not_loaded")

        options = self.options

        if user_input is not None:
            if not user_input.get(CONF_LLM_HASS_API):
                user_input.pop(CONF_LLM_HASS_API, None)

            if user_input[CONF_RECOMMENDED]:
                if self._is_new:
                    return self.async_create_entry(
                        title=user_input.pop(CONF_NAME),
                        data=user_input,
                    )
                return self.async_update_and_abort(
                    self._get_entry(),
                    self._get_reconfigure_subentry(),
                    data=user_input,
                )

            options.update(user_input)
            if CONF_LLM_HASS_API in options and CONF_LLM_HASS_API not in user_input:
                options.pop(CONF_LLM_HASS_API)
            return await self.async_step_advanced()

        step_schema: dict[vol.Marker, Any] = {}

        if self._is_new:
            if self._subentry_type == "ai_task_data":
                default_name = DEFAULT_AI_TASK_NAME
            else:
                default_name = DEFAULT_CONVERSATION_NAME
            step_schema[
                vol.Required(CONF_NAME, default=default_name)
            ] = str

        if self._subentry_type == "conversation":
            hass_apis: list[SelectOptionDict] = [
                SelectOptionDict(
                    label=api.name,
                    value=api.id,
                )
                for api in llm.async_get_apis(self.hass)
            ]
            step_schema.update(
                {
                    vol.Optional(
                        CONF_PROMPT,
                        description={
                            "suggested_value": options.get(CONF_PROMPT),
                        },
                    ): TemplateSelector(),
                    vol.Optional(
                        CONF_LLM_HASS_API,
                    ): SelectSelector(
                        SelectSelectorConfig(options=hass_apis, multiple=True)
                    ),
                }
            )

        step_schema[
            vol.Required(
                CONF_RECOMMENDED,
                default=options.get(CONF_RECOMMENDED, False),
            )
        ] = bool

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema(step_schema),
                options,
            ),
        )

    async def async_step_advanced(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Manage advanced model settings."""
        options = self.options

        if user_input is not None:
            options.update(user_input)

            if self._is_new:
                return self.async_create_entry(
                    title=options.pop(CONF_NAME),
                    data=options,
                )
            return self.async_update_and_abort(
                self._get_entry(),
                self._get_reconfigure_subentry(),
                data=options,
            )

        try:
            models = await self._fetch_models()
        except Exception:
            return self.async_abort(reason="cannot_connect")

        return self.async_show_form(
            step_id="advanced",
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema(
                    {
                        vol.Required(
                            CONF_CHAT_MODEL,
                            default=RECOMMENDED_CHAT_MODEL,
                        ): SelectSelector(
                            SelectSelectorConfig(
                                options=models,
                                mode="dropdown",
                                sort=True,
                            )
                        ),
                        vol.Required(
                            CONF_TEMPERATURE,
                            default=RECOMMENDED_TEMPERATURE,
                        ): NumberSelector(
                            NumberSelectorConfig(min=0.0, max=2.0, step=0.05),
                        ),
                        vol.Required(
                            CONF_TOP_P,
                            default=RECOMMENDED_TOP_P,
                        ): NumberSelector(
                            NumberSelectorConfig(min=0.0, max=1.0, step=0.05),
                        ),
                        vol.Required(
                            CONF_MAX_TOKENS,
                            default=RECOMMENDED_MAX_TOKENS,
                        ): int,
                    }
                ),
                options,
            ),
        )
