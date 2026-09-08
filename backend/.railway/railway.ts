import { defineRailway, github, postgres, preserve, project, redis, service, volume } from "railway/iac";

export default defineRailway(() => {
  const SellIARepo = github("lucasmarinskiba/SellIA", { checkSuites: false });

  const Postgres = postgres("Postgres", { region: "sfo" });
  Postgres.networking = { privateNetworkEndpoint: "postgres", tcpProxies: { "5432": {} } };
  const Redis = redis("Redis", { region: "sfo" });
  Redis.deploy = { startCommand: "/bin/sh -c \"rm -rf $RAILWAY_VOLUME_MOUNT_PATH/lost+found/ && exec docker-entrypoint.sh redis-server --requirepass $REDIS_PASSWORD --save 60 1 --dir $RAILWAY_VOLUME_MOUNT_PATH\"" };
  Redis.networking = { privateNetworkEndpoint: "redis", tcpProxies: { "6379": {} } };
  const redisVolume = volume("redis-volume", { alerts: { usage: { "100": {}, "80": {}, "95": {} } }, allowOnlineResize: true, region: "sfo", sizeMB: 500 });
  const postgresVolume = volume("postgres-volume", { alerts: { usage: { "100": {}, "80": {}, "95": {} } }, allowOnlineResize: true, region: "sfo", sizeMB: 500 });
  const SellIA = service("SellIA", {
    source: SellIARepo,
    replicas: { "sfo": 1 },
    networking: { privateNetworkEndpoint: "sellia" },
    env: { ACCESS_TOKEN_EXPIRE_MINUTES: preserve(), ALGORITHM: preserve(), ANTHROPIC_API_KEY: preserve(), DATABASE_URL: preserve(), ENABLE_OPENAPI: preserve(), ENVIRONMENT: preserve(), FERNET_SECRET: preserve(), FRONTEND_URL: preserve(), MERCADOPAGO_ACCESS_TOKEN: preserve(), META_PHONE_NUMBER_ID: preserve(), META_WEBHOOK_VERIFY_TOKEN: preserve(), PORT: preserve(), REDIS_URL: preserve(), RESEND_API_KEY: preserve(), RESEND_WEBHOOK_SECRET: preserve(), SECRET_KEY: preserve(), SELLIA_METRICS_KEY: preserve(), SIDECAR_SHARED_SECRET: preserve(), WEBAUTHN_RP_ID: preserve(), WEBAUTHN_RP_ORIGIN: preserve() },
  });
  const selliaCeleryBeat = service("sellia-celery-beat", {
    source: SellIARepo,
    replicas: { "sfo": 1 },
    build: { builder: "DOCKERFILE", dockerfilePath: "/Dockerfile.celery-beat" },
    env: { ACCESS_TOKEN_EXPIRE_MINUTES: preserve(), ALGORITHM: preserve(), ANTHROPIC_API_KEY: preserve(), DATABASE_URL: preserve(), ENABLE_OPENAPI: preserve(), ENVIRONMENT: preserve(), FERNET_SECRET: preserve(), FRONTEND_URL: preserve(), MERCADOPAGO_ACCESS_TOKEN: preserve(), META_PHONE_NUMBER_ID: preserve(), META_WEBHOOK_VERIFY_TOKEN: preserve(), REDIS_URL: preserve(), RESEND_API_KEY: preserve(), RESEND_WEBHOOK_SECRET: preserve(), SECRET_KEY: preserve(), SIDECAR_SHARED_SECRET: preserve(), WEBAUTHN_RP_ID: preserve(), WEBAUTHN_RP_ORIGIN: preserve() },
  });
  const selliaCeleryWorker = service("sellia-celery-worker", {
    source: SellIARepo,
    replicas: { "sfo": 1 },
    build: { builder: "DOCKERFILE", dockerfilePath: "/Dockerfile.celery-worker" },
    env: { ACCESS_TOKEN_EXPIRE_MINUTES: preserve(), ALGORITHM: preserve(), ANTHROPIC_API_KEY: preserve(), DATABASE_URL: preserve(), ENABLE_OPENAPI: preserve(), ENVIRONMENT: preserve(), FERNET_SECRET: preserve(), FRONTEND_URL: preserve(), MERCADOPAGO_ACCESS_TOKEN: preserve(), META_PHONE_NUMBER_ID: preserve(), META_WEBHOOK_VERIFY_TOKEN: preserve(), REDIS_URL: preserve(), RESEND_API_KEY: preserve(), RESEND_WEBHOOK_SECRET: preserve(), SECRET_KEY: preserve(), SIDECAR_SHARED_SECRET: preserve(), WEBAUTHN_RP_ID: preserve(), WEBAUTHN_RP_ORIGIN: preserve() },
  });
  const redisService = service("redis", {
    replicas: { "sfo": 1 },
    networking: { privateNetworkEndpoint: "redis-9bd73ba2" },
  });
  const feedIA = service("feedIA", {
    source: github("lucasmarinskiba/feedIA", { checkSuites: false }),
    replicas: { "sfo": 1 },
    networking: { privateNetworkEndpoint: "feedia" },
  });

  return project("impartial-hope", {
    resources: [SellIA, Postgres, selliaCeleryBeat, selliaCeleryWorker, redisService, feedIA, Redis, redisVolume, postgresVolume],
  });
});
