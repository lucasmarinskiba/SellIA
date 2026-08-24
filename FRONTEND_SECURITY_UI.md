# Frontend Security UI Components

Componentes React profesionales para autenticación y seguridad con UX clara.

## Componentes Incluidos

### 1. PasswordStrengthIndicator

Indicador visual de fuerza de contraseña en tiempo real.

**Ubicación**: `frontend/components/PasswordStrengthIndicator.tsx`

**Features**:
- Barra de progreso con colores (rojo → verde)
- Checklist de requisitos con iconos ✓
- Tooltips educativos
- Consejos de seguridad dinámicos
- Feedback en tiempo real

**Requisitos mostrados**:
- ✓ Mínimo 8 caracteres
- ✓ Mayúscula (A-Z)
- ✓ Minúscula (a-z)
- ✓ Número (0-9)
- ✓ Símbolo especial (@+-!#$%)

**Niveles de seguridad**:
- 1/5: Muy débil (🔴)
- 2/5: Débil (🟠)
- 3/5: Regular (🟡)
- 4/5: Buena (🔵)
- 5/5: Muy fuerte (🟢)

**Uso**:
```tsx
import { PasswordStrengthIndicator } from '@/components/PasswordStrengthIndicator';

export function MyComponent() {
  const [password, setPassword] = useState('');
  const [strength, setStrength] = useState(0);

  return (
    <>
      <input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Tu contraseña"
      />
      <PasswordStrengthIndicator
        password={password}
        onStrengthChange={setStrength}
      />
      <button disabled={strength < 4}>Enviar</button>
    </>
  );
}
```

### 2. SecureSignupForm

Formulario de registro con validación integrada de seguridad.

**Ubicación**: `frontend/components/SecureSignupForm.tsx`

**Features**:
- Validación de nombre, email, contraseña
- Indicador de fuerza integrado
- Confirmación de contraseña
- Toggle mostrar/ocultar contraseña
- Errores claros por campo
- Indicadores de seguridad

**Campos**:
- Nombre completo (requerido)
- Email (validación de formato)
- Contraseña (requisitos de fuerza)
- Confirmación de contraseña

**Validaciones**:
- Email: formato válido
- Contraseña: fuerza mínima 4/5
- Coincidencia de contraseñas
- Campos requeridos

**Uso**:
```tsx
import { SecureSignupForm } from '@/components/SecureSignupForm';

export function SignupPage() {
  return (
    <SecureSignupForm
      onSuccess={(user) => {
        console.log('Usuario creado:', user);
        // Navegar a 2FA setup o dashboard
      }}
      onError={(error) => {
        console.error('Error:', error);
      }}
    />
  );
}
```

### 3. TwoFactorSetup

Flujo interactivo de configuración de autenticación de dos factores.

**Ubicación**: `frontend/components/TwoFactorSetup.tsx`

**Steps**:
1. **Intro**: Explica 2FA y beneficios
2. **Setup**: Muestra QR code + clave secreta
3. **Verify**: Input de 6 dígitos
4. **Backup**: Resguardo de clave secreta
5. **Complete**: Confirmación

**Features**:
- QR code escanenable
- Clave secreta manual (fallback)
- Input de 6 dígitos solo números
- Validación en tiempo real
- Advertencia de backup
- Mensajes de error claros

**Apps compatibles**:
- Google Authenticator
- Microsoft Authenticator
- Authy
- 1Password
- LastPass

**Uso**:
```tsx
import { TwoFactorSetup } from '@/components/TwoFactorSetup';

export function SettingsPage() {
  return (
    <TwoFactorSetup
      userId={currentUser.id}
      onComplete={() => {
        // Actualizar UI
        setIs2FAEnabled(true);
      }}
      onCancel={() => {
        // Cerrar modal o navegar
      }}
    />
  );
}
```

## Integración en Páginas

### Signup Flow

```tsx
// pages/signup.tsx
import { SecureSignupForm } from '@/components/SecureSignupForm';
import { TwoFactorSetup } from '@/components/TwoFactorSetup';
import { useState } from 'react';

export default function SignupPage() {
  const [step, setStep] = useState<'signup' | '2fa'>('signup');
  const [userId, setUserId] = useState<string | null>(null);

  return (
    <div>
      {step === 'signup' ? (
        <SecureSignupForm
          onSuccess={({ userId }) => {
            setUserId(userId);
            setStep('2fa');
          }}
        />
      ) : userId ? (
        <div>
          <h1>Seguriza tu cuenta con 2FA</h1>
          <TwoFactorSetup
            userId={userId}
            onComplete={() => {
              // Ir a dashboard
              window.location.href = '/dashboard';
            }}
            onCancel={() => setStep('signup')}
          />
        </div>
      ) : null}
    </div>
  );
}
```

### Login Flow con 2FA

```tsx
// pages/login.tsx
import { useState } from 'react';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [totp, setTotp] = useState('');
  const [requires2FA, setRequires2FA] = useState(false);
  const [userId, setUserId] = useState<string | null>(null);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();

    const response = await fetch('/api/v1/auth/signin', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email,
        password,
        totp_code: totp || undefined,
      }),
    });

    const data = await response.json();

    if (data.requires_2fa) {
      setUserId(data.user_id);
      setRequires2FA(true);
    } else if (response.ok) {
      // Login exitoso
      localStorage.setItem('token', data.access_token);
      window.location.href = '/dashboard';
    }
  };

  if (requires2FA && userId) {
    return (
      <div className="max-w-md mx-auto p-6">
        <h2 className="text-2xl font-bold mb-4">Código de autenticación</h2>
        <p className="text-gray-600 mb-4">
          Ingresa el código de 6 dígitos de tu app autenticadora
        </p>
        <form onSubmit={handleLogin} className="space-y-4">
          <input
            type="text"
            inputMode="numeric"
            maxLength={6}
            value={totp}
            onChange={(e) => setTotp(e.target.value.replace(/\D/g, ''))}
            placeholder="000000"
            className="w-full text-center text-2xl font-mono tracking-widest border-2 border-gray-300 rounded-lg p-3"
          />
          <button
            type="submit"
            disabled={totp.length !== 6}
            className="w-full bg-blue-600 text-white font-semibold py-2 rounded-lg disabled:bg-gray-400"
          >
            Verificar
          </button>
        </form>
      </div>
    );
  }

  return (
    <form onSubmit={handleLogin} className="max-w-md mx-auto p-6">
      <h2 className="text-2xl font-bold mb-6">Iniciar sesión</h2>

      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="tu@correo.com"
        className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg mb-4 outline-none focus:border-blue-500"
      />

      <input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Tu contraseña"
        className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg mb-4 outline-none focus:border-blue-500"
      />

      <button
        type="submit"
        className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 rounded-lg"
      >
        Ingresar
      </button>
    </form>
  );
}
```

### Configuración de 2FA en Settings

```tsx
// pages/settings/security.tsx
import { TwoFactorSetup } from '@/components/TwoFactorSetup';
import { useUser } from '@/hooks/useUser';
import { useState } from 'react';

export default function SecuritySettings() {
  const { user } = useUser();
  const [show2FASetup, setShow2FASetup] = useState(false);
  const [is2FAEnabled, setIs2FAEnabled] = useState(user?.is_2fa_enabled || false);

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Seguridad</h1>

      {/* 2FA Section */}
      <div className="bg-white rounded-lg shadow-lg p-6 mb-6 border border-gray-200">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">
              Autenticación de dos factores
            </h2>
            <p className="text-sm text-gray-600 mt-1">
              {is2FAEnabled
                ? '✓ Habilitado - Tu cuenta está protegida'
                : 'Deshabilitado - Mejora tu seguridad'}
            </p>
          </div>
          <span
            className={`px-3 py-1 rounded-full text-xs font-semibold ${
              is2FAEnabled
                ? 'bg-green-100 text-green-800'
                : 'bg-gray-100 text-gray-800'
            }`}
          >
            {is2FAEnabled ? 'Activo' : 'Inactivo'}
          </span>
        </div>

        {!is2FAEnabled && (
          <button
            onClick={() => setShow2FASetup(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg"
          >
            Configurar 2FA
          </button>
        )}

        {is2FAEnabled && (
          <button
            className="bg-red-600 hover:bg-red-700 text-white font-semibold py-2 px-4 rounded-lg"
          >
            Deshabilitar 2FA
          </button>
        )}
      </div>

      {/* 2FA Setup Modal */}
      {show2FASetup && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
          <TwoFactorSetup
            userId={user!.id}
            onComplete={() => {
              setIs2FAEnabled(true);
              setShow2FASetup(false);
            }}
            onCancel={() => setShow2FASetup(false)}
          />
        </div>
      )}
    </div>
  );
}
```

## Estilos y Temas

Componentes usan Tailwind CSS. Asegúrate de tener:

```json
{
  "devDependencies": {
    "tailwindcss": "^3.x"
  }
}
```

### Colores de Seguridad

```css
/* Rojo: muy débil, error */
.text-red-600 .bg-red-50 .border-red-200

/* Naranja: advertencia, cuidado */
.text-orange-600 .bg-orange-50

/* Amarillo: regular, requiere mejora */
.text-yellow-600 .bg-yellow-50

/* Azul: información, bueno */
.text-blue-600 .bg-blue-50

/* Verde: seguro, correcto */
.text-green-600 .bg-green-50
```

## Accesibilidad

Componentes incluyen:
- Labels asociados a inputs
- Mensajes de error descriptivos
- Indicadores visuales + texto
- Soporte para input numérico en móviles
- Contraste de colores WCAG AA

## Testing

```tsx
// components/__tests__/PasswordStrengthIndicator.test.tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { PasswordStrengthIndicator } from '../PasswordStrengthIndicator';

describe('PasswordStrengthIndicator', () => {
  it('shows weak password feedback', () => {
    render(<PasswordStrengthIndicator password="weak" />);
    expect(screen.getByText(/Muy débil/)).toBeInTheDocument();
  });

  it('shows strong password feedback', () => {
    render(
      <PasswordStrengthIndicator password="SecurePass123@" />
    );
    expect(screen.getByText(/Muy fuerte/)).toBeInTheDocument();
  });
});
```

## Performance

- Validación debounced (500ms)
- Componentes optimizados con React.memo
- Cero dependencias externas (excepto React)
- < 15KB minificado

## Próximos Pasos

1. Integrar componentes en páginas de signup/login
2. Conectar con API backends
3. Añadir animaciones de transición
4. Implementar backup codes para 2FA
5. Agregar recovery email/phone para 2FA
6. Tests automatizados completos

---
**Última actualización**: 2026-08-24
