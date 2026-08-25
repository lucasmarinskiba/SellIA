'use client';

import React, { useState } from 'react';
import { SecureSignupForm } from '@/components/SecureSignupForm';
import { TwoFactorSetup } from '@/components/TwoFactorSetup';
import Link from 'next/link';

export default function SignupPage() {
  const [step, setStep] = useState<'signup' | '2fa' | 'complete'>('signup');
  const [userId, setUserId] = useState<string | null>(null);

  const handleSignupSuccess = ({ userId: newUserId }: { userId: string; email: string }) => {
    setUserId(newUserId);
    setStep('2fa');
  };

  const handle2FAComplete = () => {
    setStep('complete');
    setTimeout(() => {
      window.location.href = '/dashboard';
    }, 2000);
  };

  const handle2FACancel = () => {
    setStep('signup');
    setUserId(null);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900">SellIA</h1>
          <p className="text-gray-600 mt-2">Tu vendedor IA 24/7</p>
        </div>

        {step === 'signup' && (
          <div>
            <SecureSignupForm
              onSuccess={handleSignupSuccess}
              onError={(error) => console.error('Signup error:', error)}
            />
            <div className="mt-6 text-center">
              <p className="text-sm text-gray-600">
                ¿Ya tenés cuenta?{' '}
                <Link href="/login" className="text-blue-600 hover:underline font-semibold">
                  Inicia sesión
                </Link>
              </p>
            </div>
          </div>
        )}

        {step === '2fa' && userId && (
          <div>
            <TwoFactorSetup
              userId={userId}
              onComplete={handle2FAComplete}
              onCancel={handle2FACancel}
            />
          </div>
        )}

        {step === 'complete' && (
          <div className="bg-white rounded-lg shadow-lg p-6 border border-gray-200 text-center">
            <div className="text-4xl mb-4">✓</div>
            <h2 className="text-2xl font-bold text-green-600 mb-2">¡Cuenta creada!</h2>
            <p className="text-gray-600 mb-4">
              Tu cuenta está segura con autenticación de dos factores.
            </p>
            <p className="text-sm text-gray-500">Redirigiendo a dashboard...</p>
          </div>
        )}

        <div className="mt-8 text-center text-xs text-gray-500">
          <p>© 2026 SellIA. Todos los derechos reservados.</p>
        </div>
      </div>
    </div>
  );
}
