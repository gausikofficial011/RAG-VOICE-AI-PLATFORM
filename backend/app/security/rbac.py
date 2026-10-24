"""
Role-Based Access Control (RBAC)
Defines granular permissions, system roles, and role-to-permission mappings.
"""

from enum import Enum
from typing import List, Set


class Role(str, Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    SYSTEM_ADMIN = "SYSTEM_ADMIN"
    ORGANIZATION_OWNER = "ORGANIZATION_OWNER"
    ORGANIZATION_ADMIN = "ORGANIZATION_ADMIN"
    AI_ADMIN = "AI_ADMIN"
    AUDITOR = "AUDITOR"
    MANAGER = "MANAGER"
    USER = "USER"
    VIEWER = "VIEWER"


class Permission(str, Enum):
    # Knowledge Base
    KB_CREATE = "knowledge_base:create"
    KB_READ = "knowledge_base:read"
    KB_UPDATE = "knowledge_base:update"
    KB_DELETE = "knowledge_base:delete"

    # Document
    DOC_UPLOAD = "document:upload"
    DOC_READ = "document:read"
    DOC_DELETE = "document:delete"

    # Conversation
    CONV_CREATE = "conversation:create"
    CONV_READ = "conversation:read"
    CONV_DELETE = "conversation:delete"

    # Voice AI
    VOICE_EXECUTE = "voice:execute"

    # Analytics
    ANALYTICS_READ = "analytics:read"

    # AI / ML
    MODELS_READ = "models:read"
    MODELS_TRAIN = "models:train"
    MODELS_DEPLOY = "models:deploy"

    # Audit
    AUDIT_READ = "audit:read"

    # Administration
    USERS_MANAGE = "users:manage"
    ORG_MANAGE = "org:manage"
    SYSTEM_MANAGE = "system:manage"


# Granular mapping from Role to its permitted actions
ROLE_PERMISSIONS: dict[Role, Set[Permission]] = {
    Role.SUPER_ADMIN: {
        Permission.KB_CREATE, Permission.KB_READ, Permission.KB_UPDATE, Permission.KB_DELETE,
        Permission.DOC_UPLOAD, Permission.DOC_READ, Permission.DOC_DELETE,
        Permission.CONV_CREATE, Permission.CONV_READ, Permission.CONV_DELETE,
        Permission.VOICE_EXECUTE, Permission.ANALYTICS_READ,
        Permission.MODELS_READ, Permission.MODELS_TRAIN, Permission.MODELS_DEPLOY,
        Permission.AUDIT_READ, Permission.USERS_MANAGE, Permission.ORG_MANAGE, Permission.SYSTEM_MANAGE,
    },
    Role.SYSTEM_ADMIN: {
        Permission.KB_CREATE, Permission.KB_READ, Permission.KB_UPDATE, Permission.KB_DELETE,
        Permission.DOC_UPLOAD, Permission.DOC_READ, Permission.DOC_DELETE,
        Permission.CONV_CREATE, Permission.CONV_READ, Permission.CONV_DELETE,
        Permission.VOICE_EXECUTE, Permission.ANALYTICS_READ,
        Permission.MODELS_READ, Permission.AUDIT_READ,
        Permission.USERS_MANAGE, Permission.ORG_MANAGE, Permission.SYSTEM_MANAGE,
    },
    Role.ORGANIZATION_OWNER: {
        Permission.KB_CREATE, Permission.KB_READ, Permission.KB_UPDATE, Permission.KB_DELETE,
        Permission.DOC_UPLOAD, Permission.DOC_READ, Permission.DOC_DELETE,
        Permission.CONV_CREATE, Permission.CONV_READ, Permission.CONV_DELETE,
        Permission.VOICE_EXECUTE, Permission.ANALYTICS_READ,
        Permission.MODELS_READ, Permission.AUDIT_READ,
        Permission.USERS_MANAGE, Permission.ORG_MANAGE,
    },
    Role.ORGANIZATION_ADMIN: {
        Permission.KB_CREATE, Permission.KB_READ, Permission.KB_UPDATE, Permission.KB_DELETE,
        Permission.DOC_UPLOAD, Permission.DOC_READ, Permission.DOC_DELETE,
        Permission.CONV_CREATE, Permission.CONV_READ, Permission.CONV_DELETE,
        Permission.VOICE_EXECUTE, Permission.ANALYTICS_READ,
        Permission.AUDIT_READ, Permission.USERS_MANAGE,
    },
    Role.AI_ADMIN: {
        Permission.KB_READ, Permission.DOC_READ,
        Permission.CONV_CREATE, Permission.CONV_READ,
        Permission.VOICE_EXECUTE, Permission.ANALYTICS_READ,
        Permission.MODELS_READ, Permission.MODELS_TRAIN, Permission.MODELS_DEPLOY,
        Permission.AUDIT_READ,
    },
    Role.AUDITOR: {
        Permission.KB_READ, Permission.DOC_READ,
        Permission.CONV_READ, Permission.ANALYTICS_READ,
        Permission.MODELS_READ, Permission.AUDIT_READ,
    },
    Role.MANAGER: {
        Permission.KB_CREATE, Permission.KB_READ, Permission.KB_UPDATE,
        Permission.DOC_UPLOAD, Permission.DOC_READ,
        Permission.CONV_CREATE, Permission.CONV_READ, Permission.CONV_DELETE,
        Permission.VOICE_EXECUTE, Permission.ANALYTICS_READ,
    },
    Role.USER: {
        Permission.KB_CREATE, Permission.KB_READ, Permission.KB_UPDATE,
        Permission.DOC_UPLOAD, Permission.DOC_READ, Permission.DOC_DELETE,
        Permission.CONV_CREATE, Permission.CONV_READ, Permission.CONV_DELETE,
        Permission.VOICE_EXECUTE,
    },
    Role.VIEWER: {
        Permission.KB_READ, Permission.DOC_READ,
        Permission.CONV_READ,
    },
}


ROLE_ALIASES = {
    "PLATFORM_OWNER": Role.SUPER_ADMIN,
    "SUPER_ADMIN": Role.SUPER_ADMIN,
    "SYSTEM_ADMIN": Role.SYSTEM_ADMIN,
    "TENANT_ADMIN": Role.ORGANIZATION_ADMIN,
    "ORGANIZATION_ADMIN": Role.ORGANIZATION_ADMIN,
    "ORGANIZATION_OWNER": Role.ORGANIZATION_OWNER,
    "AI_ADMIN": Role.AI_ADMIN,
    "AUDITOR": Role.AUDITOR,
    "MANAGER": Role.MANAGER,
    "STANDARD_USER": Role.USER,
    "USER": Role.USER,
    "VIEWER": Role.VIEWER,
}


def resolve_role(role_name: str) -> Role:
    if not role_name:
        return Role.USER
    cleaned = role_name.strip().upper()
    if cleaned in ROLE_ALIASES:
        return ROLE_ALIASES[cleaned]
    try:
        return Role(cleaned)
    except ValueError:
        return Role.USER


def get_permissions_for_role(role_name: str) -> List[str]:
    """Retrieve list of permission strings for a given role name."""
    role = resolve_role(role_name)
    if role == Role.SUPER_ADMIN:
        return [p.value for p in Permission]
    return [p.value for p in ROLE_PERMISSIONS.get(role, set())]


def has_permission(role_name: str, permission: Permission) -> bool:
    """Check if a given role possesses a specific permission."""
    role = resolve_role(role_name)
    if role == Role.SUPER_ADMIN:
        return True
    return permission in ROLE_PERMISSIONS.get(role, set())

