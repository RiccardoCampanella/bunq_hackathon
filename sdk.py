from bunq.sdk.context.api_context import ApiContext
from bunq.sdk.context.bunq_context import BunqContext
from bunq import ApiEnvironmentType

# Create an API context for production
api_context = ApiContext.create(
    ApiEnvironmentType.SANDBOX, # SANDBOX for testing
    "sandbox_6aad089ce7ea397a64574b7d465a5293805a070bb835767afa80209a",
    "My Device Description"
)

# Save API context
api_context.save("bunq_api_context.conf")

# Restore API context
api_context = ApiContext.restore("bunq_api_context.conf")
BunqContext.load_api_context(api_context)
