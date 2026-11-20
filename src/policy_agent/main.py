"""Composition root. ADAPTERS=azure|fake picks the adapters; there is no default."""

import os

from agent_framework.foundry import FoundryChatClient
from azure.identity.aio import ManagedIdentityCredential
from azure.search.documents.aio import SearchClient
from margin_copilot_shared.security.tokens import entra_validator
from margin_copilot_shared.testing.issuer import LocalIssuer
from starlette.applications import Starlette

from policy_agent.adapters.inbound.a2a_server import create_a2a_app
from policy_agent.adapters.outbound.analyst import FakePolicyAnalyst, FoundryPolicyAnalyst
from policy_agent.adapters.outbound.azure_search import AzureSearchStore

TOOL_LIMITS = {"max_iterations": 2}
MODEL_TIMEOUT = 60


def create_app() -> Starlette:
    env = os.environ
    adapters = env["ADAPTERS"]
    if adapters == "azure":
        tenant_id, client_id = env["TENANT_ID"], env["CLIENT_ID"]
        callers = frozenset(env["ALLOWED_CALLERS"].split(","))
        credential = ManagedIdentityCredential(client_id=env["AZURE_CLIENT_ID"])
        store = AzureSearchStore(
            SearchClient(env["SEARCH_ENDPOINT"], env["SEARCH_INDEX"], credential)
        )
        model = FoundryChatClient(
            project_endpoint=env["FOUNDRY_PROJECT_ENDPOINT"],
            model=env["FOUNDRY_MODEL"],
            credential=credential,
            function_invocation_configuration=TOOL_LIMITS,
            timeout=MODEL_TIMEOUT,
        )
        validator = entra_validator(tenant_id, client_id, callers)
        return create_a2a_app(FoundryPolicyAnalyst(model, store), validator, env["PUBLIC_URL"])
    if adapters == "fake":
        # A fresh in-memory key per process: nobody outside this process can mint a token for it.
        validator = LocalIssuer().validator(
            audience="policy-agent", allowed_callers=frozenset({"orchestrator"})
        )
        public_url = env.get("PUBLIC_URL", "http://localhost:8000/")
        return create_a2a_app(FakePolicyAnalyst(), validator, public_url)
    raise ValueError(f"ADAPTERS must be azure or fake, not {adapters!r}")
