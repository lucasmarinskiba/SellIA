"""CRM Builder Service

Genera código completo de sistemas CRM (Next.js frontend + FastAPI backend)
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
from app.domains.agents.crm_builder.models import CRMBuildJob, CRMModule, CRMBuildStatus
from app.domains.agents.crm_builder.schemas import CRMBuildJobCreate, CRMModuleCreate

logger = get_logger(__name__)

STORAGE_DIR = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))) / "storage" / "exports"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

ALL_CRM_MODULES = [
    "contacts", "deals", "pipeline", "tasks", "calendar", "reservations", "automations",
    "dashboard", "landing",
]


class CRMBuilderService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ========== CRUD ==========

    async def create_job(self, data: CRMBuildJobCreate) -> CRMBuildJob:
        job = CRMBuildJob(
            business_id=data.business_id,
            crm_name=data.crm_name,
            modules=[m.model_dump() for m in data.modules],
            status=CRMBuildStatus.PENDING,
        )
        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)

        for mod in data.modules:
            self.db.add(CRMModule(
                job_id=job.id,
                module_name=mod.module_name,
                config=mod.config,
            ))
        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def get_job(self, job_id: uuid.UUID) -> Optional[CRMBuildJob]:
        result = await self.db.execute(select(CRMBuildJob).where(CRMBuildJob.id == job_id))
        return result.scalar_one_or_none()

    async def list_jobs(self, business_id: uuid.UUID, limit: int = 100, offset: int = 0) -> List[CRMBuildJob]:
        result = await self.db.execute(
            select(CRMBuildJob)
            .where(CRMBuildJob.business_id == business_id)
            .order_by(desc(CRMBuildJob.created_at))
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    async def update_job(self, job_id: uuid.UUID, **kwargs) -> Optional[CRMBuildJob]:
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

    async def generate_crm(
        self,
        business_id: uuid.UUID,
        modules_list: List[CRMModuleCreate],
    ) -> CRMBuildJob:
        job = await self.create_job(CRMBuildJobCreate(
            business_id=business_id,
            crm_name="SellCRM",
            modules=modules_list,
        ))
        await self.update_job(job.id, status=CRMBuildStatus.GENERATING)

        try:
            zip_path = self._generate_code_zip(job, modules_list)
            relative_url = f"/storage/exports/{zip_path.name}"
            await self.update_job(
                job.id,
                status=CRMBuildStatus.COMPLETED,
                code_url=relative_url,
            )
        except Exception as e:
            logger.exception(f"CRMBuilder generation failed for job {job.id}: {e}")
            await self.update_job(job.id, status=CRMBuildStatus.FAILED)

        return await self.get_job(job.id)

    def _generate_code_zip(self, job: CRMBuildJob, modules_list: List[CRMModuleCreate]) -> Path:
        tmpdir = tempfile.mkdtemp(prefix=f"crm_build_{job.id}_")
        crm_slug = "sellcrm"
        active_modules = {m.module_name for m in modules_list}
        if not active_modules:
            active_modules = set(ALL_CRM_MODULES)

        # === FRONTEND (Next.js) ===
        fe_dir = Path(tmpdir) / f"{crm_slug}-frontend"
        self._write_file(fe_dir / "package.json", self._frontend_package_json(crm_slug))
        self._write_file(fe_dir / "tailwind.config.js", self._frontend_tailwind_config())
        self._write_file(fe_dir / "src" / "app" / "layout.tsx", self._frontend_root_layout())
        self._write_file(fe_dir / "src" / "app" / "page.tsx", self._frontend_landing_page())
        self._write_file(fe_dir / "src" / "app" / "dashboard" / "page.tsx", self._frontend_dashboard_page(active_modules))
        self._write_file(fe_dir / "src" / "app" / "contacts" / "page.tsx", self._frontend_contacts_page())
        self._write_file(fe_dir / "src" / "app" / "deals" / "page.tsx", self._frontend_deals_page())
        self._write_file(fe_dir / "src" / "app" / "tasks" / "page.tsx", self._frontend_tasks_page())
        self._write_file(fe_dir / "src" / "app" / "calendar" / "page.tsx", self._frontend_calendar_page())
        self._write_file(fe_dir / "src" / "app" / "reservations" / "page.tsx", self._frontend_reservations_page())
        self._write_file(fe_dir / "src" / "app" / "automations" / "page.tsx", self._frontend_automations_page())
        self._write_file(fe_dir / "src" / "components" / "Layout.tsx", self._frontend_layout_component())
        self._write_file(fe_dir / "src" / "components" / "KanbanBoard.tsx", self._frontend_kanban_component())
        self._write_file(fe_dir / "src" / "components" / "LeadForm.tsx", self._frontend_lead_form())
        self._write_file(fe_dir / "src" / "lib" / "api.ts", self._frontend_api_client())

        # === BACKEND (FastAPI) ===
        be_dir = Path(tmpdir) / f"{crm_slug}-backend"
        self._write_file(be_dir / "app" / "main.py", self._backend_main_py())
        self._write_file(be_dir / "app" / "core" / "database.py", self._backend_database_py())
        self._write_file(be_dir / "app" / "core" / "security.py", self._backend_security_py())
        self._write_file(be_dir / "app" / "models" / "contact.py", self._backend_contact_model())
        self._write_file(be_dir / "app" / "models" / "deal.py", self._backend_deal_model())
        self._write_file(be_dir / "app" / "models" / "task.py", self._backend_task_model())
        self._write_file(be_dir / "app" / "models" / "reservation.py", self._backend_reservation_model())
        self._write_file(be_dir / "app" / "schemas" / "contact.py", self._backend_contact_schema())
        self._write_file(be_dir / "app" / "schemas" / "deal.py", self._backend_deal_schema())
        self._write_file(be_dir / "app" / "routers" / "contacts.py", self._backend_contacts_router())
        self._write_file(be_dir / "app" / "routers" / "deals.py", self._backend_deals_router())
        self._write_file(be_dir / "app" / "routers" / "tasks.py", self._backend_tasks_router())
        self._write_file(be_dir / "app" / "routers" / "calendar.py", self._backend_calendar_router())
        self._write_file(be_dir / "app" / "routers" / "reservations.py", self._backend_reservations_router())
        self._write_file(be_dir / "app" / "routers" / "automations.py", self._backend_automations_router())
        self._write_file(be_dir / "alembic" / "env.py", self._backend_alembic_env())
        self._write_file(be_dir / "docker-compose.yml", self._backend_docker_compose())
        self._write_file(be_dir / "requirements.txt", self._backend_requirements())
        self._write_file(be_dir / "Dockerfile", self._backend_dockerfile())
        self._write_file(be_dir / "README.md", self._backend_readme(active_modules))

        # === ZIP ===
        zip_path = STORAGE_DIR / f"{crm_slug}_{job.id}.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, _dirs, files in os.walk(tmpdir):
                for file in files:
                    file_path = Path(root) / file
                    arcname = str(file_path.relative_to(tmpdir))
                    zf.write(file_path, arcname)

        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)

        return zip_path

    def _write_file(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    # ---------- Frontend Templates ----------

    def _frontend_package_json(self, crm_slug: str) -> str:
        return f'''{{
  "name": "{crm_slug}-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {{
    "dev": "next dev",
    "build": "next build",
    "start": "next start"
  }},
  "dependencies": {{
    "next": "14.2.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "recharts": "^2.12.0"
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
  content: ['./src/**/*.{js,ts,jsx,tsx,mdx}'],
  theme: { extend: {} },
  plugins: [],
}
'''

    def _frontend_root_layout(self) -> str:
        return '''export const metadata = {
  title: 'SellCRM',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body className="bg-slate-950 text-white">{children}</body>
    </html>
  )
}
'''

    def _frontend_landing_page(self) -> str:
        return '''"use client";
import LeadForm from "@/components/LeadForm";

export default function Landing() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-6 bg-gradient-to-br from-slate-900 to-slate-800">
      <h1 className="text-5xl font-bold mb-4">SellCRM</h1>
      <p className="text-lg text-slate-300 mb-8 max-w-xl text-center">
        Gestiona contactos, deals, tareas y reservas en un solo lugar.
      </p>
      <div className="w-full max-w-md">
        <LeadForm />
      </div>
    </main>
  );
}
'''

    def _frontend_dashboard_page(self, active_modules: set) -> str:
        cards = []
        if "contacts" in active_modules:
            cards.append('        <KpiCard title="Contactos" value="1,240" trend="+5%" />')
        if "deals" in active_modules:
            cards.append('        <KpiCard title="Deals abiertos" value="$340K" trend="+12%" />')
        if "tasks" in active_modules:
            cards.append('        <KpiCard title="Tareas hoy" value="18" trend="-2" />')
        if "reservations" in active_modules:
            cards.append('        <KpiCard title="Reservas" value="42" trend="+8%" />')
        if not cards:
            cards.append('        <KpiCard title="Bienvenido" value="SellCRM" trend="Vamos" />')
        cards_str = "\n".join(cards)
        return f'''"use client";
import Layout from "@/components/Layout";

function KpiCard({{ title, value, trend }}: {{ title: string; value: string; trend: string }}) {{
  return (
    <div className="p-5 bg-slate-900 rounded-xl border border-slate-800">
      <p className="text-sm text-slate-400">{{title}}</p>
      <p className="text-2xl font-bold text-white mt-1">{{value}}</p>
      <p className="text-xs text-emerald-400 mt-1">{{trend}}</p>
    </div>
  );
}}

export default function Dashboard() {{
  return (
    <Layout>
      <div className="p-6">
        <h1 className="text-3xl font-bold text-white mb-6">Dashboard</h1>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
{cards_str}
        </div>
        <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
          <h2 className="text-lg font-semibold mb-4">Actividad reciente</h2>
          <ul className="space-y-3 text-sm text-slate-300">
            <li>Nuevo contacto: Juan Pérez</li>
            <li>Deal movido a "Negociación"</li>
            <li>Tarea completada: Seguimiento lead #42</li>
          </ul>
        </div>
      </div>
    </Layout>
  );
}}
'''

    def _frontend_contacts_page(self) -> str:
        return '''"use client";
import Layout from "@/components/Layout";

export default function Contacts() {
  return (
    <Layout>
      <div className="p-6">
        <h1 className="text-3xl font-bold text-white mb-6">Contactos</h1>
        <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-800 text-slate-400">
              <tr><th className="px-4 py-3">Nombre</th><th className="px-4 py-3">Email</th><th className="px-4 py-3">Teléfono</th><th className="px-4 py-3">Etiquetas</th></tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              <tr className="hover:bg-slate-800/50"><td className="px-4 py-3">Ana López</td><td className="px-4 py-3">ana@ejemplo.com</td><td className="px-4 py-3">+54 9 11 2222 3333</td><td className="px-4 py-3"><span className="px-2 py-1 bg-indigo-600/20 text-indigo-400 rounded text-xs">Lead</span></td></tr>
              <tr className="hover:bg-slate-800/50"><td className="px-4 py-3">Carlos Ruiz</td><td className="px-4 py-3">carlos@empresa.com</td><td className="px-4 py-3">+54 9 11 4444 5555</td><td className="px-4 py-3"><span className="px-2 py-1 bg-emerald-600/20 text-emerald-400 rounded text-xs">Cliente</span></td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </Layout>
  );
}
'''

    def _frontend_deals_page(self) -> str:
        return '''"use client";
import Layout from "@/components/Layout";
import KanbanBoard from "@/components/KanbanBoard";

export default function Deals() {
  return (
    <Layout>
      <div className="p-6">
        <h1 className="text-3xl font-bold text-white mb-6">Deals / Pipeline</h1>
        <KanbanBoard />
      </div>
    </Layout>
  );
}
'''

    def _frontend_tasks_page(self) -> str:
        return '''"use client";
import Layout from "@/components/Layout";

export default function Tasks() {
  return (
    <Layout>
      <div className="p-6">
        <h1 className="text-3xl font-bold text-white mb-6">Tareas</h1>
        <div className="space-y-3">
          {[
            { title: "Seguimiento lead #42", due: "Hoy", assignee: "Ana" },
            { title: "Enviar propuesta a TechCorp", due: "Mañana", assignee: "Luis" },
            { title: "Llamada de cierre", due: "Viernes", assignee: "Ana" },
          ].map((t, i) => (
            <div key={i} className="flex items-center justify-between p-4 bg-slate-900 rounded-xl border border-slate-800">
              <div>
                <p className="font-medium text-white">{t.title}</p>
                <p className="text-xs text-slate-400">Vence: {t.due} • Asignado: {t.assignee}</p>
              </div>
              <input type="checkbox" className="w-5 h-5 accent-indigo-600" />
            </div>
          ))}
        </div>
      </div>
    </Layout>
  );
}
'''

    def _frontend_calendar_page(self) -> str:
        return '''"use client";
import Layout from "@/components/Layout";

export default function CalendarPage() {
  return (
    <Layout>
      <div className="p-6">
        <h1 className="text-3xl font-bold text-white mb-6">Calendario</h1>
        <div className="grid grid-cols-7 gap-2 text-center text-slate-400 text-sm mb-2">
          {["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"].map(d => <div key={d}>{d}</div>)}
        </div>
        <div className="grid grid-cols-7 gap-2">
          {Array.from({ length: 31 }, (_, i) => (
            <div key={i} className="h-24 bg-slate-900 rounded border border-slate-800 p-2 text-left">
              <span className="text-xs text-slate-500">{i + 1}</span>
              {i === 14 && <div className="mt-1 text-xs bg-indigo-600/20 text-indigo-400 rounded px-1">Demo TechCorp</div>}
              {i === 22 && <div className="mt-1 text-xs bg-emerald-600/20 text-emerald-400 rounded px-1">Cierre</div>}
            </div>
          ))}
        </div>
      </div>
    </Layout>
  );
}
'''

    def _frontend_reservations_page(self) -> str:
        return '''"use client";
import Layout from "@/components/Layout";

export default function Reservations() {
  return (
    <Layout>
      <div className="p-6">
        <h1 className="text-3xl font-bold text-white mb-6">Reservas</h1>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {["09:00","10:00","11:00","14:00","15:00","16:00"].map((slot) => (
            <div key={slot} className="p-4 bg-slate-900 rounded-xl border border-slate-800 flex items-center justify-between">
              <span className="text-white font-medium">{slot}</span>
              <button className="px-3 py-1 bg-indigo-600 rounded text-sm hover:bg-indigo-700 transition">Reservar</button>
            </div>
          ))}
        </div>
      </div>
    </Layout>
  );
}
'''

    def _frontend_automations_page(self) -> str:
        return '''"use client";
import Layout from "@/components/Layout";

export default function Automations() {
  return (
    <Layout>
      <div className="p-6">
        <h1 className="text-3xl font-bold text-white mb-6">Automations</h1>
        <div className="space-y-3">
          {[
            { name: "Bienvenida nuevo lead", trigger: "Nuevo contacto", action: "Enviar email" },
            { name: "Recordatorio cita", trigger: "1h antes", action: "WhatsApp" },
            { name: "Deal estancado", trigger: "7 días sin actividad", action: "Notificar owner" },
          ].map((a, i) => (
            <div key={i} className="p-4 bg-slate-900 rounded-xl border border-slate-800">
              <p className="font-medium text-white">{a.name}</p>
              <p className="text-xs text-slate-400">Trigger: {a.trigger} → Action: {a.action}</p>
            </div>
          ))}
        </div>
      </div>
    </Layout>
  );
}
'''

    def _frontend_layout_component(self) -> str:
        return '''"use client";
import Link from "next/link";

const nav = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/contacts", label: "Contactos" },
  { href: "/deals", label: "Deals" },
  { href: "/tasks", label: "Tareas" },
  { href: "/calendar", label: "Calendario" },
  { href: "/reservations", label: "Reservas" },
  { href: "/automations", label: "Automations" },
];

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-slate-950 text-white">
      <nav className="border-b border-slate-800 bg-slate-900/50 backdrop-blur sticky top-0">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
          <Link href="/" className="text-xl font-bold text-indigo-400">SellCRM</Link>
          <div className="flex gap-5 text-sm text-slate-300">
            {nav.map((n) => (
              <Link key={n.href} href={n.href} className="hover:text-white transition">{n.label}</Link>
            ))}
          </div>
        </div>
      </nav>
      <main>{children}</main>
    </div>
  );
}
'''

    def _frontend_kanban_component(self) -> str:
        return '''"use client";

const columns = ["Nuevo", "Calificado", "Propuesta", "Negociación", "Cerrado"];
const deals = [
  { title: "TechCorp", value: "$50K", stage: "Negociación" },
  { title: "Acme SA", value: "$12K", stage: "Propuesta" },
  { title: "Global Inc", value: "$80K", stage: "Nuevo" },
];

export default function KanbanBoard() {
  return (
    <div className="flex gap-4 overflow-x-auto pb-2">
      {columns.map((col) => (
        <div key={col} className="min-w-[240px] bg-slate-900 rounded-xl border border-slate-800 p-3">
          <h3 className="text-sm font-semibold text-slate-300 mb-3">{col}</h3>
          <div className="space-y-2">
            {deals.filter((d) => d.stage === col).map((d) => (
              <div key={d.title} className="p-3 bg-slate-800 rounded border border-slate-700">
                <p className="text-white text-sm font-medium">{d.title}</p>
                <p className="text-xs text-indigo-400 mt-1">{d.value}</p>
              </div>
            ))}
            {deals.filter((d) => d.stage === col).length === 0 && (
              <p className="text-xs text-slate-600">Sin deals</p>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
'''

    def _frontend_lead_form(self) -> str:
        return '''"use client";
import { useState } from "react";

export default function LeadForm() {
  const [email, setEmail] = useState("");
  return (
    <form className="space-y-3" onSubmit={(e) => e.preventDefault()}>
      <h3 className="text-lg font-semibold text-white">Solicita una demo</h3>
      <input
        type="email"
        placeholder="tu@email.com"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        className="w-full px-4 py-2 bg-slate-800 rounded border border-slate-700 text-white focus:outline-none focus:border-indigo-500"
      />
      <button className="w-full py-2 bg-indigo-600 rounded text-white hover:bg-indigo-700 transition">Enviar</button>
    </form>
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

    def _backend_main_py(self) -> str:
        return '''from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import contacts, deals, tasks, calendar, reservations, automations

app = FastAPI(title="SellCRM API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(contacts.router, prefix="/contacts", tags=["contacts"])
app.include_router(deals.router, prefix="/deals", tags=["deals"])
app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
app.include_router(calendar.router, prefix="/calendar", tags=["calendar"])
app.include_router(reservations.router, prefix="/reservations", tags=["reservations"])
app.include_router(automations.router, prefix="/automations", tags=["automations"])

@app.get("/health")
async def health():
    return {"status": "ok"}
'''

    def _backend_database_py(self) -> str:
        return '''from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

DATABASE_URL = "postgresql+asyncpg://user:password@db:5432/crm"
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

    def _backend_security_py(self) -> str:
        return '''from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import jwt

SECRET_KEY = "change-me-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
'''

    def _backend_contact_model(self) -> str:
        return '''import uuid
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base
from datetime import datetime, timezone


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    tags = Column(JSONB, default=list, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
'''

    def _backend_deal_model(self) -> str:
        return '''import uuid
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
from datetime import datetime, timezone


class Deal(Base):
    __tablename__ = "deals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contact_id = Column(UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    stage = Column(String(50), default="nuevo", nullable=False, index=True)
    value = Column(Integer, default=0, nullable=False)
    currency = Column(String(10), default="USD", nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
'''

    def _backend_task_model(self) -> str:
        return '''import uuid
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
from datetime import datetime, timezone


class Task(Base):
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    assignee = Column(String(255), nullable=True)
    due_date = Column(DateTime(timezone=True), nullable=True)
    is_done = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
'''

    def _backend_reservation_model(self) -> str:
        return '''import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
from datetime import datetime, timezone


class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contact_id = Column(UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True, index=True)
    start_at = Column(DateTime(timezone=True), nullable=False)
    end_at = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(20), default="confirmed", nullable=False)
    notes = Column(String(1000), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
'''

    def _backend_contact_schema(self) -> str:
        return '''from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional, List


class ContactBase(BaseModel):
    email: str
    name: str
    phone: Optional[str] = None
    tags: List[str] = []
    notes: Optional[str] = None


class ContactCreate(ContactBase):
    pass


class ContactUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None


class ContactResponse(ContactBase):
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
'''

    def _backend_deal_schema(self) -> str:
        return '''from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional


class DealBase(BaseModel):
    title: str
    stage: str = "nuevo"
    value: int = 0
    currency: str = "USD"


class DealCreate(DealBase):
    contact_id: Optional[UUID] = None


class DealResponse(DealBase):
    id: UUID
    contact_id: Optional[UUID] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
'''

    def _backend_contacts_router(self) -> str:
        return '''from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.contact import Contact
from app.schemas.contact import ContactCreate, ContactUpdate, ContactResponse

router = APIRouter()


@router.get("/", response_model=list[ContactResponse])
async def list_contacts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Contact).order_by(Contact.created_at.desc()))
    return result.scalars().all()


@router.post("/", response_model=ContactResponse)
async def create_contact(data: ContactCreate, db: AsyncSession = Depends(get_db)):
    contact = Contact(**data.model_dump())
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact


@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(contact_id: str, db: AsyncSession = Depends(get_db)):
    from uuid import UUID
    result = await db.execute(select(Contact).where(Contact.id == UUID(contact_id)))
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Contacto no encontrado")
    return contact


@router.patch("/{contact_id}", response_model=ContactResponse)
async def update_contact(contact_id: str, data: ContactUpdate, db: AsyncSession = Depends(get_db)):
    from uuid import UUID
    result = await db.execute(select(Contact).where(Contact.id == UUID(contact_id)))
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Contacto no encontrado")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(contact, k, v)
    await db.commit()
    await db.refresh(contact)
    return contact


@router.delete("/{contact_id}")
async def delete_contact(contact_id: str, db: AsyncSession = Depends(get_db)):
    from uuid import UUID
    result = await db.execute(select(Contact).where(Contact.id == UUID(contact_id)))
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Contacto no encontrado")
    await db.delete(contact)
    await db.commit()
    return {"message": "Eliminado"}
'''

    def _backend_deals_router(self) -> str:
        return '''from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.models.deal import Deal
from app.schemas.deal import DealCreate, DealResponse

router = APIRouter()


@router.get("/", response_model=list[DealResponse])
async def list_deals(stage: str | None = None, db: AsyncSession = Depends(get_db)):
    query = select(Deal)
    if stage:
        query = query.where(Deal.stage == stage)
    result = await db.execute(query.order_by(Deal.created_at.desc()))
    return result.scalars().all()


@router.post("/", response_model=DealResponse)
async def create_deal(data: DealCreate, db: AsyncSession = Depends(get_db)):
    deal = Deal(**data.model_dump())
    db.add(deal)
    await db.commit()
    await db.refresh(deal)
    return deal


@router.get("/pipeline/summary")
async def pipeline_summary(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Deal.stage, func.count(Deal.id), func.sum(Deal.value)).group_by(Deal.stage))
    rows = result.all()
    return [{"stage": r[0], "count": r[1], "value": r[2] or 0} for r in rows]
'''

    def _backend_tasks_router(self) -> str:
        return '''from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.task import Task

router = APIRouter()


@router.get("/")
async def list_tasks(done: bool | None = None, db: AsyncSession = Depends(get_db)):
    query = select(Task)
    if done is not None:
        query = query.where(Task.is_done == done)
    result = await db.execute(query.order_by(Task.due_date))
    return result.scalars().all()


@router.post("/")
async def create_task(title: str, assignee: str | None = None, due_date: str | None = None, db: AsyncSession = Depends(get_db)):
    from datetime import datetime
    task = Task(title=title, assignee=assignee, due_date=datetime.fromisoformat(due_date) if due_date else None)
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task
'''

    def _backend_calendar_router(self) -> str:
        return '''from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.reservation import Reservation

router = APIRouter()


@router.get("/events")
async def list_events(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Reservation).order_by(Reservation.start_at))
    return result.scalars().all()
'''

    def _backend_reservations_router(self) -> str:
        return '''from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.reservation import Reservation

router = APIRouter()


@router.get("/availability")
async def availability(date: str, db: AsyncSession = Depends(get_db)):
    # Simplificado: devolver slots para la fecha
    return {"date": date, "slots": ["09:00","10:00","11:00","14:00","15:00","16:00"]}


@router.post("/")
async def create_reservation(contact_id: str, start_at: str, end_at: str, db: AsyncSession = Depends(get_db)):
    from datetime import datetime
    from uuid import UUID
    r = Reservation(contact_id=UUID(contact_id), start_at=datetime.fromisoformat(start_at), end_at=datetime.fromisoformat(end_at))
    db.add(r)
    await db.commit()
    await db.refresh(r)
    return r
'''

    def _backend_automations_router(self) -> str:
        return '''from fastapi import APIRouter

router = APIRouter()


@router.get("/workflows")
async def list_workflows():
    return [
        {"id": "wf-1", "name": "Bienvenida nuevo lead", "trigger": "new_contact", "active": True},
        {"id": "wf-2", "name": "Recordatorio cita", "trigger": "appointment_1h_before", "active": True},
    ]


@router.post("/workflows/{wf_id}/trigger")
async def trigger_workflow(wf_id: str, payload: dict):
    return {"workflow_id": wf_id, "triggered": True, "payload": payload}
'''

    def _backend_alembic_env(self) -> str:
        return '''from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
from app.core.database import Base

config = context.config
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

    def _backend_docker_compose(self) -> str:
        return '''version: "3.9"
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: crm
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  backend:
    build: ./
    environment:
      DATABASE_URL: postgresql+asyncpg://user:password@db:5432/crm
    ports:
      - "8000:8000"
    depends_on:
      - db

  frontend:
    build: ./sellcrm-frontend
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

    def _backend_readme(self, active_modules: set) -> str:
        modules_md = "\n".join(f"- {m}" for m in sorted(active_modules))
        return f'''# SellCRM

Sistema CRM completo generado por SellIA.

## Módulos activos
{modules_md}

## Levantar localmente

```bash
docker-compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs
'''

    # ========== Download ==========

    async def get_crm_code(self, job_id: uuid.UUID) -> Optional[Path]:
        job = await self.get_job(job_id)
        if not job or not job.code_url:
            return None
        filename = job.code_url.split("/")[-1]
        path = STORAGE_DIR / filename
        return path if path.exists() else None
