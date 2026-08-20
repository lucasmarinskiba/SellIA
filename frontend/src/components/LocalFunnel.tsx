import React, { useState } from "react";
import { MapPin, Users, TrendingUp, Mail } from "lucide-react";

interface Location {
  id: string;
  location_name: string;
  address: string;
  latitude: number;
  longitude: number;
  location_type: string;
  capacity: number;
  geofence_radius_km: number;
}

interface ProximityEvent {
  user_id: string;
  distance_km: number;
  detected_at: string;
}

interface OfflineMetrics {
  total_foot_traffic: number;
  unique_visitors: number;
  conversion_rate_offline: number;
  avg_dwell_time_minutes: number;
  total_revenue_from_visits: number;
  online_to_offline_conversions: number;
  offline_to_online_conversions: number;
  full_loop_conversions: number;
}

const LocalFunnel: React.FC = () => {
  const [activeTab, setActiveTab] = useState<"locations" | "proximity" | "analytics" | "reengagement">("locations");
  const [locations, setLocations] = useState<Location[]>([]);
  const [nearbyUsers, setNearbyUsers] = useState<ProximityEvent[]>([]);
  const [metrics, setMetrics] = useState<OfflineMetrics | null>(null);

  return (
    <div className="w-full bg-slate-900 text-white p-6 rounded-lg">
      <h1 className="text-3xl font-bold mb-6">Local-First Funnel (Phase 5)</h1>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 border-b border-slate-700">
        <button
          onClick={() => setActiveTab("locations")}
          className={`px-4 py-2 font-semibold transition ${
            activeTab === "locations" ? "border-b-2 border-blue-500 text-blue-400" : "text-slate-400"
          }`}
        >
          <MapPin className="inline mr-2 w-4 h-4" /> Locations
        </button>
        <button
          onClick={() => setActiveTab("proximity")}
          className={`px-4 py-2 font-semibold transition ${
            activeTab === "proximity" ? "border-b-2 border-blue-500 text-blue-400" : "text-slate-400"
          }`}
        >
          <Users className="inline mr-2 w-4 h-4" /> Proximity
        </button>
        <button
          onClick={() => setActiveTab("analytics")}
          className={`px-4 py-2 font-semibold transition ${
            activeTab === "analytics" ? "border-b-2 border-blue-500 text-blue-400" : "text-slate-400"
          }`}
        >
          <TrendingUp className="inline mr-2 w-4 h-4" /> Analytics
        </button>
        <button
          onClick={() => setActiveTab("reengagement")}
          className={`px-4 py-2 font-semibold transition ${
            activeTab === "reengagement" ? "border-b-2 border-blue-500 text-blue-400" : "text-slate-400"
          }`}
        >
          <Mail className="inline mr-2 w-4 h-4" /> Re-engagement
        </button>
      </div>

      {/* Locations Tab */}
      {activeTab === "locations" && (
        <div className="space-y-4">
          <h2 className="text-2xl font-bold mb-4">Location Profiles</h2>
          <div className="bg-slate-800 p-4 rounded-lg mb-4">
            <p className="text-slate-300 mb-2">Add Location</p>
            <div className="grid grid-cols-3 gap-3">
              <input type="text" placeholder="Location Name" className="bg-slate-700 p-2 rounded text-sm" />
              <input type="text" placeholder="Address" className="bg-slate-700 p-2 rounded text-sm" />
              <select className="bg-slate-700 p-2 rounded text-sm">
                <option>showroom</option>
                <option>factory</option>
                <option>office</option>
                <option>retail</option>
                <option>warehouse</option>
              </select>
              <input type="number" placeholder="Latitude" className="bg-slate-700 p-2 rounded text-sm" />
              <input type="number" placeholder="Longitude" className="bg-slate-700 p-2 rounded text-sm" />
              <input type="number" placeholder="Geofence (km)" className="bg-slate-700 p-2 rounded text-sm" />
            </div>
            <button className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded mt-3 text-sm font-semibold">
              Create Location
            </button>
          </div>

          <div className="space-y-3">
            {locations.length === 0 ? (
              <p className="text-slate-400">No locations yet. Create one above.</p>
            ) : (
              locations.map((loc) => (
                <div key={loc.id} className="bg-slate-800 p-4 rounded-lg">
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="font-bold text-lg">{loc.location_name}</h3>
                      <p className="text-slate-400 text-sm">{loc.address}</p>
                      <p className="text-slate-400 text-sm">
                        Type: {loc.location_type} | Capacity: {loc.capacity} | Geofence: {loc.geofence_radius_km} km
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-xs text-slate-500">Coordinates</p>
                      <p className="text-sm font-mono">{loc.latitude.toFixed(3)}, {loc.longitude.toFixed(3)}</p>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* Proximity Tab */}
      {activeTab === "proximity" && (
        <div className="space-y-4">
          <h2 className="text-2xl font-bold mb-4">Nearby Users Detection</h2>
          <div className="bg-slate-800 p-4 rounded-lg mb-4">
            <div className="grid grid-cols-2 gap-3">
              <input type="number" placeholder="User Latitude" className="bg-slate-700 p-2 rounded text-sm" />
              <input type="number" placeholder="User Longitude" className="bg-slate-700 p-2 rounded text-sm" />
              <button className="col-span-2 bg-green-600 hover:bg-green-700 px-4 py-2 rounded text-sm font-semibold">
                Check Nearby Locations
              </button>
            </div>
          </div>

          <div className="bg-slate-800 p-4 rounded-lg">
            <h3 className="font-bold mb-3">Detected Proximities</h3>
            {nearbyUsers.length === 0 ? (
              <p className="text-slate-400 text-sm">No proximity events yet.</p>
            ) : (
              <div className="space-y-2">
                {nearbyUsers.map((event, idx) => (
                  <div key={idx} className="bg-slate-700 p-3 rounded flex justify-between items-center">
                    <div>
                      <p className="text-sm font-semibold">User: {event.user_id.slice(0, 8)}...</p>
                      <p className="text-xs text-slate-400">{new Date(event.detected_at).toLocaleString()}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-bold text-blue-400">{event.distance_km.toFixed(2)} km</p>
                      <p className="text-xs text-slate-400">Automation triggered</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Analytics Tab */}
      {activeTab === "analytics" && (
        <div className="space-y-4">
          <h2 className="text-2xl font-bold mb-4">Offline Analytics</h2>
          {metrics ? (
            <div className="grid grid-cols-4 gap-4">
              <div className="bg-slate-800 p-4 rounded-lg">
                <p className="text-slate-400 text-sm">Foot Traffic</p>
                <p className="text-3xl font-bold text-blue-400">{metrics.total_foot_traffic}</p>
                <p className="text-xs text-slate-500">unique: {metrics.unique_visitors}</p>
              </div>
              <div className="bg-slate-800 p-4 rounded-lg">
                <p className="text-slate-400 text-sm">Conversion Rate</p>
                <p className="text-3xl font-bold text-green-400">{metrics.conversion_rate_offline.toFixed(1)}%</p>
                <p className="text-xs text-slate-500">offline conversions</p>
              </div>
              <div className="bg-slate-800 p-4 rounded-lg">
                <p className="text-slate-400 text-sm">Avg Dwell Time</p>
                <p className="text-3xl font-bold text-purple-400">{metrics.avg_dwell_time_minutes.toFixed(1)}</p>
                <p className="text-xs text-slate-500">minutes</p>
              </div>
              <div className="bg-slate-800 p-4 rounded-lg">
                <p className="text-slate-400 text-sm">Revenue</p>
                <p className="text-3xl font-bold text-yellow-400">${metrics.total_revenue_from_visits.toFixed(0)}</p>
                <p className="text-xs text-slate-500">from visits</p>
              </div>
            </div>
          ) : (
            <p className="text-slate-400">Load metrics to see analytics.</p>
          )}

          <div className="bg-slate-800 p-4 rounded-lg mt-4">
            <h3 className="font-bold mb-3">Attribution Conversions</h3>
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-slate-700 p-3 rounded text-center">
                <p className="text-slate-400 text-xs mb-1">Online → Offline</p>
                <p className="text-2xl font-bold text-blue-400">{metrics?.online_to_offline_conversions || 0}</p>
              </div>
              <div className="bg-slate-700 p-3 rounded text-center">
                <p className="text-slate-400 text-xs mb-1">Offline → Online</p>
                <p className="text-2xl font-bold text-green-400">{metrics?.offline_to_online_conversions || 0}</p>
              </div>
              <div className="bg-slate-700 p-3 rounded text-center">
                <p className="text-slate-400 text-xs mb-1">Full Loop</p>
                <p className="text-2xl font-bold text-purple-400">{metrics?.full_loop_conversions || 0}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Re-engagement Tab */}
      {activeTab === "reengagement" && (
        <div className="space-y-4">
          <h2 className="text-2xl font-bold mb-4">Post-Visit Re-engagement</h2>
          <div className="bg-slate-800 p-4 rounded-lg mb-4">
            <p className="text-slate-300 mb-2">Create Post-Visit Sequence</p>
            <div className="space-y-3">
              <input type="text" placeholder="Sequence Name" className="w-full bg-slate-700 p-2 rounded text-sm" />
              <select className="w-full bg-slate-700 p-2 rounded text-sm">
                <option>post_visit</option>
                <option>no_purchase_visit</option>
                <option>high_dwell</option>
              </select>
              <div className="flex gap-2">
                <input type="number" placeholder="SMS count" className="flex-1 bg-slate-700 p-2 rounded text-sm" />
                <input type="number" placeholder="Email count" className="flex-1 bg-slate-700 p-2 rounded text-sm" />
                <input
                  type="number"
                  placeholder="WhatsApp count"
                  className="flex-1 bg-slate-700 p-2 rounded text-sm"
                />
              </div>
              <button className="w-full bg-purple-600 hover:bg-purple-700 px-4 py-2 rounded text-sm font-semibold">
                Create Sequence
              </button>
            </div>
          </div>

          <div className="bg-slate-800 p-4 rounded-lg">
            <h3 className="font-bold mb-3">Active Sequences</h3>
            <p className="text-slate-400 text-sm">Sequences will auto-trigger for visits without purchase.</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default LocalFunnel;
