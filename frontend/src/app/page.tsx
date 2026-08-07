/**
 * Home `/` → Landing pública.
 *
 * La raíz del dominio es lo que Google indexa y lo que reciben los
 * backlinks: debe servir la landing de marketing (/landing), no el
 * Command Center interno (/sellia-brain), que requiere sesión y no
 * tiene contenido indexable para SEO.
 */

import { redirect } from 'next/navigation'

export default function HomePage(): never {
  redirect('/landing')
}
