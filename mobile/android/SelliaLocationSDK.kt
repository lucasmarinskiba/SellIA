/// SelliaLocationSDK — Android library for location check-in + real-time dashboard
/// Supports: QR scanning, manual entry, geofence, NPS feedback, staff tracking

package com.sellia.location.sdk

import android.content.Context
import android.location.Location
import com.google.android.gms.location.FusedLocationProviderClient
import com.google.android.gms.location.LocationServices
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.util.concurrent.TimeUnit

/// Main SDK entry point
object SelliaLocationSDK {
    private var apiClient: APIClient? = null
    private var geofenceManager: GeofenceManager? = null
    private var qrScanner: QRScanner? = null
    private var dashboardClient: DashboardWebSocketClient? = null

    fun initialize(context: Context, businessId: String, apiToken: String) {
        apiClient = APIClient(businessId, apiToken)
        geofenceManager = GeofenceManager(context)
        qrScanner = QRScanner()
        dashboardClient = DashboardWebSocketClient()
    }

    fun getAPIClient() = apiClient ?: throw Exception("SDK not initialized")
    fun getGeofenceManager() = geofenceManager ?: throw Exception("SDK not initialized")
    fun getQRScanner() = qrScanner ?: throw Exception("SDK not initialized")
    fun getDashboardClient() = dashboardClient ?: throw Exception("SDK not initialized")
}

// MARK: - API Client
class APIClient(
    val businessId: String,
    val token: String
) {
    private val baseURL = "https://api.sellia.app/api/v1"
    private val httpClient = OkHttpClient.Builder()
        .readTimeout(30, TimeUnit.SECONDS)
        .writeTimeout(30, TimeUnit.SECONDS)
        .build()

    /// Check-in endpoint
    fun checkin(
        locationId: String,
        checkinType: String,
        visitorPhone: String? = null,
        visitorEmail: String? = null,
        callback: (CheckinResponse?, Throwable?) -> Unit
    ) {
        val endpoint = "$baseURL/mobile/checkin/start"
        val payload = JSONObject().apply {
            put("location_id", locationId)
            put("checkin_type", checkinType)
            if (visitorPhone != null) put("visitor_phone", visitorPhone)
            if (visitorEmail != null) put("visitor_email", visitorEmail)
            put("device_id", android.provider.Settings.Secure.ANDROID_ID)
            put("app_version", getAppVersion())
        }

        val body = payload.toString().toRequestBody("application/json".toMediaType())
        val request = Request.Builder()
            .url(endpoint)
            .post(body)
            .addHeader("Authorization", "Bearer $token")
            .addHeader("Content-Type", "application/json")
            .build()

        httpClient.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                callback(null, e)
            }

            override fun onResponse(call: Call, response: Response) {
                try {
                    val responseBody = response.body?.string() ?: ""
                    val json = JSONObject(responseBody)
                    val result = CheckinResponse(
                        status = json.getString("status"),
                        checkinId = json.getString("checkin_id"),
                        checkinTime = json.getString("checkin_time"),
                        message = json.optString("message")
                    )
                    callback(result, null)
                } catch (e: Exception) {
                    callback(null, e)
                }
            }
        })
    }

    /// Checkout endpoint
    fun checkout(
        checkinId: String,
        visitedSections: List<String>,
        callback: (CheckoutResponse?, Throwable?) -> Unit
    ) {
        val endpoint = "$baseURL/locations/checkout"
        val payload = JSONObject().apply {
            put("checkin_id", checkinId)
            put("visited_sections", org.json.JSONArray(visitedSections))
        }

        val body = payload.toString().toRequestBody("application/json".toMediaType())
        val request = Request.Builder()
            .url(endpoint)
            .post(body)
            .addHeader("Authorization", "Bearer $token")
            .build()

        httpClient.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                callback(null, e)
            }

            override fun onResponse(call: Call, response: Response) {
                try {
                    val responseBody = response.body?.string() ?: ""
                    val json = JSONObject(responseBody)
                    val result = CheckoutResponse(
                        status = json.getString("status"),
                        dwellSeconds = json.getInt("dwell_seconds"),
                        dwellMinutes = json.getInt("dwell_minutes")
                    )
                    callback(result, null)
                } catch (e: Exception) {
                    callback(null, e)
                }
            }
        })
    }

    /// Submit feedback
    fun submitFeedback(
        locationId: String,
        npsScore: Int,
        comment: String? = null,
        topics: List<String>? = null,
        callback: (FeedbackResponse?, Throwable?) -> Unit
    ) {
        val endpoint = "$baseURL/locations/feedback"
        val payload = JSONObject().apply {
            put("location_id", locationId)
            put("nps_score", npsScore)
            if (comment != null) put("comment", comment)
            if (topics != null) put("topics", org.json.JSONArray(topics))
        }

        val body = payload.toString().toRequestBody("application/json".toMediaType())
        val request = Request.Builder()
            .url(endpoint)
            .post(body)
            .addHeader("Authorization", "Bearer $token")
            .build()

        httpClient.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                callback(null, e)
            }

            override fun onResponse(call: Call, response: Response) {
                try {
                    val responseBody = response.body?.string() ?: ""
                    val json = JSONObject(responseBody)
                    val result = FeedbackResponse(
                        status = json.getString("status"),
                        feedbackId = json.getString("feedback_id"),
                        sentiment = json.getString("sentiment")
                    )
                    callback(result, null)
                } catch (e: Exception) {
                    callback(null, e)
                }
            }
        })
    }

    /// Geofence check
    fun checkGeofence(
        latitude: Double,
        longitude: Double,
        callback: (GeofenceResponse?, Throwable?) -> Unit
    ) {
        val endpoint = "$baseURL/mobile/geofence/check"
        val payload = JSONObject().apply {
            put("latitude", latitude)
            put("longitude", longitude)
            put("business_id", businessId)
            put("accuracy_meters", 10.0)
        }

        val body = payload.toString().toRequestBody("application/json".toMediaType())
        val request = Request.Builder()
            .url(endpoint)
            .post(body)
            .addHeader("Authorization", "Bearer $token")
            .build()

        httpClient.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                callback(null, e)
            }

            override fun onResponse(call: Call, response: Response) {
                try {
                    val responseBody = response.body?.string() ?: ""
                    val json = JSONObject(responseBody)
                    val result = GeofenceResponse(
                        triggered = json.getBoolean("triggered"),
                        locationId = json.optString("location_id"),
                        locationName = json.optString("location_name"),
                        message = json.optString("message")
                    )
                    callback(result, null)
                } catch (e: Exception) {
                    callback(null, e)
                }
            }
        })
    }

    private fun getAppVersion(): String {
        return "1.0"  // TODO: get from BuildConfig
    }
}

// MARK: - Geofence Manager
class GeofenceManager(context: Context) {
    private val fusedLocationClient: FusedLocationProviderClient = LocationServices.getFusedLocationProviderClient(context)

    fun startMonitoring() {
        try {
            fusedLocationClient.lastLocation.addOnSuccessListener { location: Location? ->
                if (location != null) {
                    checkGeofence(location)
                }
            }
        } catch (e: SecurityException) {
            e.printStackTrace()
        }
    }

    private fun checkGeofence(location: Location) {
        SelliaLocationSDK.getAPIClient().checkGeofence(
            latitude = location.latitude,
            longitude = location.longitude
        ) { response, error ->
            if (response?.triggered == true) {
                println("Geofence triggered: ${response.message}")
                // Trigger check-in
            }
        }
    }
}

// MARK: - QR Scanner
class QRScanner {
    fun startScanning(callback: (String) -> Unit) {
        // Use ML Kit or ZXing library for QR scanning
        println("QR scanning started")
    }

    fun handleQRCode(code: String) {
        // Parse QR: selliaapp://checkin?location=...&type=...
        if (!code.startsWith("selliaapp://checkin?")) return

        val params = mutableMapOf<String, String>()
        code.substring("selliaapp://checkin?".length)
            .split("&")
            .forEach { pair ->
                val (key, value) = pair.split("=")
                params[key] = value
            }

        val locationId = params["location"] ?: return
        val checkinType = params["type"] ?: "qr_scan"

        // Trigger check-in
        SelliaLocationSDK.getAPIClient().checkin(
            locationId = locationId,
            checkinType = checkinType
        ) { response, error ->
            if (response != null) {
                println("Checked in: ${response.message}")
            }
        }
    }
}

// MARK: - WebSocket Dashboard Client
class DashboardWebSocketClient {
    private var webSocket: WebSocket? = null
    var onMessage: ((DashboardMessage) -> Unit)? = null

    fun connect(locationId: String, token: String) {
        val httpClient = OkHttpClient.Builder()
            .readTimeout(0, TimeUnit.MILLISECONDS)
            .build()

        val wsUrl = "wss://api.sellia.app/api/v1/ws/locations/$locationId"
        val request = Request.Builder()
            .url(wsUrl)
            .addHeader("Authorization", "Bearer $token")
            .build()

        webSocket = httpClient.newWebSocket(request, object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: Response) {
                println("WebSocket connected")
            }

            override fun onMessage(webSocket: WebSocket, text: String) {
                try {
                    val json = JSONObject(text)
                    val message = DashboardMessage(
                        type = json.getString("type"),
                        timestamp = json.getString("timestamp"),
                        data = json.optJSONObject("data")?.toString()
                    )
                    onMessage?.invoke(message)
                } catch (e: Exception) {
                    e.printStackTrace()
                }
            }

            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                println("WebSocket error: ${t.message}")
            }

            override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
                println("WebSocket disconnected")
            }
        })
    }

    fun disconnect() {
        webSocket?.close(1000, "Closing")
    }
}

// MARK: - Models
data class CheckinResponse(
    val status: String,
    val checkinId: String,
    val checkinTime: String,
    val message: String? = null
)

data class CheckoutResponse(
    val status: String,
    val dwellSeconds: Int,
    val dwellMinutes: Int
)

data class FeedbackResponse(
    val status: String,
    val feedbackId: String,
    val sentiment: String
)

data class GeofenceResponse(
    val triggered: Boolean,
    val locationId: String? = null,
    val locationName: String? = null,
    val message: String? = null
)

data class DashboardMessage(
    val type: String,
    val timestamp: String,
    val data: String? = null
)
