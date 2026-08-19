/// SelliaLocationSDK — iOS framework for location check-in + real-time dashboard
/// Supports: QR scanning, manual entry, geofence, NPS feedback, staff tracking

import Foundation
import CoreLocation

/// Main SDK entry point
public class SelliaLocationSDK {
    static let shared = SelliaLocationSDK()

    let apiClient: APIClient
    let geofenceManager: GeofenceManager
    let qrScanner: QRScanner
    let dashboardClient: DashboardWebSocketClient

    private init() {
        self.apiClient = APIClient()
        self.geofenceManager = GeofenceManager()
        self.qrScanner = QRScanner()
        self.dashboardClient = DashboardWebSocketClient()
    }

    /// Initialize SDK with business & location config
    public func initialize(businessId: String, apiToken: String) {
        apiClient.businessId = businessId
        apiClient.token = apiToken
    }
}

// MARK: - API Client
class APIClient {
    var businessId: String?
    var token: String?
    let baseURL = "https://api.sellia.app/api/v1"

    /// Check-in endpoint
    func checkin(
        locationId: String,
        checkinType: String,
        visitorPhone: String? = nil,
        completion: @escaping (CheckinResponse?, Error?) -> Void
    ) {
        let endpoint = "\(baseURL)/mobile/checkin/start"
        let payload: [String: Any] = [
            "location_id": locationId,
            "checkin_type": checkinType,
            "visitor_phone": visitorPhone ?? NSNull(),
            "device_id": UIDevice.current.identifierForVendor?.uuidString ?? "",
            "app_version": Bundle.main.appVersion
        ]

        var request = URLRequest(url: URL(string: endpoint)!)
        request.httpMethod = "POST"
        request.setValue("Bearer \(token ?? "")", forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try? JSONSerialization.data(withJSONObject: payload)

        URLSession.shared.dataTask(with: request) { data, _, error in
            if let error = error {
                completion(nil, error)
                return
            }

            guard let data = data else {
                completion(nil, NSError(domain: "APIClient", code: -1))
                return
            }

            let response = try? JSONDecoder().decode(CheckinResponse.self, from: data)
            completion(response, nil)
        }.resume()
    }

    /// Checkout endpoint
    func checkout(
        checkinId: String,
        visitedSections: [String],
        completion: @escaping (CheckoutResponse?, Error?) -> Void
    ) {
        let endpoint = "\(baseURL)/locations/checkout"
        let payload: [String: Any] = [
            "checkin_id": checkinId,
            "visited_sections": visitedSections
        ]

        var request = URLRequest(url: URL(string: endpoint)!)
        request.httpMethod = "POST"
        request.setValue("Bearer \(token ?? "")", forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try? JSONSerialization.data(withJSONObject: payload)

        URLSession.shared.dataTask(with: request) { data, _, error in
            if let error = error {
                completion(nil, error)
                return
            }

            guard let data = data else {
                completion(nil, NSError(domain: "APIClient", code: -1))
                return
            }

            let response = try? JSONDecoder().decode(CheckoutResponse.self, from: data)
            completion(response, nil)
        }.resume()
    }

    /// Submit feedback
    func submitFeedback(
        locationId: String,
        npsScore: Int,
        comment: String?,
        completion: @escaping (FeedbackResponse?, Error?) -> Void
    ) {
        let endpoint = "\(baseURL)/locations/feedback"
        let payload: [String: Any] = [
            "location_id": locationId,
            "nps_score": npsScore,
            "comment": comment ?? NSNull()
        ]

        var request = URLRequest(url: URL(string: endpoint)!)
        request.httpMethod = "POST"
        request.setValue("Bearer \(token ?? "")", forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try? JSONSerialization.data(withJSONObject: payload)

        URLSession.shared.dataTask(with: request) { data, _, error in
            if let error = error {
                completion(nil, error)
                return
            }

            guard let data = data else {
                completion(nil, NSError(domain: "APIClient", code: -1))
                return
            }

            let response = try? JSONDecoder().decode(FeedbackResponse.self, from: data)
            completion(response, nil)
        }.resume()
    }

    /// Geofence check
    func checkGeofence(
        latitude: Double,
        longitude: Double,
        completion: @escaping (GeofenceResponse?, Error?) -> Void
    ) {
        let endpoint = "\(baseURL)/mobile/geofence/check"
        let payload: [String: Any] = [
            "latitude": latitude,
            "longitude": longitude,
            "business_id": businessId ?? "",
            "accuracy_meters": 10.0
        ]

        var request = URLRequest(url: URL(string: endpoint)!)
        request.httpMethod = "POST"
        request.setValue("Bearer \(token ?? "")", forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try? JSONSerialization.data(withJSONObject: payload)

        URLSession.shared.dataTask(with: request) { data, _, error in
            if let error = error {
                completion(nil, error)
                return
            }

            guard let data = data else {
                completion(nil, NSError(domain: "APIClient", code: -1))
                return
            }

            let response = try? JSONDecoder().decode(GeofenceResponse.self, from: data)
            completion(response, nil)
        }.resume()
    }
}

// MARK: - Geofence Manager
class GeofenceManager: NSObject, CLLocationManagerDelegate {
    let locationManager = CLLocationManager()

    override init() {
        super.init()
        locationManager.delegate = self
        locationManager.desiredAccuracy = kCLLocationAccuracyBest
        locationManager.requestAlwaysAndWhenInUseAuthorization()
    }

    func startMonitoring() {
        locationManager.startUpdatingLocation()
    }

    func stopMonitoring() {
        locationManager.stopUpdatingLocation()
    }

    func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        guard let latest = locations.last else { return }

        // Check geofence every 30-60s
        SelliaLocationSDK.shared.apiClient.checkGeofence(
            latitude: latest.coordinate.latitude,
            longitude: latest.coordinate.longitude
        ) { response, error in
            if let response = response, response.triggered {
                DispatchQueue.main.async {
                    print("Geofence triggered: \(response.message ?? "")")
                }
            }
        }
    }
}

// MARK: - QR Scanner
class QRScanner {
    func startScanning(completion: @escaping (String) -> Void) {
        // iOS 16+ uses VisionKit
        // Delegate: AVCaptureMetadataOutputObjectsDelegate
        print("QR scanning started")
    }

    func handleQRCode(_ code: String) {
        // Parse QR: selliaapp://checkin?location=...&type=...
        let components = code.split(separator: "?")
        guard components.count == 2 else { return }

        let params = String(components[1]).split(separator: "&")
        var locationId = ""
        var checkinType = "qr_scan"

        for param in params {
            let kv = param.split(separator: "=")
            if kv.count == 2 {
                if kv[0] == "location" {
                    locationId = String(kv[1])
                } else if kv[0] == "type" {
                    checkinType = String(kv[1])
                }
            }
        }

        // Trigger check-in
        SelliaLocationSDK.shared.apiClient.checkin(
            locationId: locationId,
            checkinType: checkinType
        ) { response, error in
            if let response = response {
                print("Checked in: \(response.message ?? "")")
            }
        }
    }
}

// MARK: - WebSocket Dashboard Client
class DashboardWebSocketClient: NSObject, URLSessionWebSocketDelegate {
    var webSocket: URLSessionWebSocket?
    var onMessage: ((DashboardMessage) -> Void)?

    func connect(locationId: String, token: String) {
        let url = URL(string: "wss://api.sellia.app/api/v1/ws/locations/\(locationId)")!
        var request = URLRequest(url: url)
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")

        let session = URLSession(configuration: .default, delegate: self, delegateQueue: .main)
        webSocket = session.webSocketTask(with: request)
        webSocket?.resume()

        receiveMessage()
    }

    func disconnect() {
        webSocket?.cancel(with: .goingAway, reason: nil)
    }

    private func receiveMessage() {
        webSocket?.receive { [weak self] result in
            switch result {
            case .success(.string(let text)):
                if let data = text.data(using: .utf8),
                   let json = try? JSONDecoder().decode(DashboardMessage.self, from: data) {
                    self?.onMessage?(json)
                }
                self?.receiveMessage()

            case .success(.data(let data)):
                if let json = try? JSONDecoder().decode(DashboardMessage.self, from: data) {
                    self?.onMessage?(json)
                }
                self?.receiveMessage()

            case .failure(let error):
                print("WebSocket error: \(error)")
            }
        }
    }

    func urlSession(_ session: URLSession, webSocketTask: URLSessionWebSocketTask, didOpenWithProtocol protocol: String?) {
        print("WebSocket connected")
    }

    func urlSession(_ session: URLSession, webSocketTask: URLSessionWebSocketTask, didCloseWith closeCode: URLSessionWebSocketTask.CloseCode, reason: Data?) {
        print("WebSocket disconnected")
    }
}

// MARK: - Models
struct CheckinResponse: Codable {
    let status: String
    let checkinId: String
    let checkinTime: String
    let message: String?

    enum CodingKeys: String, CodingKey {
        case status
        case checkinId = "checkin_id"
        case checkinTime = "checkin_time"
        case message
    }
}

struct CheckoutResponse: Codable {
    let status: String
    let dwellSeconds: Int
    let dwellMinutes: Int

    enum CodingKeys: String, CodingKey {
        case status
        case dwellSeconds = "dwell_seconds"
        case dwellMinutes = "dwell_minutes"
    }
}

struct FeedbackResponse: Codable {
    let status: String
    let feedbackId: String
    let sentiment: String

    enum CodingKeys: String, CodingKey {
        case status
        case feedbackId = "feedback_id"
        case sentiment
    }
}

struct GeofenceResponse: Codable {
    let triggered: Bool
    let locationId: String?
    let locationName: String?
    let message: String?

    enum CodingKeys: String, CodingKey {
        case triggered
        case locationId = "location_id"
        case locationName = "location_name"
        case message
    }
}

struct DashboardMessage: Codable {
    let type: String
    let timestamp: String
    let data: [String: AnyCodable]?
}

enum AnyCodable: Codable {
    case null
    case bool(Bool)
    case int(Int)
    case double(Double)
    case string(String)

    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        switch self {
        case .null:
            try container.encodeNil()
        case .bool(let b):
            try container.encode(b)
        case .int(let i):
            try container.encode(i)
        case .double(let d):
            try container.encode(d)
        case .string(let s):
            try container.encode(s)
        }
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        if container.decodeNil() {
            self = .null
        } else if let b = try? container.decode(Bool.self) {
            self = .bool(b)
        } else if let i = try? container.decode(Int.self) {
            self = .int(i)
        } else if let d = try? container.decode(Double.self) {
            self = .double(d)
        } else if let s = try? container.decode(String.self) {
            self = .string(s)
        } else {
            throw DecodingError.dataCorruptedError(in: container, debugDescription: "Cannot decode AnyCodable")
        }
    }
}

// Bundle extension
extension Bundle {
    var appVersion: String {
        infoDictionary?["CFBundleShortVersionString"] as? String ?? "1.0"
    }
}
