"""App MVP Builder Service

Genera código completo de aplicaciones (Next.js frontend + FastAPI backend)
como archivos de texto, los comprime en ZIP y guarda en storage.
"""

import os
import uuid
import zipfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domains.agents.app_builder.models import AppBuildJob, AppFeature, AppBuildStatus
from app.domains.agents.app_builder.schemas import AppBuildJobCreate, AppFeatureCreate
from app.domains.agents.prompts.business_context_adapter import (
    get_agent_prompt_context,
    format_business_context_for_prompt,
)

logger = get_logger(__name__)

STORAGE_DIR = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))) / "storage" / "exports"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)


class AppBuilderService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ========== CRUD ==========

    async def create_job(self, data: AppBuildJobCreate) -> AppBuildJob:
        job = AppBuildJob(
            business_id=data.business_id,
            app_name=data.app_name,
            description=data.description,
            features=[f.model_dump() for f in data.features],
            tech_stack=data.tech_stack,
            status=AppBuildStatus.PENDING,
        )
        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)

        # Guardar features individuales
        for feat in data.features:
            self.db.add(AppFeature(
                job_id=job.id,
                feature_name=feat.feature_name,
                description=feat.description,
                priority=feat.priority,
                estimated_hours=feat.estimated_hours,
            ))
        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def get_job(self, job_id: uuid.UUID) -> Optional[AppBuildJob]:
        result = await self.db.execute(select(AppBuildJob).where(AppBuildJob.id == job_id))
        return result.scalar_one_or_none()

    async def list_jobs(self, business_id: uuid.UUID, limit: int = 100, offset: int = 0) -> List[AppBuildJob]:
        result = await self.db.execute(
            select(AppBuildJob)
            .where(AppBuildJob.business_id == business_id)
            .order_by(desc(AppBuildJob.created_at))
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    async def update_job(self, job_id: uuid.UUID, **kwargs) -> Optional[AppBuildJob]:
        job = await self.get_job(job_id)
        if not job:
            return None
        for k, v in kwargs.items():
            if hasattr(job, k):
                setattr(job, k, v)
        await self.db.commit()
        await self.db.refresh(job)
        return job

    # ========== Generation ==========

    async def generate_app_mvp(
        self,
        business_id: uuid.UUID,
        app_description: str,
        features_list: List[AppFeatureCreate],
    ) -> AppBuildJob:
        """1. Crea job; 2. Analiza con LLM; 3. Genera código; 4. ZIP + guarda."""
        job = await self.create_job(AppBuildJobCreate(
            business_id=business_id,
            app_name=app_description.split("\n")[0][:100] or "MVP App",
            description=app_description,
            features=features_list,
        ))
        await self.update_job(job.id, status=AppBuildStatus.ANALYZING)

        try:
            # Opcional: LLM analysis (best-effort)
            analysis = await self._analyze_with_llm(business_id, app_description, features_list)
            logger.info(f"AppBuilder LLM analysis for job {job.id}: {analysis[:200]}...")
        except Exception as e:
            logger.warning(f"AppBuilder LLM analysis failed: {e}")
            analysis = ""

        await self.update_job(job.id, status=AppBuildStatus.GENERATING)

        try:
            zip_path = self._generate_code_zip(job, app_description, features_list, analysis)
            relative_url = f"/storage/exports/{zip_path.name}"
            preview = self._build_preview_instructions(job, features_list)

            await self.update_job(
                job.id,
                status=AppBuildStatus.COMPLETED,
                code_zip_url=relative_url,
                preview_url=relative_url,
                deploy_instructions=preview,
            )
        except Exception as e:
            logger.exception(f"AppBuilder generation failed for job {job.id}: {e}")
            await self.update_job(job.id, status=AppBuildStatus.FAILED, deploy_instructions=str(e))

        return await self.get_job(job.id)

    async def _analyze_with_llm(self, business_id: uuid.UUID, app_description: str, features_list: List[AppFeatureCreate]) -> str:
        from langchain_core.messages import SystemMessage, HumanMessage
        from app.domains.agents.llm_provider import generate_with_fallback

        ctx = await get_agent_prompt_context(self.db, business_id)
        context_block = format_business_context_for_prompt(ctx)

        features_text = "\n".join(
            f"- {f.feature_name}: {f.description or ''} (prioridad {f.priority})"
            for f in features_list
        )
        human_content = (
            f"Descripción de la app:\n{app_description}\n\n"
            f"Features:\n{features_text}\n\n"
            "Devuelve un análisis breve (máx 500 palabras) con stack recomendado, "
            "estructura de carpetas y consideraciones de seguridad."
        )
        if context_block:
            human_content = f"{context_block}\n\n{human_content}"
        messages = [
            SystemMessage(content="Eres un arquitecto de software senior. Analiza requerimientos y sugiere una arquitectura limpia."),
            HumanMessage(content=human_content),
        ]
        resp = await generate_with_fallback(self.db, business_id, messages, model="gpt-4o-mini", temperature=0.3, max_tokens=1200)
        return resp.content if resp else ""

    def _generate_code_zip(
        self,
        job: AppBuildJob,
        app_description: str,
        features_list: List[AppFeatureCreate],
        analysis: str,
    ) -> Path:
        """Genera archivos de código como texto y los empaqueta en ZIP."""
        tmpdir = tempfile.mkdtemp(prefix=f"app_build_{job.id}_")
        app_slug = self._slugify(job.app_name)

        # === FRONTEND (Next.js) ===
        fe_dir = Path(tmpdir) / f"{app_slug}-frontend"
        self._write_file(fe_dir / "package.json", self._frontend_package_json(app_slug))
        self._write_file(fe_dir / "tailwind.config.js", self._frontend_tailwind_config())
        self._write_file(fe_dir / "src" / "app" / "page.tsx", self._frontend_home_page(app_description))
        self._write_file(fe_dir / "src" / "app" / "auth" / "page.tsx", self._frontend_auth_page())
        self._write_file(fe_dir / "src" / "app" / "dashboard" / "page.tsx", self._frontend_dashboard_page(features_list))
        self._write_file(fe_dir / "src" / "app" / "settings" / "page.tsx", self._frontend_settings_page())
        self._write_file(fe_dir / "src" / "components" / "Layout.tsx", self._frontend_layout_component())
        self._write_file(fe_dir / "src" / "components" / "FormInput.tsx", self._frontend_form_input())
        self._write_file(fe_dir / "src" / "components" / "DataTable.tsx", self._frontend_data_table())
        self._write_file(fe_dir / "src" / "components" / "Card.tsx", self._frontend_card_component())
        self._write_file(fe_dir / "src" / "lib" / "api.ts", self._frontend_api_client())

        # === BACKEND (FastAPI) ===
        be_dir = Path(tmpdir) / f"{app_slug}-backend"
        self._write_file(be_dir / "app" / "main.py", self._backend_main_py(app_slug))
        self._write_file(be_dir / "app" / "core" / "database.py", self._backend_database_py())
        self._write_file(be_dir / "app" / "core" / "config.py", self._backend_config_py())
        self._write_file(be_dir / "app" / "core" / "security.py", self._backend_security_py())
        self._write_file(be_dir / "app" / "models" / "user.py", self._backend_user_model())
        self._write_file(be_dir / "app" / "schemas" / "user.py", self._backend_user_schema())
        self._write_file(be_dir / "app" / "routers" / "auth.py", self._backend_auth_router())
        self._write_file(be_dir / "app" / "routers" / "items.py", self._backend_items_router(features_list))
        self._write_file(be_dir / "alembic" / "env.py", self._backend_alembic_env())
        self._write_file(be_dir / "docker-compose.yml", self._backend_docker_compose(app_slug))
        self._write_file(be_dir / "requirements.txt", self._backend_requirements())
        self._write_file(be_dir / "Dockerfile", self._backend_dockerfile())
        self._write_file(be_dir / "README.md", self._backend_readme(app_slug, app_description, features_list, analysis))

        # === ZIP ===
        zip_path = STORAGE_DIR / f"{app_slug}_{job.id}.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, _dirs, files in os.walk(tmpdir):
                for file in files:
                    file_path = Path(root) / file
                    arcname = str(file_path.relative_to(tmpdir))
                    zf.write(file_path, arcname)

        # Cleanup temp
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)

        return zip_path

    def _write_file(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def _slugify(self, text: str) -> str:
        import re
        return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40]

    # ---------- Frontend Templates ----------

    def _frontend_package_json(self, app_slug: str) -> str:
        return f'''{{
  "name": "{app_slug}-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {{
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  }},
  "dependencies": {{
    "next": "14.2.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  }},
  "devDependencies": {{
    "typescript": "^5.4.0",
    "@types/node": "^20.0.0",
    "@types/react": "^18.2.0",
    "tailwindcss": "^3.4.0",
    "postcss": "^8.4.0",
    "autoprefixer": "^10.4.0"
  }}
}}
'''

    def _frontend_tailwind_config(self) -> str:
        return '''/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
'''

    def _frontend_home_page(self, description: str) -> str:
        return f'''export default function Home() {{
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-gradient-to-br from-slate-900 to-slate-800 text-white">
      <h1 className="text-5xl font-bold mb-6">Bienvenido</h1>
      <p className="text-xl max-w-2xl text-center text-slate-300">
        {description.replace(chr(10), ' ')}
      </p>
      <div className="mt-10 flex gap-4">
        <a href="/auth" className="px-6 py-3 bg-indigo-600 rounded-lg hover:bg-indigo-700 transition">Iniciar Sesión</a>
        <a href="/dashboard" className="px-6 py-3 border border-slate-500 rounded-lg hover:bg-slate-700 transition">Dashboard</a>
      </div>
    </main>
  );
}}
'''

    def _frontend_auth_page(self) -> str:
        return '''"use client";
import { useState } from "react";

export default function AuthPage() {
  const [mode, setMode] = useState<"login" | "register">("login");
  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-950 text-white">
      <div className="w-full max-w-md p-8 bg-slate-900 rounded-2xl border border-slate-800">
        <h2 className="text-2xl font-bold mb-6">{mode === "login" ? "Iniciar Sesión" : "Crear Cuenta"}</h2>
        <form className="space-y-4">
          <input type="email" placeholder="Email" className="w-full px-4 py-2 bg-slate-800 rounded border border-slate-700 focus:outline-none focus:border-indigo-500" />
          <input type="password" placeholder="Contraseña" className="w-full px-4 py-2 bg-slate-800 rounded border border-slate-700 focus:outline-none focus:border-indigo-500" />
          <button type="submit" className="w-full py-2 bg-indigo-600 rounded hover:bg-indigo-700 transition">{mode === "login" ? "Entrar" : "Registrarse"}</button>
        </form>
        <p className="mt-4 text-sm text-slate-400 text-center">
          {mode === "login" ? "¿No tienes cuenta? " : "¿Ya tienes cuenta? "}
          <button onClick={() => setMode(mode === "login" ? "register" : "login")} className="text-indigo-400 hover:underline">{mode === "login" ? "Regístrate" : "Inicia sesión"}</button>
        </p>
      </div>
    </div>
  );
}
'''

    def _frontend_dashboard_page(self, features: List[AppFeatureCreate]) -> str:
        cards = "\n".join(
            f'        <Card title="{f.feature_name}" description="{f.description or ""}" />'
            for f in features[:6]
        ) if features else '        <Card title="Bienvenido" description="Tu dashboard está listo." />'
        return f'''"use client";
import Card from "@/components/Card";
import Layout from "@/components/Layout";

export default function Dashboard() {{
  return (
    <Layout>
      <div className="p-6">
        <h1 className="text-3xl font-bold text-white mb-6">Dashboard</h1>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
{cards}
        </div>
      </div>
    </Layout>
  );
}}
'''

    def _frontend_settings_page(self) -> str:
        return '''"use client";
import Layout from "@/components/Layout";

export default function Settings() {
  return (
    <Layout>
      <div className="p-6 max-w-2xl">
        <h1 className="text-3xl font-bold text-white mb-6">Configuración</h1>
        <div className="space-y-4 bg-slate-900 p-6 rounded-xl border border-slate-800">
          <div>
            <label className="block text-sm text-slate-400 mb-1">Nombre de la empresa</label>
            <input type="text" className="w-full px-4 py-2 bg-slate-800 rounded border border-slate-700 text-white" defaultValue="Mi Negocio" />
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-1">Email de contacto</label>
            <input type="email" className="w-full px-4 py-2 bg-slate-800 rounded border border-slate-700 text-white" defaultValue="hola@ejemplo.com" />
          </div>
          <button className="px-6 py-2 bg-indigo-600 rounded text-white hover:bg-indigo-700 transition">Guardar cambios</button>
        </div>
      </div>
    </Layout>
  );
}
'''

    def _frontend_layout_component(self) -> str:
        return '''import Link from "next/link";

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-slate-950 text-white">
      <nav className="border-b border-slate-800 bg-slate-900/50 backdrop-blur">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
          <Link href="/" className="text-xl font-bold text-indigo-400">MVP</Link>
          <div className="flex gap-6 text-sm text-slate-300">
            <Link href="/dashboard" className="hover:text-white transition">Dashboard</Link>
            <Link href="/settings" className="hover:text-white transition">Settings</Link>
          </div>
        </div>
      </nav>
      <main>{children}</main>
    </div>
  );
}
'''

    def _frontend_form_input(self) -> str:
        return '''interface FormInputProps {
  label: string;
  type?: string;
  value: string;
  onChange: (val: string) => void;
}

export default function FormInput({ label, type = "text", value, onChange }: FormInputProps) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-sm text-slate-400">{label}</label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="px-4 py-2 bg-slate-800 rounded border border-slate-700 text-white focus:outline-none focus:border-indigo-500"
      />
    </div>
  );
}
'''

    def _frontend_data_table(self) -> str:
        return '''interface Column<T> {
  key: keyof T;
  title: string;
}

export default function DataTable<T extends Record<string, any>>({ columns, rows }: { columns: Column<T>[]; rows: T[] }) {
  return (
    <div className="overflow-x-auto rounded-xl border border-slate-800">
      <table className="w-full text-left text-sm text-slate-300">
        <thead className="bg-slate-900 text-slate-400">
          <tr>
            {columns.map((c) => (
              <th key={String(c.key)} className="px-4 py-3 font-medium">{c.title}</th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800">
          {rows.map((row, i) => (
            <tr key={i} className="bg-slate-900/50 hover:bg-slate-800/50">
              {columns.map((c) => (
                <td key={String(c.key)} className="px-4 py-3">{String(row[c.key])}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
'''

    def _frontend_card_component(self) -> str:
        return '''export default function Card({ title, description }: { title: string; description?: string }) {
  return (
    <div className="p-5 bg-slate-900 rounded-xl border border-slate-800 hover:border-indigo-500/50 transition">
      <h3 className="text-lg font-semibold text-white mb-1">{title}</h3>
      <p className="text-sm text-slate-400">{description}</p>
    </div>
  );
}
'''

    def _frontend_api_client(self) -> str:
        return '''const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function apiFetch(path: string, options?: RequestInit) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
'''

    # ---------- Backend Templates ----------

    def _backend_main_py(self, app_slug: str) -> str:
        return f'''from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, items

app = FastAPI(title="{app_slug.title()} API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(items.router, prefix="/items", tags=["items"])

@app.get("/health")
async def health():
    return {{"status": "ok"}}
'''

    def _backend_database_py(self) -> str:
        return '''from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

DATABASE_URL = "postgresql+asyncpg://user:password@db:5432/appdb"

engine = create_async_engine(DATABASE_URL, echo=False, future=True)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
'''

    def _backend_config_py(self) -> str:
        return '''from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://user:password@db:5432/appdb"
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    class Config:
        env_file = ".env"

settings = Settings()
'''

    def _backend_security_py(self) -> str:
        return '''from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import jwt
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
'''

    def _backend_user_model(self) -> str:
        return '''import uuid
from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
from datetime import datetime, timezone


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
'''

    def _backend_user_schema(self) -> str:
        return '''from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime


class UserBase(BaseModel):
    email: str


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: UUID
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
'''

    def _backend_auth_router(self) -> str:
        return '''from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, Token

router = APIRouter()


@router.post("/register", response_model=UserResponse)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email ya registrado")
    user = User(email=data.email, hashed_password=get_password_hash(data.password))
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login", response_model=Token)
async def login(data: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token}
'''

    def _backend_items_router(self, features: List[AppFeatureCreate]) -> str:
        feature_names = ", ".join(f'"{f.feature_name}"' for f in features[:5]) if features else '"items"'
        return f'''from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db

router = APIRouter()


@router.get("/")
async def list_items(db: AsyncSession = Depends(get_db)):
    # TODO: reemplazar con tu modelo real
    return {{"items": [{feature_names}]}}


@router.post("/")
async def create_item(name: str, db: AsyncSession = Depends(get_db)):
    return {{"id": "uuid-here", "name": name}}
'''

    def _backend_alembic_env(self) -> str:
        return '''from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
from app.core.database import Base
from app.core.config import settings

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(config.get_section(config.config_ini_section, {}), prefix="sqlalchemy.", poolclass=pool.NullPool)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    import asyncio
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
'''

    def _backend_docker_compose(self, app_slug: str) -> str:
        return f'''version: "3.9"
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: appdb
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  backend:
    build: ./
    environment:
      DATABASE_URL: postgresql+asyncpg://user:password@db:5432/appdb
      SECRET_KEY: change-me-in-production
    ports:
      - "8000:8000"
    depends_on:
      - db

  frontend:
    build: ./{app_slug}-frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend

volumes:
  pgdata:
'''

    def _backend_requirements(self) -> str:
        return '''fastapi==0.111.0
uvicorn[standard]==0.30.0
sqlalchemy[asyncio]==2.0.30
asyncpg==0.29.0
alembic==1.13.1
pydantic==2.7.0
pydantic-settings==2.2.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.9
'''

    def _backend_dockerfile(self) -> str:
        return '''FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
'''

    def _backend_readme(
        self,
        app_slug: str,
        description: str,
        features: List[AppFeatureCreate],
        analysis: str,
    ) -> str:
        features_md = "\n".join(f"- {f.feature_name}: {f.description or ''}" for f in features)
        return f'''# {app_slug.title()}

{description}

## Features
{features_md}

## Arquitectura
{analysis or "Next.js 14 frontend + FastAPI backend + PostgreSQL."}

## Levantar localmente

```bash
docker-compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs
'''

    def _build_preview_instructions(self, job: AppBuildJob, features: List[AppFeatureCreate]) -> str:
        features_text = "\n".join(f"- {f.feature_name}" for f in features)
        return f"""# Instrucciones de despliegue — {job.app_name}

## Estructura generada
- `{self._slugify(job.app_name)}-frontend/`: Next.js 14 + Tailwind CSS
- `{self._slugify(job.app_name)}-backend/`: FastAPI + SQLAlchemy async + Alembic

## Requisitos
- Docker & docker-compose
- Node.js 20+ (si corres frontend sin Docker)
- Python 3.11+ (si corres backend sin Docker)

## Pasos
1. Descomprime el ZIP.
2. `cd {self._slugify(job.app_name)}-backend && docker-compose up --build`
3. Accede a:
   - Frontend: http://localhost:3000
   - Backend: http://localhost:8000
   - Docs: http://localhost:8000/docs

## Features incluidas
{features_text}
"""

    # ========== Download ==========

    async def get_app_code(self, job_id: uuid.UUID) -> Optional[Path]:
        job = await self.get_job(job_id)
        if not job or not job.code_zip_url:
            return None
        filename = job.code_zip_url.split("/")[-1]
        path = STORAGE_DIR / filename
        return path if path.exists() else None
