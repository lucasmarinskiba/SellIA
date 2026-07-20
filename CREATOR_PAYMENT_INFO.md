# Datos de Pago del Creador — SellIA

> ⚠️ Este archivo contiene información sensible. No commitear a git.

## Métodos de Pago Configurados

| Método | Región | Moneda | Destino |
|--------|--------|--------|---------|
| **MercadoPago** | Argentina | ARS | `lucas.marin.skiba.mp` |
| **Payoneer Checkout** | Internacional | USD | Cuenta Payoneer de Lucas |
| **USDT (TRC-20)** | Global | USD | `TU5ZjtMioPeDFqEXvCJf8M3AV5z7dbRK57` |
| **USDT (BEP-20)** | Global | USD | `0xa69b9db124d994b8ce45284d96ad733a95f1fd55` |

---

## Datos Completos del Creador

### Personales / Fiscales
| Campo | Valor |
|-------|-------|
| Nombre completo | Lucas Daniel Marin |
| DNI | 41.941.012 |
| CUIL | 20-41941012-9 |
| Domicilio fiscal | Francia 2481 - Santa Fe - La Capital - Santa Fe |

### Argentina
| Campo | Valor |
|-------|-------|
| Alias MercadoPago | `lucas.marin.skiba.mp` |
| Alias Coco | `LMARIN11.COCOS` |

### Payoneer
| Campo | Valor |
|-------|-------|
| Cuenta | lucasdmarin |
| Binance ID (referencia) | 40890503 |
| Banco receptor | Citibank |
| Dirección banco | 111 Wall Street New York, NY 10043 USA |
| Routing (ABA) | `031100209` |
| SWIFT | `CITIUS33` |
| Cuenta | `70588150000455082` |
| Tipo | CHECKING |
| Beneficiario | Lucas Daniel Marin |

### Crypto / Binance
| Campo | Valor |
|-------|-------|
| USDT BEP-20 (BSC) | `0xa69b9db124d994b8ce45284d96ad733a95f1fd55` |
| USDT TRC-20 (Tron) | `TU5ZjtMioPeDFqEXvCJf8M3AV5z7dbRK57` |

---

## Pendiente para Activar Payoneer Checkout

Payoneer requiere credenciales de API para el checkout directo. Necesitás:

| Dato | Dónde conseguirlo |
|------|-------------------|
| `PAYONEER_PROGRAM_ID` | Dashboard de Payoneer → Developers → Program ID |
| `PAYONEER_CLIENT_ID` | Dashboard de Payoneer → Developers → OAuth App → Client ID |
| `PAYONEER_CLIENT_SECRET` | Dashboard de Payoneer → Developers → OAuth App → Client Secret |

Una vez que tengas estos datos, los agregás al `.env` y reiniciás el backend.

---

## Flujo de Pagos por Cliente

### Cliente Argentino
1. Ve precios en ARS
2. Selecciona **MercadoPago**
3. Paga con tarjeta, saldo MP, Rapipago, Pago Fácil, etc.
4. El dinero llega a `lucas.marin.skiba.mp`

### Cliente Internacional
1. Ve precios en USD
2. Puede elegir:
   - **Payoneer Checkout** → Paga con tarjeta internacional → El dinero llega a tu cuenta Payoneer
   - **USDT (TRC-20)** → Transfiere a `TU5ZjtMioPeDFqEXvCJf8M3AV5z7dbRK57` → Confirmación automática en blockchain
   - **USDT (BEP-20)** → Transfiere a `0xa69b9db124d994b8ce45284d96ad733a95f1fd55` → Confirmación automática en blockchain

---

## Notas Técnicas

- **MercadoPago**: Ya activo con `MERCADOPAGO_ACCESS_TOKEN`
- **Payoneer Checkout**: Estructura lista, esperando credenciales API
- **Crypto USDT**: Direcciones configuradas y activas en el checkout
- **Stripe**: Eliminado del sistema (reemplazado por Payoneer)
- **Facturación AFIP**: Pendiente condición IVA (Monotributo / RI / Exento)
