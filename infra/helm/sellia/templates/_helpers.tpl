{{/*
Expand the name of the chart.
*/}}
{{- define "sellia.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "sellia.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "sellia.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "sellia.labels" -}}
helm.sh/chart: {{ include "sellia.chart" . }}
{{ include "sellia.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "sellia.selectorLabels" -}}
app.kubernetes.io/name: {{ include "sellia.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "sellia.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "sellia.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Envoy static configuration with optional ext_authz sidecar
*/}}
{{- define "sellia.envoyConfig" -}}
static_resources:
  listeners:
    - name: listener_http
      address:
        socket_address:
          address: 0.0.0.0
          port_value: 80
      filter_chains:
        - filters:
            - name: envoy.filters.network.http_connection_manager
              typed_config:
                "@type": type.googleapis.com/envoy.extensions.filters.network.http_connection_manager.v3.HttpConnectionManager
                stat_prefix: ingress_http
                codec_type: AUTO
                use_remote_address: true
                xff_num_trusted_hops: 1

                access_log:
                  - name: envoy.access_loggers.stdout
                    typed_config:
                      "@type": type.googleapis.com/envoy.extensions.access_loggers.stream.v3.StdoutAccessLog
                      log_format:
                        json_format:
                          timestamp: "%START_TIME%"
                          method: "%REQ(:METHOD)%"
                          path: "%REQ(X-ENVOY-ORIGINAL-PATH?:PATH)%"
                          protocol: "%PROTOCOL%"
                          response_code: "%RESPONSE_CODE%"
                          response_flags: "%RESPONSE_FLAGS%"
                          bytes_received: "%BYTES_RECEIVED%"
                          bytes_sent: "%BYTES_SENT%"
                          duration_ms: "%DURATION%"
                          user_agent: "%REQ(USER-AGENT)%"
                          request_id: "%REQ(X-REQUEST-ID)%"
                          cf_connecting_ip: "%REQ(CF-CONNECTING-IP)%"
                          cf_ray: "%REQ(CF-RAY)%"
                          cf_ipcountry: "%REQ(CF-IPCOUNTRY)%"
                          x_forwarded_for: "%REQ(X-FORWARDED-FOR)%"
                          authority: "%REQ(:AUTHORITY)%"
                          upstream_host: "%UPSTREAM_HOST%"
                          upstream_cluster: "%UPSTREAM_CLUSTER%"

                route_config:
                  name: local_route
                  virtual_hosts:
                    - name: sellia
                      domains: ["*"]
                      routes:
                        - match:
                            safe_regex:
                              google_re2: {}
                              regex: "^/(docs|redoc|openapi\\.json)$"
                          direct_response:
                            status: 404
                            body:
                              inline_string: "Not Found"

                        - match:
                            path: "/envoy-health"
                          direct_response:
                            status: 200
                            body:
                              inline_string: "healthy\n"

                        - match:
                            prefix: "/api/v1/ws/"
                          route:
                            cluster: backend
                            timeout: 0s
                            upgrade_configs:
                              - upgrade_type: websocket
                                enabled: true

                        - match:
                            prefix: "/api/v1/upload"
                          route:
                            cluster: backend

                        - match:
                            prefix: "/api/"
                          route:
                            cluster: backend
                          typed_per_filter_config:
                            envoy.filters.http.local_ratelimit:
                              "@type": type.googleapis.com/envoy.extensions.filters.http.local_ratelimit.v3.LocalRateLimit
                              stat_prefix: backend_ratelimit
                              token_bucket:
                                max_tokens: 20
                                tokens_per_fill: 10
                                fill_interval: 60s
                              filter_enabled:
                                runtime_key: local_rate_limit_enabled
                                default_value:
                                  numerator: 100
                                  denominator: HUNDRED
                              filter_enforced:
                                runtime_key: local_rate_limit_enforced
                                default_value:
                                  numerator: 100
                                  denominator: HUNDRED
                          response_headers_to_add:
                            - header:
                                key: Cache-Control
                                value: "no-store, no-cache, must-revalidate, private"
                            - header:
                                key: Pragma
                                value: "no-cache"
                            - header:
                                key: Expires
                                value: "0"

                        - match:
                            prefix: "/"
                          route:
                            cluster: frontend
                            timeout: 0s

                      response_headers_to_add:
                        - header:
                            key: X-Frame-Options
                            value: DENY
                        - header:
                            key: X-Content-Type-Options
                            value: nosniff
                        - header:
                            key: X-XSS-Protection
                            value: "1; mode=block"
                        - header:
                            key: Referrer-Policy
                            value: strict-origin-when-cross-origin
                        - header:
                            key: Permissions-Policy
                            value: "geolocation=(), microphone=(), camera=(), payment=(), usb=(), magnetometer=(), gyroscope=(), accelerometer=()"
                        - header:
                            key: Strict-Transport-Security
                            value: "max-age=63072000; includeSubDomains; preload"

                http_filters:
                  - name: envoy.filters.http.lua
                    typed_config:
                      "@type": type.googleapis.com/envoy.extensions.filters.http.lua.v3.Lua
                      inline_code: |
                        function envoy_on_request(request_handle)
                          local cf_ip = request_handle:headers():get("CF-Connecting-IP")
                          if cf_ip then
                            request_handle:headers():add("X-Real-IP", cf_ip)
                          end
                        end

{{- if .Values.sidecar.enabled }}
                  - name: envoy.filters.http.ext_authz
                    typed_config:
                      "@type": type.googleapis.com/envoy.extensions.filters.http.ext_authz.v3.ExtAuthz
                      http_service:
                        server_uri:
                          uri: "http://127.0.0.1:8081"
                          cluster: sidecar
                          timeout: 5s
                        authorization_request:
                          allowed_headers:
                            patterns:
                              - exact: authorization
                              - exact: user-agent
                              - exact: x-request-id
                              - exact: cf-connecting-ip
                              - exact: cf-ray
                              - exact: cf-ipcountry
                              - exact: x-forwarded-for
                              - exact: x-forwarded-method
                              - exact: x-forwarded-uri
                              - exact: x-forwarded-host
                        authorization_response:
                          allowed_upstream_headers:
                            patterns:
                              - exact: x-user-id
                              - exact: x-user-email
                              - exact: x-user-role
                              - exact: x-authenticated
                              - exact: x-ratelimit-limit
                              - exact: x-ratelimit-remaining
                          allowed_client_headers:
                            patterns:
                              - exact: x-ratelimit-limit
                              - exact: x-ratelimit-remaining
                              - exact: retry-after
                      transport_api_version: V3
                      include_peer_certificate: false
{{- end }}

                  - name: envoy.filters.http.local_ratelimit
                    typed_config:
                      "@type": type.googleapis.com/envoy.extensions.filters.http.local_ratelimit.v3.LocalRateLimit
                      stat_prefix: http_local_rate_limiter
                      token_bucket:
                        max_tokens: 200
                        tokens_per_fill: 100
                        fill_interval: 60s
                      filter_enabled:
                        runtime_key: local_rate_limit_enabled
                        default_value:
                          numerator: 100
                          denominator: HUNDRED
                      filter_enforced:
                        runtime_key: local_rate_limit_enforced
                        default_value:
                          numerator: 100
                          denominator: HUNDRED
                      response_headers_to_add:
                        - append_action: OVERWRITE_IF_EXISTS_OR_ADD
                          header:
                            key: x-local-rate-limit
                            value: 'true'

                  - name: envoy.filters.http.compressor
                    typed_config:
                      "@type": type.googleapis.com/envoy.extensions.filters.http.compressor.v3.Compressor
                      response_direction_config:
                        common_config:
                          min_content_length: 100
                          content_type:
                            - text/plain
                            - text/css
                            - text/xml
                            - application/json
                            - application/javascript
                            - application/rss+xml
                            - application/atom+xml
                            - image/svg+xml
                        disable_on_etag_header: false
                      request_direction_config:
                        common_config:
                          enabled:
                            default_value: false
                            runtime_key: request_compressor_enabled
                      compressor_library:
                        name: text_optimized
                        typed_config:
                          "@type": type.googleapis.com/envoy.extensions.compression.gzip.compressor.v3.Gzip
                          memory_level: 6
                          window_bits: 12
                          compression_level: COMPRESSION_LEVEL_6
                          compression_strategy: DEFAULT_STRATEGY

                  - name: envoy.filters.http.router
                    typed_config:
                      "@type": type.googleapis.com/envoy.extensions.filters.http.router.v3.Router

  clusters:
    - name: frontend
      connect_timeout: 5s
      type: STRICT_DNS
      lb_policy: ROUND_ROBIN
      load_assignment:
        cluster_name: frontend
        endpoints:
          - lb_endpoints:
              - endpoint:
                  address:
                    socket_address:
                      address: {{ include "sellia.fullname" . }}-frontend
                      port_value: 3000
      health_checks:
        - timeout: 5s
          interval: 10s
          unhealthy_threshold: 3
          healthy_threshold: 2
          http_health_check:
            path: /
      circuit_breakers:
        thresholds:
          - max_connections: 1000
            max_pending_requests: 1000
            max_requests: 1000
            max_retries: 3

    - name: backend
      connect_timeout: 5s
      type: STRICT_DNS
      lb_policy: ROUND_ROBIN
      load_assignment:
        cluster_name: backend
        endpoints:
          - lb_endpoints:
              - endpoint:
                  address:
                    socket_address:
                      address: {{ include "sellia.fullname" . }}-backend
                      port_value: 8000
      health_checks:
        - timeout: 5s
          interval: 10s
          unhealthy_threshold: 3
          healthy_threshold: 2
          http_health_check:
            path: /health
      circuit_breakers:
        thresholds:
          - max_connections: 1000
            max_pending_requests: 1000
            max_requests: 1000
            max_retries: 3

{{- if .Values.sidecar.enabled }}
    - name: sidecar
      connect_timeout: 1s
      type: STATIC
      lb_policy: ROUND_ROBIN
      load_assignment:
        cluster_name: sidecar
        endpoints:
          - lb_endpoints:
              - endpoint:
                  address:
                    socket_address:
                      address: 127.0.0.1
                      port_value: 8081
{{- end }}

  admin:
    address:
      socket_address:
        address: 0.0.0.0
        port_value: 9901
    access_log:
      - name: envoy.access_loggers.stdout
        typed_config:
          "@type": type.googleapis.com/envoy.extensions.access_loggers.stream.v3.StdoutAccessLog
{{- end }}
