export default function DataDeletionPage() {
  return (
    <main style={{ maxWidth: 800, margin: '0 auto', padding: '48px 24px', fontFamily: 'sans-serif', lineHeight: 1.7 }}>
      <h1>Eliminación de Datos — SellIA</h1>
      <p><strong>Última actualización:</strong> 18 de julio de 2026</p>

      <p>
        De acuerdo con los requisitos de la plataforma Meta (Facebook, WhatsApp, Instagram),
        podés solicitar la eliminación de todos tus datos almacenados en SellIA.
      </p>

      <h2>¿Qué datos se eliminan?</h2>
      <ul>
        <li>Tu cuenta y perfil de usuario.</li>
        <li>Datos de negocio, catálogo y configuración.</li>
        <li>Historial de conversaciones y mensajes.</li>
        <li>Tokens de acceso de Meta (WhatsApp / Instagram).</li>
        <li>Métricas y reportes asociados a tu cuenta.</li>
      </ul>

      <h2>Cómo solicitar la eliminación</h2>

      <h3>Opción 1 — Desde la app</h3>
      <ol>
        <li>Iniciá sesión en <a href="https://sellia-brain.vercel.app/login">sellia-brain.vercel.app/login</a></li>
        <li>Andá a <strong>Configuración → Cuenta → Eliminar cuenta</strong></li>
        <li>Confirmá la eliminación. Tus datos serán borrados en 30 días.</li>
      </ol>

      <h3>Opción 2 — Por email</h3>
      <p>
        Enviá un email a <a href="mailto:lucasdmarin@gmail.com">lucasdmarin@gmail.com</a> con el asunto
        <strong>"Eliminación de datos SellIA"</strong> incluyendo el email de tu cuenta.
        Procesamos la solicitud en un plazo máximo de 30 días.
      </p>

      <h2>Confirmación</h2>
      <p>
        Una vez procesada la solicitud, recibirás un email de confirmación a la dirección
        de tu cuenta indicando que todos tus datos fueron eliminados permanentemente.
      </p>

      <h2>Contacto</h2>
      <p>
        Lucas Daniel Marín · <a href="mailto:lucasdmarin@gmail.com">lucasdmarin@gmail.com</a>
      </p>
    </main>
  );
}
