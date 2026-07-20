/**
 * Home `/` → Command Center.
 *
 * La página principal de SellIA es el cerebro (/sellia-brain): Command Center
 * enterprise con pipeline, audit log, procesamiento de IA y NeuralBrain.
 * La landing de marketing vive ahora en /landing.
 */

import { redirect } from 'next/navigation'

export default function HomePage(): never {
  redirect('/sellia-brain')
}
