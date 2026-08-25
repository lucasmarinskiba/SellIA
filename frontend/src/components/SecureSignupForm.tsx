import React, { useState } from 'react';
import { PasswordStrengthIndicator } from './PasswordStrengthIndicator';

interface SecureSignupFormProps {
  onSuccess: (userData: { userId: string; email: string }) => void;
  onError?: (error: string) => void;
}

export const SecureSignupForm: React.FC<SecureSignupFormProps> = ({
  onSuccess,
  onError,
}) => {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordStrength, setPasswordStrength] = useState(0);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [showPassword, setShowPassword] = useState(false);

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!fullName.trim()) {
      newErrors.fullName = 'El nombre es requerido';
    }

    if (!email.trim()) {
      newErrors.email = 'El email es requerido';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      newErrors.email = 'Email inválido';
    }

    if (!password) {
      newErrors.password = 'La contraseña es requerida';
    } else if (passwordStrength < 4) {
      newErrors.password = 'La contraseña no es lo suficientemente segura';
    }

    if (password !== confirmPassword) {
      newErrors.confirmPassword = 'Las contraseñas no coinciden';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      onError?.('Por favor corrige los errores');
      return;
    }

    setLoading(true);
    try {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'https://sellia-production.up.railway.app';
      const response = await fetch(`${backendUrl}/api/v1/auth/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          full_name: fullName,
          email,
          password,
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Error en el signup');
      }

      const data = await response.json();
      onSuccess({
        userId: data.user_id,
        email: data.email,
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error desconocido';
      setErrors({ submit: message });
      onError?.(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="max-w-md mx-auto p-6 bg-white rounded-lg shadow-lg border border-gray-200">
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Crear cuenta segura</h2>
        <p className="text-sm text-gray-600 mt-1">
          Tu privacidad y seguridad son prioridad
        </p>
      </div>

      {/* Full Name */}
      <div className="mb-4">
        <label className="block text-sm font-semibold text-gray-700 mb-2">
          Nombre completo
        </label>
        <input
          type="text"
          value={fullName}
          onChange={(e) => {
            setFullName(e.target.value);
            setErrors({ ...errors, fullName: '' });
          }}
          placeholder="Juan García"
          className={`w-full px-4 py-2 border-2 rounded-lg outline-none transition ${
            errors.fullName
              ? 'border-red-500 focus:border-red-600'
              : 'border-gray-300 focus:border-blue-500'
          }`}
        />
        {errors.fullName && (
          <p className="text-xs text-red-600 mt-1">{errors.fullName}</p>
        )}
      </div>

      {/* Email */}
      <div className="mb-4">
        <label className="block text-sm font-semibold text-gray-700 mb-2">
          Email
        </label>
        <input
          type="email"
          value={email}
          onChange={(e) => {
            setEmail(e.target.value);
            setErrors({ ...errors, email: '' });
          }}
          placeholder="tu@correo.com"
          className={`w-full px-4 py-2 border-2 rounded-lg outline-none transition ${
            errors.email
              ? 'border-red-500 focus:border-red-600'
              : 'border-gray-300 focus:border-blue-500'
          }`}
        />
        {errors.email && (
          <p className="text-xs text-red-600 mt-1">{errors.email}</p>
        )}
      </div>

      {/* Password */}
      <div className="mb-4">
        <label className="block text-sm font-semibold text-gray-700 mb-2">
          Contraseña
        </label>
        <div className="relative">
          <input
            type={showPassword ? 'text' : 'password'}
            value={password}
            onChange={(e) => {
              setPassword(e.target.value);
              setErrors({ ...errors, password: '' });
            }}
            placeholder="MiContraseña123@"
            className={`w-full px-4 py-2 pr-10 border-2 rounded-lg outline-none transition ${
              errors.password
                ? 'border-red-500 focus:border-red-600'
                : 'border-gray-300 focus:border-blue-500'
            }`}
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-3 top-3 text-gray-500 hover:text-gray-700"
          >
            {showPassword ? '🙈' : '👁️'}
          </button>
        </div>
        {errors.password && (
          <p className="text-xs text-red-600 mt-1">{errors.password}</p>
        )}

        {/* Password Strength Indicator */}
        <PasswordStrengthIndicator
          password={password}
          onStrengthChange={setPasswordStrength}
        />
      </div>

      {/* Confirm Password */}
      <div className="mb-6">
        <label className="block text-sm font-semibold text-gray-700 mb-2">
          Confirmar contraseña
        </label>
        <input
          type={showPassword ? 'text' : 'password'}
          value={confirmPassword}
          onChange={(e) => {
            setConfirmPassword(e.target.value);
            setErrors({ ...errors, confirmPassword: '' });
          }}
          placeholder="Repite tu contraseña"
          className={`w-full px-4 py-2 border-2 rounded-lg outline-none transition ${
            errors.confirmPassword
              ? 'border-red-500 focus:border-red-600'
              : password && confirmPassword === password
              ? 'border-green-500'
              : 'border-gray-300 focus:border-blue-500'
          }`}
        />
        {errors.confirmPassword && (
          <p className="text-xs text-red-600 mt-1">{errors.confirmPassword}</p>
        )}
        {password && confirmPassword === password && !errors.confirmPassword && (
          <p className="text-xs text-green-600 mt-1">✓ Las contraseñas coinciden</p>
        )}
      </div>

      {/* Security Notice */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-6">
        <p className="text-xs font-semibold text-blue-900 flex gap-2 mb-2">
          <span>🔐</span>
          <span>Protección de seguridad</span>
        </p>
        <ul className="text-xs text-blue-800 space-y-1 ml-5 list-disc">
          <li>Contraseña cifrada con bcrypt (salted hash)</li>
          <li>Autenticación de dos factores disponible</li>
          <li>Datos encriptados en tránsito (HTTPS)</li>
          <li>Cumple con OWASP y estándares internacionales</li>
        </ul>
      </div>

      {/* Submit Error */}
      {errors.submit && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
          <p className="text-xs text-red-800">{errors.submit}</p>
        </div>
      )}

      {/* Submit Button */}
      <button
        type="submit"
        disabled={loading || passwordStrength < 4}
        className={`w-full py-2 rounded-lg font-semibold transition mb-3 ${
          loading || passwordStrength < 4
            ? 'bg-gray-300 text-gray-600 cursor-not-allowed'
            : 'bg-blue-600 hover:bg-blue-700 text-white'
        }`}
      >
        {loading ? 'Creando cuenta...' : 'Crear cuenta'}
      </button>

      {/* Login Link */}
      <p className="text-center text-sm text-gray-600">
        ¿Ya tenés cuenta?{' '}
        <a href="/login" className="text-blue-600 hover:underline font-semibold">
          Ingresa aquí
        </a>
      </p>
    </form>
  );
};
