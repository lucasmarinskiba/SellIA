#!/bin/sh
# Falla (exit 1) si el diff recibido por stdin AGREGA una credencial.
#
#   git diff --cached | scripts/check-added-secrets.sh        # pre-commit
#   git diff origin/main...HEAD | scripts/check-added-secrets.sh   # CI
#
# Una sola implementación para el hook local y para el CI, así lo que bloquea un
# commit en tu máquina es exactamente lo que bloquea el PR.
#
# Por qué existe: GitHub no ofrece "non-provider patterns" en este repo (sólo
# patrones de proveedores), y un commit con URLs de base de datos de producción
# con contraseña llegó a un repo público sin que nada lo frenara.
#
# Sólo mira líneas AGREGADAS: borrar un secreto (como hace el commit que lo
# remedia) no dispara nada. Los valores se enmascaran en la salida.

ADDED="$(grep -E '^\+[^+]' || true)"
[ -n "$ADDED" ] || exit 0

# URL con usuario:contraseña embebida, salvo placeholders conocidos o variables.
URL_CREDS="$(printf '%s\n' "$ADDED" \
  | grep -E '(postgres(ql)?(\+[a-z0-9]+)?|mysql|mongodb(\+srv)?|redis|amqp)://[^:/@ "'"'"'$<{]+:[^@ "'"'"'$<{]{6,}@' \
  | grep -viE '://(user|username|test|postgres|root|admin|sellia|ia_vendedor|u|x|app|db|default):(password|pass|test|postgres|secret|changeme|change-me|xxx+|your[-_a-z]*|secure_password_here|redis_password_here|[a-z_]*password[a-z_]*|dev[-_a-z0-9]*|local[-_a-z0-9]*|\*+|x|d|redis)@')"

# Tokens con formato real de proveedor, claves privadas, JWT y "Bearer <token largo>".
TOKENS="$(printf '%s\n' "$ADDED" | grep -E \
  'sk-ant-[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9]{32,}|AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{30,}|xox[bpa]-[A-Za-z0-9-]{20,}|APP_USR-[0-9a-f-]{20,}|-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----|eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}|Bearer[[:space:]]+[A-Za-z0-9._-]{30,}([^A-Za-z0-9._-]|$)' \
  | grep -vE 'Bearer[[:space:]]+(\$|<|\{|%)')"

if [ -n "$URL_CREDS$TOKENS" ]; then
  echo "[secret-guard] posible credencial en las líneas agregadas (valor oculto):" >&2
  printf '%s\n%s\n' "$URL_CREDS" "$TOKENS" | grep -v '^$' \
    | sed -E 's#(://[^:/@ ]+:)[^@ ]+@#\1***@#; s#(sk-[A-Za-z0-9_-]{4})[A-Za-z0-9_-]+#\1***#; s#(Bearer[[:space:]]+)[A-Za-z0-9._-]+#\1***#; s#eyJ[A-Za-z0-9_.-]+#eyJ***#g' \
    | cut -c1-140 >&2
  echo "[secret-guard] Usá una variable de entorno o un archivo ignorado por git." >&2
  echo "[secret-guard] Si ya llegó a un remoto, rotá la credencial: borrarla del código no la revoca." >&2
  echo "[secret-guard] Falso positivo (placeholder)? Agregalo a la lista de este script." >&2
  exit 1
fi
exit 0
