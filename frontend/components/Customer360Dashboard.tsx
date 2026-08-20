import React, { useState, useEffect } from 'react';
import { Mail, Phone, MapPin, Briefcase, TrendingUp, AlertTriangle, Target, Heart, Star, Send } from 'lucide-react';

const Customer360Dashboard: React.FC<{ customerId: string; businessId: string }> = ({ customerId, businessId }) => {
  const [profile, setProfile] = useState<any>(null);
  const [scores, setScores] = useState<any>(null);
  const [insights, setInsights] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchProfile();
  }, [customerId, businessId]);

  const fetchProfile = async () => {
    try {
      setLoading(true);
      const profileRes = await fetch(
        `/api/v1/customers/${customerId}/profile?business_id=${businessId}`
      );
      const profileData = await profileRes.json();
      setProfile(profileData);

      if (profileData.scores) {
        setScores(profileData.scores);
      }

      if (profileData.insights) {
        setInsights(profileData.insights);
      }

      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch profile:', error);
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="w-full flex items-center justify-center p-8">
        <div className="text-gray-500">Cargando perfil del cliente...</div>
      </div>
    );
  }

  if (!profile || !profile.profile) {
    return (
      <div className="w-full flex items-center justify-center p-8">
        <div className="text-gray-500">Cliente no encontrado</div>
      </div>
    );
  }

  const { profile: p, scores: s, segments, insights: ins, metadata } = profile;

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600 bg-green-50';
    if (score >= 60) return 'text-yellow-600 bg-yellow-50';
    if (score >= 40) return 'text-orange-600 bg-orange-50';
    return 'text-red-600 bg-red-50';
  };

  const getLifecycleColor = (stage: string) => {
    switch (stage) {
      case 'prospect':
        return 'bg-blue-100 text-blue-800';
      case 'lead':
        return 'bg-cyan-100 text-cyan-800';
      case 'customer':
        return 'bg-green-100 text-green-800';
      case 'loyal':
        return 'bg-emerald-100 text-emerald-800';
      case 'advocate':
        return 'bg-purple-100 text-purple-800';
      case 'inactive':
        return 'bg-gray-100 text-gray-800';
      case 'lost':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="w-full space-y-6 p-6 bg-gray-50">
      {/* Header / Profile Card */}
      <div className="bg-white p-6 rounded-lg shadow border-t-4 border-blue-600">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 bg-gradient-to-br from-blue-400 to-blue-600 rounded-full flex items-center justify-center text-white text-2xl font-bold">
              {p.first_name?.charAt(0)}{p.last_name?.charAt(0)}
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                {p.first_name} {p.last_name}
              </h1>
              <span className={`inline-block mt-2 px-3 py-1 rounded-full text-sm font-semibold ${getLifecycleColor(p.lifecycle_stage)}`}>
                {p.lifecycle_stage}
              </span>
            </div>
          </div>
          <div className="text-right">
            <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2">
              <Send className="w-4 h-4" />
              Enviar
            </button>
          </div>
        </div>

        {/* Contact Info */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-4">
          {p.email && (
            <div className="flex items-center gap-2">
              <Mail className="w-5 h-5 text-gray-600" />
              <div>
                <p className="text-xs text-gray-600">Email</p>
                <p className="font-semibold text-gray-900">{p.email}</p>
              </div>
            </div>
          )}
          {p.phone && (
            <div className="flex items-center gap-2">
              <Phone className="w-5 h-5 text-gray-600" />
              <div>
                <p className="text-xs text-gray-600">Teléfono</p>
                <p className="font-semibold text-gray-900">{p.phone}</p>
              </div>
            </div>
          )}
          {p.company && (
            <div className="flex items-center gap-2">
              <Briefcase className="w-5 h-5 text-gray-600" />
              <div>
                <p className="text-xs text-gray-600">Empresa</p>
                <p className="font-semibold text-gray-900">{p.company}</p>
              </div>
            </div>
          )}
          {p.industry && (
            <div className="flex items-center gap-2">
              <MapPin className="w-5 h-5 text-gray-600" />
              <div>
                <p className="text-xs text-gray-600">Industria</p>
                <p className="font-semibold text-gray-900">{p.industry}</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Key Metrics */}
      {s && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className={`p-6 rounded-lg shadow ${getScoreColor(s.customer_lifetime_value / 100)}`}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium opacity-75">Lifetime Value</p>
                <p className="text-3xl font-bold mt-2">${(s.customer_lifetime_value / 100).toLocaleString()}</p>
              </div>
              <TrendingUp className="w-10 h-10 opacity-50" />
            </div>
          </div>

          <div className={`p-6 rounded-lg shadow ${getScoreColor(s.rfm_score)}`}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium opacity-75">RFM Score</p>
                <p className="text-3xl font-bold mt-2">{s.rfm_score}</p>
              </div>
              <Star className="w-10 h-10 opacity-50" />
            </div>
          </div>

          <div className={`p-6 rounded-lg shadow ${s.churn_risk > 70 ? getScoreColor(0) : getScoreColor(100)}`}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium opacity-75">Churn Risk</p>
                <p className="text-3xl font-bold mt-2">{s.churn_risk}%</p>
              </div>
              <AlertTriangle className="w-10 h-10 opacity-50" />
            </div>
          </div>

          <div className={`p-6 rounded-lg shadow ${getScoreColor(s.engagement)}`}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium opacity-75">Engagement</p>
                <p className="text-3xl font-bold mt-2">{s.engagement}</p>
              </div>
              <Heart className="w-10 h-10 opacity-50" />
            </div>
          </div>
        </div>
      )}

      {/* Segments */}
      {segments && segments.length > 0 && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-lg font-bold text-gray-900 mb-4">Segmentos</h2>
          <div className="flex flex-wrap gap-2">
            {segments.map((segment) => (
              <span
                key={segment.name}
                className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-semibold"
              >
                {segment.name}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Next Best Actions & Recommendations */}
      {s && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-white p-6 rounded-lg shadow border-l-4 border-green-500">
            <h3 className="font-bold text-gray-900 mb-2">Siguiente mejor acción</h3>
            <p className="text-lg font-semibold text-green-600">{s.next_best_action}</p>
            <p className="text-sm text-gray-600 mt-2">Canal: {s.next_best_channel}</p>
          </div>

          <div className="bg-white p-6 rounded-lg shadow border-l-4 border-blue-500">
            <h3 className="font-bold text-gray-900 mb-2">Propensión a comprar</h3>
            <div className="w-full bg-gray-200 rounded-full h-3 mt-2">
              <div
                className="bg-blue-600 h-3 rounded-full"
                style={{ width: `${s.propensity_to_buy}%` }}
              ></div>
            </div>
            <p className="text-sm text-gray-600 mt-2">{s.propensity_to_buy}% de probabilidad</p>
          </div>
        </div>
      )}

      {/* Insights */}
      {ins && ins.length > 0 && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-lg font-bold text-gray-900 mb-4">Recomendaciones AI</h2>
          <div className="space-y-3">
            {ins.slice(0, 5).map((insight) => (
              <div
                key={insight.insight_id}
                className="p-4 bg-blue-50 border border-blue-200 rounded-lg"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="font-semibold text-gray-900">{insight.title}</p>
                    <p className="text-sm text-gray-600 mt-1">{insight.description}</p>
                    {insight.recommended_action && (
                      <p className="text-sm text-blue-700 font-medium mt-2">
                        Acción: {insight.recommended_action} ({insight.recommended_channel})
                      </p>
                    )}
                  </div>
                  <span className="text-xs bg-blue-200 text-blue-800 px-2 py-1 rounded font-semibold ml-2">
                    {insight.confidence}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tags */}
      {p.tags && p.tags.length > 0 && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="font-bold text-gray-900 mb-3">Tags</h3>
          <div className="flex flex-wrap gap-2">
            {p.tags.map((tag) => (
              <span key={tag} className="px-3 py-1 bg-gray-200 text-gray-800 rounded-full text-sm">
                {tag}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Data Quality */}
      {metadata && (
        <div className="bg-gray-100 p-4 rounded-lg text-xs text-gray-600">
          <p>Perfil {metadata.profile_completeness}% completo • Fuentes de datos: {metadata.data_sources} • Calidad: {metadata.data_quality}/100</p>
        </div>
      )}
    </div>
  );
};

export default Customer360Dashboard;
