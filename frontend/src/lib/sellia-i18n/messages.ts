/**
 * Translation dictionaries · 12 languages.
 *
 * Keys are dot-namespaced (e.g. login.title).
 * Add new keys to ALL locales (or fallback to en will kick in).
 */
export type Locale = 'es' | 'en' | 'pt' | 'fr' | 'it' | 'de' | 'ja' | 'zh' | 'ar' | 'hi' | 'ko' | 'ru'

export const DEFAULT_LOCALE: Locale = 'es'

type Dict = Record<string, string>

const es: Dict = {
  'app.title': 'SellIA · Brain Hub',
  'nav.dashboard': 'Dashboard',
  'nav.deals': 'Deals',
  'nav.channels': 'Canales',
  'nav.settings': 'Configuración',
  'nav.logout': 'Cerrar sesión',
  'login.title': 'Iniciar sesión',
  'login.subtitle': 'Iniciá sesión en tu Brain Hub',
  'login.email': 'Email',
  'login.password': 'Contraseña',
  'login.submit': 'Entrar',
  'login.submitting': 'Entrando…',
  'login.no_account': '¿No tenés cuenta?',
  'login.signup_link': 'Crear ahora',
  'signup.title': 'Crear cuenta',
  'signup.subtitle': 'Trial 14 días · sin tarjeta',
  'signup.name': 'Tu nombre',
  'signup.tenant_name': 'Nombre del negocio',
  'signup.submit': 'Crear cuenta',
  'onboarding.subdomain_title': 'Elegí tu subdominio',
  'onboarding.subdomain_hint': 'Tu negocio vivirá en {sub}.sellia.app',
  'onboarding.subdomain_available': '✓ Disponible',
  'onboarding.connect_stripe': 'Conectar Stripe Express →',
  'common.loading': 'Cargando…',
  'common.error': 'Error',
  'common.save': 'Guardar',
  'common.cancel': 'Cancelar',
  'common.delete': 'Eliminar',
  'common.confirm_delete': '¿Eliminar?',
  'deals.title': 'Deals',
  'deals.empty': 'No hay deals · pipeline vacío',
  'deals.mark_won': 'Marcar ganado',
  'deals.reopen': 'Reabrir',
  'ws.status': 'WS · {status}',
}

const en: Dict = {
  'app.title': 'SellIA · Brain Hub',
  'nav.dashboard': 'Dashboard',
  'nav.deals': 'Deals',
  'nav.channels': 'Channels',
  'nav.settings': 'Settings',
  'nav.logout': 'Sign out',
  'login.title': 'Sign in',
  'login.subtitle': 'Sign in to your Brain Hub',
  'login.email': 'Email',
  'login.password': 'Password',
  'login.submit': 'Sign in',
  'login.submitting': 'Signing in…',
  'login.no_account': 'No account?',
  'login.signup_link': 'Create one',
  'signup.title': 'Create account',
  'signup.subtitle': '14-day trial · no card required',
  'signup.name': 'Your name',
  'signup.tenant_name': 'Business name',
  'signup.submit': 'Create account',
  'onboarding.subdomain_title': 'Choose your subdomain',
  'onboarding.subdomain_hint': 'Your business will live at {sub}.sellia.app',
  'onboarding.subdomain_available': '✓ Available',
  'onboarding.connect_stripe': 'Connect Stripe Express →',
  'common.loading': 'Loading…',
  'common.error': 'Error',
  'common.save': 'Save',
  'common.cancel': 'Cancel',
  'common.delete': 'Delete',
  'common.confirm_delete': 'Delete?',
  'deals.title': 'Deals',
  'deals.empty': 'No deals · empty pipeline',
  'deals.mark_won': 'Mark won',
  'deals.reopen': 'Reopen',
  'ws.status': 'WS · {status}',
}

const pt: Dict = {
  'app.title': 'SellIA · Brain Hub',
  'login.title': 'Entrar',
  'login.email': 'Email',
  'login.password': 'Senha',
  'login.submit': 'Entrar',
  'signup.title': 'Criar conta',
  'common.loading': 'Carregando…',
  'common.save': 'Salvar',
  'common.cancel': 'Cancelar',
  'deals.title': 'Negócios',
  'deals.empty': 'Sem negócios',
}

const fr: Dict = {
  'app.title': 'SellIA · Brain Hub',
  'login.title': 'Se connecter',
  'login.email': 'Email',
  'login.password': 'Mot de passe',
  'login.submit': 'Entrer',
  'signup.title': 'Créer un compte',
  'common.loading': 'Chargement…',
  'common.save': 'Enregistrer',
  'common.cancel': 'Annuler',
  'deals.title': 'Affaires',
}

const it: Dict = {
  'app.title': 'SellIA · Brain Hub',
  'login.title': 'Accedi',
  'login.email': 'Email',
  'login.password': 'Password',
  'login.submit': 'Entra',
  'common.loading': 'Caricamento…',
  'common.save': 'Salva',
}

const de: Dict = {
  'app.title': 'SellIA · Brain Hub',
  'login.title': 'Anmelden',
  'login.email': 'E-Mail',
  'login.password': 'Passwort',
  'login.submit': 'Anmelden',
  'common.loading': 'Lädt…',
  'common.save': 'Speichern',
}

const ja: Dict = {
  'app.title': 'SellIA · ブレイン・ハブ',
  'login.title': 'ログイン',
  'login.email': 'メール',
  'login.password': 'パスワード',
  'login.submit': 'ログイン',
  'common.loading': '読み込み中…',
  'common.save': '保存',
}

const zh: Dict = {
  'app.title': 'SellIA · 大脑中心',
  'login.title': '登录',
  'login.email': '邮箱',
  'login.password': '密码',
  'login.submit': '登录',
  'common.loading': '加载中…',
  'common.save': '保存',
}

const ar: Dict = {
  'app.title': 'SellIA · مركز الدماغ',
  'login.title': 'تسجيل الدخول',
  'login.email': 'البريد الإلكتروني',
  'login.password': 'كلمة المرور',
  'login.submit': 'دخول',
  'common.loading': 'جار التحميل…',
  'common.save': 'حفظ',
}

const hi: Dict = {
  'app.title': 'SellIA · ब्रेन हब',
  'login.title': 'साइन इन',
  'login.email': 'ईमेल',
  'login.password': 'पासवर्ड',
  'login.submit': 'प्रवेश',
  'common.loading': 'लोड हो रहा है…',
}

const ko: Dict = {
  'app.title': 'SellIA · 브레인 허브',
  'login.title': '로그인',
  'login.email': '이메일',
  'login.password': '비밀번호',
  'login.submit': '로그인',
  'common.loading': '로드 중…',
}

const ru: Dict = {
  'app.title': 'SellIA · Центр мозга',
  'login.title': 'Войти',
  'login.email': 'Электронная почта',
  'login.password': 'Пароль',
  'login.submit': 'Войти',
  'common.loading': 'Загрузка…',
}

export const MESSAGES: Record<Locale, Dict> = {
  es, en, pt, fr, it, de, ja, zh, ar, hi, ko, ru,
}

export const LOCALE_LABELS: Record<Locale, { label: string; flag: string }> = {
  es: { label: 'Español',    flag: '🇦🇷' },
  en: { label: 'English',    flag: '🇺🇸' },
  pt: { label: 'Português',  flag: '🇧🇷' },
  fr: { label: 'Français',   flag: '🇫🇷' },
  it: { label: 'Italiano',   flag: '🇮🇹' },
  de: { label: 'Deutsch',    flag: '🇩🇪' },
  ja: { label: '日本語',     flag: '🇯🇵' },
  zh: { label: '中文',       flag: '🇨🇳' },
  ar: { label: 'العربية',     flag: '🇸🇦' },
  hi: { label: 'हिन्दी',      flag: '🇮🇳' },
  ko: { label: '한국어',     flag: '🇰🇷' },
  ru: { label: 'Русский',    flag: '🇷🇺' },
}
