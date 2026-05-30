"""OpenAPI helpers for project-specific authentication."""

from drf_spectacular.extensions import OpenApiAuthenticationExtension

from users.authentication import TokenAuthentication


class TokenAuthenticationScheme(OpenApiAuthenticationExtension):
    """Describe the custom `Authorization: Token <key>` authentication header."""

    target_class = TokenAuthentication
    name = "TokenAuth"

    def get_security_definition(self, auto_schema: object) -> dict[str, str]:
        """Return the OpenAPI security scheme for custom token auth."""
        return {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
            "description": "Use `Token <opaque-token>`.",
        }
