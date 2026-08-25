'use client';

import React, { useState } from 'react';
import Link from 'next/link';

type Plan = 'free' | 'pro' | 'enterprise';

const plans = [
  {
    id: 'free',
    name: 'Free',
    price: 0,
    description: 'Prueba gratis',
    features: [
      '1 agente',
      '1 canal',
      '50 conversaciones/mes',
      'Soporte por email',
    ],
    cta: 'Crear cuenta gratis',
  },
  {
    id: 'pro',
    name: 'Pro',
    price: 49,
    description: 'Lo más elegido',
    features: [
      '5 agentes',
      '14 canales',
      'Conversaciones ilimitadas',
      'Computer Use (3 sandbox)',
      'Manos libres (12 idiomas)',
      'Workflows + automatizaciones',
      'Soporte prioritario',
    ],
    cta: 'Comenzar Pro',
    popular: true,
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    price: null,
    description: 'Para equipos grandes',
    features: [
      'Agentes ilimitados',
      'API + SLA',
      'Onboarding dedicado',
      'Multi-tenant + RBAC',
      'Integraciones custom',
      'Audit + SSO',
    ],
    cta: 'Contactar ventas',
  },
];

export default function PricingPage() {
  const [selectedPlan, setSelectedPlan] = useState<Plan>('pro');
  const [isLoading, setIsLoading] = useState(false);

  const handleCheckout = async (planId: Plan) => {
    if (planId === 'free') {
      window.location.href = '/signup';
      return;
    }

    if (planId === 'enterprise') {
      // Send email
      window.location.href = 'mailto:ventas@sellia.io?subject=Plan Enterprise';
      return;
    }

    setIsLoading(true);
    try {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'https://sellia-production.up.railway.app';
      const response = await fetch(`${backendUrl}/api/v1/checkout/session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          plan: planId,
          currency: 'ARS',
        }),
      });

      const data = await response.json();
      if (data.checkout_url) {
        window.location.href = data.checkout_url;
      }
    } catch (err) {
      console.error('Checkout error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="border-b border-gray-200 sticky top-0 z-50 bg-white/95 backdrop-blur">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <Link href="/" className="text-2xl font-bold text-gray-900">
            SellIA
          </Link>
          <div className="space-x-4">
            <Link href="/login" className="text-gray-600 hover:text-gray-900">
              Ingresar
            </Link>
            <Link href="/signup" className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">
              Crear cuenta
            </Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="py-20 px-4 text-center">
        <h1 className="text-5xl font-bold text-gray-900 mb-4">
          Precios simples y justos
        </h1>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto">
          Elige el plan que mejor se adapte a tu negocio. Sin sorpresas, sin contratos de larga duración.
        </p>
      </section>

      {/* Pricing Cards */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 grid md:grid-cols-3 gap-8 mb-20">
        {plans.map((plan) => (
          <div
            key={plan.id}
            className={`rounded-lg border-2 p-8 transition ${
              plan.popular
                ? 'border-blue-600 bg-blue-50 shadow-lg scale-105'
                : 'border-gray-200 bg-white'
            }`}
          >
            {plan.popular && (
              <div className="text-blue-600 font-semibold mb-2 text-sm">
                ⭐ {plan.description}
              </div>
            )}

            <h3 className="text-2xl font-bold text-gray-900 mb-2">
              {plan.name}
            </h3>

            <div className="mb-6">
              {plan.price !== null ? (
                <>
                  <span className="text-4xl font-bold text-gray-900">
                    ${plan.price}
                  </span>
                  <span className="text-gray-600">/mes</span>
                </>
              ) : (
                <span className="text-2xl text-gray-600">Plan custom</span>
              )}
            </div>

            <button
              onClick={() => handleCheckout(plan.id as Plan)}
              disabled={isLoading}
              className={`w-full py-2 rounded-lg font-semibold mb-8 transition ${
                plan.popular
                  ? 'bg-blue-600 text-white hover:bg-blue-700'
                  : 'border-2 border-gray-300 text-gray-900 hover:border-gray-400'
              } disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              {isLoading ? 'Procesando...' : plan.cta}
            </button>

            <ul className="space-y-3 text-sm text-gray-600">
              {plan.features.map((feature, idx) => (
                <li key={idx} className="flex gap-2">
                  <span className="text-green-600 font-bold">✓</span>
                  {feature}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </section>

      {/* FAQ */}
      <section className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-20 border-t border-gray-200">
        <h2 className="text-3xl font-bold text-gray-900 mb-12 text-center">
          Preguntas frecuentes
        </h2>

        <div className="space-y-6">
          {[
            {
              q: '¿Puedo cambiar de plan?',
              a: 'Sí, puedes cambiar de plan en cualquier momento. Los cambios se reflejan en tu próxima facturación.',
            },
            {
              q: '¿Qué métodos de pago aceptan?',
              a: 'Aceptamos todas las tarjetas de crédito, débito y billeteras digitales a través de MercadoPago.',
            },
            {
              q: '¿Hay período de prueba?',
              a: 'Sí, el plan Free es completamente gratis y no requiere tarjeta de crédito.',
            },
            {
              q: '¿Puedo cancelar en cualquier momento?',
              a: 'Sí, puedes cancelar tu suscripción en cualquier momento sin penalizaciones.',
            },
          ].map((faq, idx) => (
            <div key={idx} className="border border-gray-200 rounded-lg p-6">
              <h3 className="font-semibold text-gray-900 mb-2">{faq.q}</h3>
              <p className="text-gray-600">{faq.a}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="bg-blue-600 text-white py-20 px-4 text-center">
        <h2 className="text-3xl font-bold mb-4">
          Comienza a vender con IA hoy
        </h2>
        <p className="text-lg text-blue-100 mb-8 max-w-2xl mx-auto">
          Sin tarjeta de crédito. Sin compromiso. Cancela cuando quieras.
        </p>
        <button
          onClick={() => handleCheckout('pro')}
          className="bg-white text-blue-600 px-8 py-3 rounded-lg font-semibold hover:bg-gray-100 transition"
        >
          Comenzar con Pro
        </button>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-400 py-12 px-4 text-center">
        <p>© 2026 SellIA. Todos los derechos reservados.</p>
      </footer>
    </div>
  );
}
