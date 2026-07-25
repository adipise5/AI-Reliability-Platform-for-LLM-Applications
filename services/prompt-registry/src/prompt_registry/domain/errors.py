from __future__ import annotations

from uuid import UUID


class PromptRegistryError(Exception):
    """Base class for all domain errors raised by the Prompt Registry."""


class PromptNotFoundError(PromptRegistryError):
    def __init__(self, prompt_id: UUID) -> None:
        self.prompt_id = prompt_id
        super().__init__(f"no prompt {prompt_id} in this org")


class DuplicatePromptNameError(PromptRegistryError):
    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"a prompt named {name!r} already exists in this org")


class PromptVersionNotFoundError(PromptRegistryError):
    def __init__(self, version_id: UUID) -> None:
        self.version_id = version_id
        super().__init__(f"no version {version_id} on this prompt")


class NoActiveVersionError(PromptRegistryError):
    def __init__(self, prompt_id: UUID, environment: str) -> None:
        self.prompt_id = prompt_id
        self.environment = environment
        super().__init__(f"prompt {prompt_id} has no version promoted to {environment!r}")
