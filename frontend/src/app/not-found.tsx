import Link from 'next/link'

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-[#060812] text-white p-6">
      <div className="text-center">
        <p className="text-7xl font-black bg-gradient-to-br from-brand-orange to-purple-500 bg-clip-text text-transparent mb-2">404</p>
        <h2 className="text-xl font-bold mb-1">Página no encontrada</h2>
        <p className="text-sm text-white/50 mb-6">La ruta que buscás no existe.</p>
        <Link
          href="/"
          className="inline-block px-5 py-2.5 rounded-xl bg-brand-orange/20 border border-brand-orange/30 text-brand-orange font-medium hover:bg-brand-orange/30 transition-all"
        >
          Volver al inicio
        </Link>
      </div>
    </div>
  )
}
