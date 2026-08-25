import React, { useState } from 'react';

interface TwoFactorSetupProps {
  userId: string;
  onComplete: () => void;
  onCancel: () => void;
}

type Step = 'intro' | 'setup' | 'verify' | 'backup' | 'complete';

export const TwoFactorSetup: React.FC<TwoFactorSetupProps> = ({
  userId,
  onComplete,
  onCancel,
}) => {
  const [step, setStep] = useState<Step>('intro');
  const [qrCode, setQrCode] = useState<string | null>(null);
  const [secret, setSecret] = useState<string | null>(null);
  const [verificationCode, setVerificationCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleEnableClick = async () => {
    setLoading(true);
    setError(null);
    try {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
      const response = await fetch(`${backendUrl}/api/v1/auth/2fa/enable`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId }),
      });

      if (!response.ok) throw new Error('Failed to enable 2FA');

      const data = await response.json();
      setQrCode(data.qr_code);
      setSecret(data.secret);
      setStep('setup');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error enabling 2FA');
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async () => {
    if (!verificationCode || verificationCode.length !== 6) {
      setError('Código debe tener 6 dígitos');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
      const response = await fetch(`${backendUrl}/api/v1/auth/2fa/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          secret,
          totp_code: verificationCode,
        }),
      });

      if (!response.ok) throw new Error('Código 2FA inválido');

      setStep('backup');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error verificando código');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto p-6 bg-white rounded-lg shadow-lg border border-gray-200">
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">
          Autenticación de dos factores
        </h2>
        <p className="text-sm text-gray-600 mt-1">
          Protege tu cuenta con verificación en dos pasos
        </p>
      </div>

      {step === 'intro' && (
        <div className="space-y-4">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 space-y-3">
            <p className="text-sm font-semibold text-blue-900">
              ¿Por qué necesitas 2FA?
            </p>
            <ul className="text-xs text-blue-800 space-y-2">
              <li className="flex gap-2">
                <span>🔒</span>
                <span>Protege tu cuenta incluso si alguien obtiene tu contraseña</span>
              </li>
              <li className="flex gap-2">
                <span>📱</span>
                <span>Un código único que cambia cada 30 segundos</span>
              </li>
              <li className="flex gap-2">
                <span>✓</span>
                <span>Cumple con estándares de seguridad internacionales</span>
              </li>
            </ul>
          </div>

          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <p className="text-xs font-semibold text-gray-700 mb-2">REQUISITOS:</p>
            <ul className="text-xs text-gray-600 space-y-1">
              <li>✓ App autenticadora (Google, Microsoft, Authy)</li>
              <li>✓ Código QR o clave secreta</li>
              <li>✓ 2 minutos de tu tiempo</li>
            </ul>
          </div>

          <button
            onClick={handleEnableClick}
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold py-2 rounded-lg transition"
          >
            {loading ? 'Cargando...' : 'Configurar 2FA'}
          </button>

          <button
            onClick={onCancel}
            className="w-full bg-gray-200 hover:bg-gray-300 text-gray-800 font-semibold py-2 rounded-lg transition"
          >
            Ahora no
          </button>
        </div>
      )}

      {step === 'setup' && qrCode && secret && (
        <div className="space-y-4">
          <div className="text-center">
            <p className="text-sm font-semibold text-gray-900 mb-3">
              Paso 1: Escanea este código QR
            </p>
            <img
              src={qrCode}
              alt="QR Code"
              className="w-48 h-48 mx-auto border-4 border-gray-300 rounded-lg"
            />
          </div>

          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
            <p className="text-xs font-semibold text-yellow-900 mb-2">
              ¿No puedes escanear?
            </p>
            <p className="text-xs text-yellow-800 mb-2">Clave secreta manual:</p>
            <code className="block text-xs bg-white p-2 rounded border border-yellow-200 font-mono break-all text-center text-gray-900">
              {secret}
            </code>
            <p className="text-xs text-yellow-800 mt-2">
              Cópiala en tu app autenticadora si el QR no funciona.
            </p>
          </div>

          <div className="space-y-3">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Paso 2: Ingresa el código de 6 dígitos
              </label>
              <input
                type="text"
                inputMode="numeric"
                maxLength={6}
                placeholder="000000"
                value={verificationCode}
                onChange={(e) => {
                  setVerificationCode(e.target.value.replace(/\D/g, ''));
                  setError(null);
                }}
                className="w-full text-center text-2xl font-mono tracking-widest border-2 border-gray-300 rounded-lg p-3 focus:border-blue-500 outline-none"
              />
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                <p className="text-xs text-red-800">{error}</p>
              </div>
            )}

            <button
              onClick={handleVerify}
              disabled={loading || verificationCode.length !== 6}
              className="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white font-semibold py-2 rounded-lg transition"
            >
              {loading ? 'Verificando...' : 'Verificar código'}
            </button>
          </div>

          <p className="text-xs text-gray-600 text-center">
            Después del "." en tu app autenticadora
          </p>
        </div>
      )}

      {step === 'backup' && (
        <div className="space-y-4">
          <div className="text-center text-3xl mb-4">✓</div>

          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <p className="text-sm font-semibold text-green-900">
              ¡2FA Habilitado!
            </p>
            <p className="text-xs text-green-800 mt-1">
              Tu cuenta está ahora protegida con verificación en dos pasos.
            </p>
          </div>

          <div className="bg-orange-50 border border-orange-200 rounded-lg p-4 space-y-2">
            <p className="text-xs font-semibold text-orange-900 flex gap-2">
              <span>⚠️</span>
              <span>Guarda tu clave secreta en un lugar seguro</span>
            </p>
            <p className="text-xs text-orange-800">
              Si pierdes acceso a tu app autenticadora, necesitarás esta clave para recuperar tu cuenta:
            </p>
            <code className="block text-xs bg-white p-2 rounded border border-orange-200 font-mono break-all text-center text-gray-900 mt-2">
              {secret}
            </code>
          </div>

          <button
            onClick={() => {
              setStep('complete');
              onComplete();
            }}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 rounded-lg transition"
          >
            Continuar
          </button>
        </div>
      )}
    </div>
  );
};
