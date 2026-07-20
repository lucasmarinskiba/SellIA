/**
 * SellIA Frontend Logger
 * 
 * Solo loguea en desarrollo. En producción, los errores se envían
 * silenciosamente a un endpoint de telemetry (futuro) sin exponer
 * detalles internos en la consola.
 */

const isDev = process.env.NODE_ENV === 'development';

export const logger = {
  debug: (...args: unknown[]) => {
    if (isDev) console.debug('[SellIA]', ...args);
  },
  info: (...args: unknown[]) => {
    if (isDev) console.info('[SellIA]', ...args);
  },
  warn: (...args: unknown[]) => {
    if (isDev) console.warn('[SellIA]', ...args);
  },
  error: (message: string, error?: unknown) => {
    if (isDev) {
      console.error('[SellIA]', message, error);
    } else {
      // En producción: enviar a telemetry endpoint sin exponer en consola
      // fetch('/api/v1/telemetry/log', { method: 'POST', body: JSON.stringify({ level: 'error', message }) });
    }
  },
};
