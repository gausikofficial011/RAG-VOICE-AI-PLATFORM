import asyncio
import uuid
from backend.app.core.database import async_session_maker
from backend.app.models.organization import Organization
from backend.app.models.user import User
from backend.app.models.knowledge_base import KnowledgeBase
from backend.app.security.password import hash_password
from sqlalchemy import select
from backend.app.services.document_service import DocumentService

DEMO_PASSWORD = "Password123!"

DEMO_USERS = [
    {
        "email": "admin@ragvoice.ai",
        "full_name": "Platform Superadmin",
        "role": "PLATFORM_OWNER",
        "portal_access": "All Portals (User, Org Admin, AI/ML Admin, System Admin, Auditor)",
    },
    {
        "email": "orgadmin@ragvoice.ai",
        "full_name": "Sarah Chen (Org Admin)",
        "role": "TENANT_ADMIN",
        "portal_access": "Organization Admin & User Portals",
    },
    {
        "email": "aiadmin@ragvoice.ai",
        "full_name": "Alex Vance (MLOps Engineer)",
        "role": "AI_ADMIN",
        "portal_access": "AI/ML Admin & User Portals",
    },
    {
        "email": "auditor@ragvoice.ai",
        "full_name": "Marcus Stone (Security Auditor)",
        "role": "AUDITOR",
        "portal_access": "Auditor & User Portals",
    },
    {
        "email": "user@ragvoice.ai",
        "full_name": "Elena Rostova (Standard User)",
        "role": "STANDARD_USER",
        "portal_access": "User Portal (Voice Orb & Chat)",
    },
]

SAMPLE_DOC_TEXT = """# Acme Enterprise Intelligence Guidelines & Company Policies

## 1. Customer Refund & Return Policy
Customers are eligible for a 100% full refund on software licenses within 30 calendar days of initial purchase. To initiate a refund, contact billing@acme.io with your enterprise license key. Hardware items may be returned within 45 days in original packaging.

## 2. Remote Work & Security Standards
All employees operating remotely must connect via the corporate WireGuard VPN with Multi-Factor Authentication (MFA) enabled. Passwords must be at least 12 characters and adhere to Argon2id security requirements. Workstations must lock automatically after 5 minutes of inactivity.

## 3. Product Architecture & AI Platform
The Acme Voice AI platform operates on a two-layer AI architecture combining foundation large language models with lightweight project-specific classifiers. Grounding validation scores must exceed 0.70 before any generative response is surfaced to the customer.

## 4. Emergency Response & Incident Escalation
In case of a security breach or service outage exceeding 15 minutes, notify the incident response team at oncall@acme.io. P1 incidents require an executive war room within 10 minutes and status page updates every 20 minutes.
"""

async def seed():
    async with async_session_maker() as session:
        # 1. Organization
        stmt = select(Organization).where(Organization.name == "Acme Intelligence Corp")
        res = await session.execute(stmt)
        org = res.scalar_one_or_none()

        if not org:
            org = Organization(
                id=str(uuid.uuid4()),
                name="Acme Intelligence Corp",
                slug="acme-corp",
                is_active=True,
                settings={"plan": "enterprise", "max_users": 100, "storage_mb": 10240},
            )
            session.add(org)
            await session.commit()
            await session.refresh(org)
            print(f"[+] Created organization: {org.name} ({org.id})")
        else:
            print(f"[*] Organization already exists: {org.name} ({org.id})")

        # 2. Users
        created_users = []
        for u_data in DEMO_USERS:
            stmt = select(User).where(User.email == u_data["email"])
            res = await session.execute(stmt)
            user = res.scalar_one_or_none()

            if not user:
                user = User(
                    id=str(uuid.uuid4()),
                    tenant_id=org.id,
                    email=u_data["email"],
                    hashed_password=hash_password(DEMO_PASSWORD),
                    full_name=u_data["full_name"],
                    role=u_data["role"],
                    is_active=True,
                    is_verified=True,
                    mfa_enabled=False,
                )
                session.add(user)
                await session.commit()
                await session.refresh(user)
                print(f"[+] Created user: {user.email} (Role: {user.role})")
            else:
                user.role = u_data["role"]
                user.hashed_password = hash_password(DEMO_PASSWORD)
                user.mfa_enabled = False
                await session.commit()
                print(f"[*] Updated user: {user.email} (Role: {user.role})")
            created_users.append(user)

        # 3. Knowledge Base
        stmt = select(KnowledgeBase).where(
            KnowledgeBase.tenant_id == org.id,
            KnowledgeBase.name == "Enterprise Knowledge Base"
        )
        res = await session.execute(stmt)
        kb = res.scalar_one_or_none()

        if not kb:
            kb = KnowledgeBase(
                id=str(uuid.uuid4()),
                tenant_id=org.id,
                name="Enterprise Knowledge Base",
                description="Company policies, refund terms, remote work security, and platform architecture.",
                chunk_size=500,
                chunk_overlap=80,
                top_k=5,
                retrieval_strategy="hybrid",
                created_by=created_users[0].id,
            )
            session.add(kb)
            await session.commit()
            await session.refresh(kb)
            print(f"[+] Created Knowledge Base: {kb.name} ({kb.id})")

            # 4. Ingest Sample Document
            doc_service = DocumentService()
            doc = await doc_service.process_and_index_document(
                db=session,
                tenant_id=org.id,
                kb_id=kb.id,
                filename="Acme_Company_Policies.md",
                file_bytes=SAMPLE_DOC_TEXT.encode("utf-8"),
                mime_type="text/markdown",
                user_id=created_users[0].id,
            )
            print(f"[+] Ingested sample policy document: {doc.filename} with {doc.chunk_count} chunks.")
        else:
            print(f"[*] Knowledge Base already exists: {kb.name} ({kb.id})")

    print("\n[SUCCESS] Seeding complete! All accounts ready.")

if __name__ == "__main__":
    asyncio.run(seed())
