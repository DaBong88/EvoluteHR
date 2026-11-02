"""Single source of truth for the Horilla HR product version.

Keep in lockstep with release tags so published artifacts and source releases
always identify the same product version.
"""

__version__ = "2.1.7"

# Contract version for unauthenticated clients. ``/health/`` advertises this
# instead of ``__version__``: a client needs to know "is this Horilla, and does
# it speak a protocol I understand", which is not the same question as "which
# patch release is this" -- and the second answer, given to anyone who asks,
# maps a host straight onto the published advisories for that exact version.
# Bump when the API contract changes in a way a client must react to.
API_VERSION = 1
