export default function PrivacyPage() {
  return (
    <main style={{ maxWidth: 800, margin: '0 auto', padding: '48px 24px', fontFamily: 'sans-serif', lineHeight: 1.7 }}>
      <h1>Política de Privacidad — SellIA</h1>
      <p><strong>Última actualización:</strong> 18 de julio de 2026</p>

      <h2>1. Quiénes somos</h2>
      <p>
        SellIA es un agente de inteligencia artificial para automatización de ventas, desarrollado por
        Lucas Daniel Marín (CUIL 20-41941012-9), con domicilio en Francia 2481, Santa Fe, Argentina.
        Sitio web: <a href="https://sellia-brain.vercel.app">sellia-brain.vercel.app</a>
      </p>

      <h2>2. Datos que recopilamos</h2>
      <ul>
        <li><strong>Datos de cuenta:</strong> nombre, correo electrónico, contraseña cifrada.</li>
        <li><strong>Datos de negocio:</strong> nombre del negocio, catálogo de productos/servicios, precios.</li>
        <li><strong>Conversaciones:</strong> mensajes intercambiados a través de WhatsApp, Instagram u otros canales conectados.</li>
        <li><strong>Datos de pago:</strong> procesados por terceros (Mercado Pago). No almacenamos datos de tarjetas.</li>
        <li><strong>Datos de uso:</strong> métricas de actividad, logs de sesión.</li>
      </ul>

      <h2>3. Cómo usamos los datos</h2>
      <ul>
        <li>Operar el servicio de agente IA de ventas.</li>
        <li>Responder mensajes de clientes en nombre del usuario.</li>
        <li>Generar reportes y análisis de ventas.</li>
        <li>Mejorar el servicio y entrenar modelos internos (datos anonimizados).</li>
      </ul>

      <h2>4. Compartición de datos</h2>
      <p>
        Compartimos datos con proveedores de infraestructura (Railway, Vercel, OpenAI, Anthropic, Meta)
        exclusivamente para operar el servicio. No vendemos datos a terceros.
      </p>

      <h2>5. Datos de Meta (WhatsApp / Instagram)</h2>
      <p>
        Cuando conectás WhatsApp o Instagram, SellIA accede a mensajes y datos de negocio a través de
        la API de Meta. Estos datos se usan únicamente para automatizar respuestas según tus instrucciones.
        Podés desconectar tu cuenta en cualquier momento desde Configuración → Canales.
      </p>

      <h2>6. Retención de datos</h2>
      <p>
        Conservamos tus datos mientras tengas una cuenta activa. Podés solicitar la eliminación en
        cualquier momento (ver sección 8).
      </p>

      <h2>7. Seguridad</h2>
      <p>
        Usamos cifrado en tránsito (HTTPS/TLS) y en reposo. Las contraseñas se almacenan con bcrypt.
        Las credenciales de terceros se cifran con Fernet.
      </p>

      <h2>8. Tus derechos</h2>
      <ul>
        <li>Acceder, corregir o eliminar tus datos.</li>
        <li>Revocar el acceso a tus cuentas de Meta.</li>
        <li>Exportar tus datos.</li>
      </ul>
      <p>
        Para ejercer estos derechos o eliminar tu cuenta y datos:{' '}
        <a href="mailto:lucasdmarin@gmail.com">lucasdmarin@gmail.com</a> o visitá{' '}
        <a href="/data-deletion">sellia-brain.vercel.app/data-deletion</a>
      </p>

      <h2>9. Cookies</h2>
      <p>Usamos cookies de sesión estrictamente necesarias para el funcionamiento del servicio.</p>

      <h2>10. Cambios a esta política</h2>
      <p>Notificaremos cambios significativos por email con 30 días de anticipación.</p>

      <h2>11. Contacto</h2>
      <p>
        Lucas Daniel Marín · <a href="mailto:lucasdmarin@gmail.com">lucasdmarin@gmail.com</a>
      </p>
    </main>
  );
}
