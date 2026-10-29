# Consulta legal: prospección en frío con Harvey (SellIA)

> **Qué es este documento.** Un resumen técnico y neutro, escrito para llevárselo a un abogado/a especializado en
> protección de datos personales y comunicaciones comerciales. **No es asesoramiento legal.** Describe lo que el
> sistema hace hoy (verificado en el código al 2026-10-29) y las preguntas que hay que responder antes de usarlo con
> volumen real. No afirma qué dice la ley: eso es trabajo del profesional.

## 1. Qué es Harvey

Harvey es una función de SellIA que ayuda a **cada negocio cliente** (un usuario con su propio negocio y su propia
casilla de email) a escribirles a posibles clientes. Cada negocio es el responsable de sus envíos; SellIA es la
plataforma que le da la herramienta. Un negocio carga su oferta, su cliente ideal y una dirección postal; Harvey
redacta borradores de emails; **una persona del negocio aprueba cada email antes de que salga**; el email sale desde
la casilla del propio negocio (no desde un servidor de SellIA).

## 2. De dónde salen los destinatarios

| Origen | Cómo funciona |
|---|---|
| **Lista propia** | El negocio carga contactos a mano o importa un CSV (hasta 1000 filas). Quedan como email "provisto por el negocio". |
| **Sitios web públicos** | Harvey lee páginas públicas de empresas (inicio y páginas de contacto/nosotros), respetando `robots.txt`, con un identificador propio, y toma **solo direcciones publicadas en el dominio de esa empresa** (por ejemplo `contacto@empresa.com`). Ignora casillas personales de proveedores gratuitos (gmail, hotmail, etc.) y nunca adivina direcciones. |
| **Búsqueda automática** (opcional) | Si el negocio carga su propia clave de un buscador, Harvey encuentra sitios según su cliente ideal y luego aplica la lectura de arriba. |

Las direcciones obtenidas de sitios web se guardan como **"sin verificar"** y el sistema **no envía a ninguna hasta que
una persona del negocio la verifica**. Cada negocio ve solo sus propios datos (aislamiento por negocio).

## 3. Qué datos se tratan y dónde

- **Del destinatario:** email, y si el negocio lo cargó, nombre, empresa, cargo, sitio web y notas. Del sitio público:
  nombre de la empresa, descripción y el email publicado. Más adelante: el texto de su respuesta, si contesta.
- **Del negocio cliente:** su oferta, su cliente ideal, su dirección postal, la casilla de email (credenciales cifradas
  en reposo) y la lista de "no contactar".
- **Procesadores externos:** (a) la plataforma de IA **Anthropic** (EE. UU.) recibe el texto de los datos públicos del
  destinatario y de sus respuestas para redactar y clasificar; (b) el proveedor de la casilla de cada negocio (Gmail,
  Outlook u otro) transporta los emails; (c) la infraestructura de SellIA (hosting en Railway, EE. UU.).
- **Retención:** hoy no hay una política automática de borrado de prospectos o respuestas. **Es un punto abierto.**

## 4. Salvaguardas que ya existen (verificadas en el código)

1. **Aprobación humana de cada email.** Nada sale sin que una persona lo apruebe.
2. **Línea de baja obligatoria en cada email** ("respondé 'no gracias' y no te escribo más", configurable) y
   **dirección postal del negocio** agregadas al pie. Si falta la dirección postal, no se puede enviar.
3. **Lista de "no contactar"** por email o por dominio, revisada antes de cada envío.
4. **Baja por respuesta:** si el destinatario responde pidiendo la baja, un chequeo **sin IA** (reglas fijas) lo agrega
   a la lista de no contactar y cancela cualquier seguimiento pendiente. Una respuesta de "no me interesa" detiene la
   secuencia y archiva el hilo.
5. **Secuencia corta:** como máximo 3 emails por destinatario (el primero y dos seguimientos), todos de texto plano.
6. **Reglas de contenido verificadas por código** (no por IA) antes de poder aprobar: sin frases de urgencia o
   promesas ("últimos lugares", "resultados garantizados", etc.), sin variables sin reemplazar, límites de largo, y a lo
   sumo un enlace. Las afirmaciones sobre el destinatario solo pueden salir de los hechos cargados; el modelo tiene
   prohibido inventar datos.
7. **Límites de volumen:** tope diario de borradores y de envíos por negocio, ventana horaria de envío (por defecto 9 a
   18 h, días hábiles) y arranque gradual para casillas nuevas.
8. **Lectura de sitios con cuidado:** respeta `robots.txt`, se identifica, y bloquea direcciones internas.
9. **Casilla propia y verificada:** el negocio conecta su email con un código de confirmación enviado a esa casilla;
   solo una casilla confirmada puede enviar.

## 5. Preguntas para el/la profesional

**A. Base legal y consentimiento**
1. Para un negocio en Argentina que escribe a **empresas** a direcciones corporativas publicadas en su sitio, ¿hace
   falta consentimiento previo, o alcanza con el "interés legítimo"/dato publicado? ¿Cambia si la dirección es de una
   persona (nombre.apellido@empresa.com) y no de una casilla genérica (contacto@, ventas@)?
2. ¿Qué cambia si el destinatario es una **persona física** (profesional independiente) y no una empresa?
3. ¿Cómo aplica a destinatarios de **otros países** (UE/RGPD, EE. UU., Brasil/LGPD, Uruguay, Chile)? ¿Conviene limitar
   la herramienta a ciertos países o exigir que el negocio declare su alcance?

**B. Ley 25.326 y registro de bases de datos**
4. ¿Cada negocio cliente debe **inscribir** su base de contactos ante la autoridad de protección de datos? ¿Y SellIA, por
   alojar y tratar esas bases como encargado del tratamiento?
5. ¿Qué datos de la leyenda/derechos hay que incluir en los mensajes publicitarios (acceso, rectificación,
   supresión, baja) y en qué forma? ¿Alcanza con la línea de baja actual?
6. ¿Hace falta informar al destinatario **de dónde se obtuvo** su dato en el primer contacto? Hoy no lo decimos.

**C. Transferencia internacional**
7. El texto de los datos públicos y de las respuestas se procesa con una plataforma de IA en el exterior. ¿Requiere
   cláusulas contractuales, aviso previo o consentimiento? ¿Qué debe decir la política de privacidad?

**D. Roles y contratos**
8. ¿Cómo se redactan los **términos para los negocios clientes**: responsabilidad del negocio por sus envíos,
   declaración de que tiene base legal para contactar, y prohibición de usarlo con listas compradas?
9. ¿SellIA es **encargado** o **responsable** del tratamiento? ¿Qué contrato (encargado del tratamiento) hace falta
   con cada negocio y con los proveedores (Anthropic, hosting)?

**E. Operación**
10. ¿Cuánto tiempo se pueden **conservar** prospectos y respuestas? ¿Qué política de borrado automático conviene
    (por ejemplo, borrar prospectos sin respuesta a los 12 meses)?
11. Si alguien pide **supresión o acceso**, ¿cuál es el procedimiento y el plazo? (Hoy se hace a mano; no hay
    pantalla para eso.)
12. ¿Hay obligaciones adicionales por usar **IA** para redactar (transparencia, no hacerse pasar por una persona)? Hoy
    el email lo firma el nombre configurado por el negocio y no dice que fue redactado con ayuda de IA.

## 6. Qué se puede cambiar en el producto según la respuesta

Todo lo siguiente es técnicamente simple de agregar; se decide con la respuesta del profesional:
- Aviso de origen del dato en el primer email ("tu dirección figura publicada en tu sitio web").
- Mención de que el mensaje se redactó con ayuda de IA.
- Bloqueo por país o por tipo de dirección (por ejemplo, solo casillas genéricas, nunca personales).
- Aceptación de términos del negocio antes de activar Harvey (con la declaración de base legal).
- Política de retención con borrado automático, y pantalla de exportación y borrado por destinatario.
- Registro de cada baja y de su fecha, para poder demostrarla.
