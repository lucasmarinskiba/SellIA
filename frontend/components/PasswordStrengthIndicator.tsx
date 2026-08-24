import React, { useState, useMemo } from 'react';

interface PasswordRequirement {
  label: string;
  regex: RegExp;
  met: boolean;
}

interface PasswordStrengthIndicatorProps {
  password: string;
  onStrengthChange?: (strength: number) => void;
}

export const PasswordStrengthIndicator: React.FC<PasswordStrengthIndicatorProps> = ({
  password,
  onStrengthChange,
}) => {
  const requirements: PasswordRequirement[] = useMemo(() => {
    return [
      {
        label: 'Mínimo 8 caracteres',
        regex: /.{8,}/,
        met: password.length >= 8,
      },
      {
        label: 'Mayúscula (A-Z)',
        regex: /[A-Z]/,
        met: /[A-Z]/.test(password),
      },
      {
        label: 'Minúscula (a-z)',
        regex: /[a-z]/,
        met: /[a-z]/.test(password),
      },
      {
        label: 'Número (0-9)',
        regex: /\d/,
        met: /\d/.test(password),
      },
      {
        label: 'Símbolo especial (@+-!#$%)',
        regex: /[@+\-!#$%]/,
        met: /@|\+|\-|!|#|\$|%/.test(password),
      },
    ];
  }, [password]);

  const metRequirements = useMemo(() => {
    return requirements.filter((req) => req.met).length;
  }, [requirements]);

  const strengthScore = useMemo(() => {
    const score = Math.min(5, metRequirements);
    if (onStrengthChange) onStrengthChange(score);
    return score;
  }, [metRequirements, onStrengthChange]);

  const strengthLabel = useMemo(() => {
    if (strengthScore === 0) return 'Muy débil';
    if (strengthScore === 1) return 'Débil';
    if (strengthScore === 2) return 'Regular';
    if (strengthScore === 3) return 'Buena';
    if (strengthScore === 4) return 'Fuerte';
    return 'Muy fuerte';
  }, [strengthScore]);

  const strengthColor = useMemo(() => {
    if (strengthScore === 0) return 'bg-red-600';
    if (strengthScore === 1) return 'bg-red-500';
    if (strengthScore === 2) return 'bg-yellow-500';
    if (strengthScore === 3) return 'bg-blue-500';
    if (strengthScore === 4) return 'bg-green-500';
    return 'bg-green-600';
  }, [strengthScore]);

  const textColor = useMemo(() => {
    if (strengthScore <= 1) return 'text-red-600';
    if (strengthScore === 2) return 'text-yellow-600';
    if (strengthScore === 3) return 'text-blue-600';
    return 'text-green-600';
  }, [strengthScore]);

  if (!password) return null;

  return (
    <div className="mt-4 space-y-3">
      {/* Strength bar */}
      <div className="space-y-1">
        <div className="flex justify-between items-center">
          <label className="text-sm font-medium text-gray-700">
            Seguridad de contraseña
          </label>
          <span className={`text-sm font-semibold ${textColor}`}>
            {strengthLabel}
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
          <div
            className={`h-full ${strengthColor} transition-all duration-300`}
            style={{ width: `${(strengthScore / 5) * 100}%` }}
          />
        </div>
      </div>

      {/* Requirements checklist */}
      <div className="space-y-2 bg-gray-50 p-4 rounded-lg border border-gray-200">
        <p className="text-xs font-semibold text-gray-700 uppercase tracking-wide">
          Requisitos de contraseña
        </p>
        <ul className="space-y-2">
          {requirements.map((req, idx) => (
            <li
              key={idx}
              className="flex items-center gap-2 text-sm transition-colors duration-200"
            >
              <span
                className={`flex-shrink-0 w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold ${
                  req.met
                    ? 'bg-green-100 text-green-700'
                    : 'bg-gray-300 text-gray-500'
                }`}
              >
                {req.met ? '✓' : '○'}
              </span>
              <span className={req.met ? 'text-gray-700' : 'text-gray-500'}>
                {req.label}
              </span>
            </li>
          ))}
        </ul>
      </div>

      {/* Security tips */}
      {strengthScore < 5 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-xs text-blue-700">
          <p className="font-semibold mb-1">💡 Consejos de seguridad:</p>
          <ul className="space-y-1 ml-2">
            <li>• Usa una combinación de letras, números y símbolos</li>
            <li>• Evita información personal (nombre, fecha nacimiento)</li>
            <li>• Usa una frase memorable con números: "MiCafe2024!"</li>
            <li>• Cada carácter adicional multiplica la seguridad</li>
          </ul>
        </div>
      )}

      {strengthScore >= 4 && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-3 text-xs text-green-700">
          <p className="font-semibold">✓ Contraseña segura</p>
        </div>
      )}
    </div>
  );
};
