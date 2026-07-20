import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/Tabs';
import { Button } from '@/components/ui/Button';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export default function Dashboard() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const response = await fetch('/api/v1/analytics/overview?days=30');
      const result = await response.json();
      setData(result);
    } catch (error) {
      console.error('Error fetching dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="p-8">Cargando...</div>;
  }

  const kpis = data?.kpis || {};

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">🤖 SellIA Dashboard</h1>
          <p className="text-slate-400">Vendedor autónomo 24/7</p>
        </div>

        {/* KPIs */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <KPICard label="Total Revenue" value={`$${kpis.total_revenue?.toLocaleString()}`} icon="💰" />
          <KPICard label="Total Orders" value={kpis.total_orders} icon="📦" />
          <KPICard label="Conversion Rate" value={`${(kpis.conversion_rate * 100).toFixed(1)}%`} icon="📈" />
          <KPICard label="CAC" value={`$${kpis.customer_acquisition_cost?.toFixed(2)}`} icon="💸" />
        </div>

        {/* Tabs */}
        <Tabs defaultValue="analytics" className="w-full">
          <TabsList className="grid w-full grid-cols-5 bg-slate-800">
            <TabsTrigger value="analytics">Analytics</TabsTrigger>
            <TabsTrigger value="travel">Travel Mode</TabsTrigger>
            <TabsTrigger value="platforms">Platforms</TabsTrigger>
            <TabsTrigger value="pricing">Pricing</TabsTrigger>
            <TabsTrigger value="status">Status</TabsTrigger>
          </TabsList>

          {/* Analytics Tab */}
          <TabsContent value="analytics" className="space-y-4">
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">Revenue Trend</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={getRevenueData()}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
                    <XAxis dataKey="day" stroke="#94a3b8" />
                    <YAxis stroke="#94a3b8" />
                    <Tooltip contentStyle={{ backgroundColor: '#1e293b' }} />
                    <Legend />
                    <Line type="monotone" dataKey="revenue" stroke="#3b82f6" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <MetricCard title="Avg Order Value" value={`$${kpis.avg_order_value?.toFixed(2)}`} />
              <MetricCard title="LTV" value={`$${kpis.lifetime_value?.toFixed(2)}`} />
              <MetricCard title="ROI" value={`${kpis.roi?.toFixed(1)}x`} />
              <MetricCard title="Repeat Rate" value={`${(kpis.repeat_customer_rate * 100).toFixed(1)}%`} />
            </div>
          </TabsContent>

          {/* Travel Mode Tab */}
          <TabsContent value="travel" className="space-y-4">
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">✈️ Travel Mode</CardTitle>
                <CardDescription>Configure travel dates. Sistema sigue vendiendo automático.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm text-slate-300">Start Date</label>
                    <input type="date" className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white" />
                  </div>
                  <div>
                    <label className="text-sm text-slate-300">End Date</label>
                    <input type="date" className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white" />
                  </div>
                </div>
                <div>
                  <label className="text-sm text-slate-300">Notes (Optional)</label>
                  <textarea className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white" rows={3} placeholder="Ej: Vacaciones a Cancún" />
                </div>
                <Button className="w-full bg-blue-600 hover:bg-blue-700">Activar Travel Mode</Button>
                <div className="bg-slate-700 p-4 rounded mt-4">
                  <p className="text-sm text-slate-300">
                    ✓ Google Calendar bloqueado (no agendar reuniones)<br/>
                    ✓ WhatsApp auto-responde ("estoy de viaje")<br/>
                    ✓ Órdenes siguen procesándose<br/>
                    ✓ Leads guardados para cuando vuelves
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Platforms Tab */}
          <TabsContent value="platforms" className="space-y-4">
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">Platform Intelligence</CardTitle>
                <CardDescription>Analyze platforms for your products.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <input type="text" placeholder="Product name..." className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white" />
                <input type="number" placeholder="Price ($)..." className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white" />
                <select className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white">
                  <option>Physical</option>
                  <option>Digital</option>
                </select>
                <Button className="w-full bg-green-600 hover:bg-green-700">Analizar</Button>
              </CardContent>
            </Card>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <PlatformCard platform="Mercado Libre" score={85} commission={10} />
              <PlatformCard platform="Amazon" score={80} commission={15} />
              <PlatformCard platform="Shopify" score={75} commission={2.9} />
            </div>
          </TabsContent>

          {/* Pricing Tab */}
          <TabsContent value="pricing" className="space-y-4">
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">Dynamic Pricing Optimizer</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm text-slate-300">Base Price</label>
                    <input type="number" placeholder="$50" className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white" />
                  </div>
                  <div>
                    <label className="text-sm text-slate-300">Platform</label>
                    <select className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white">
                      <option>Mercado Libre</option>
                      <option>Amazon</option>
                      <option>Shopify</option>
                    </select>
                  </div>
                </div>
                <Button className="w-full bg-purple-600 hover:bg-purple-700">Optimizar Precio</Button>
              </CardContent>
            </Card>

            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white text-2xl">Optimal Price: $55.28</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 text-sm text-slate-300">
                  <p>Base Price: $50.00</p>
                  <p>Commission (10%): +$5.55</p>
                  <p>Competitor Adjustment: -$2.77 (undercut 5%)</p>
                  <p>Inventory Adjustment: -$5.00 (high stock)</p>
                  <p>Expected Margin: +12%</p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Status Tab */}
          <TabsContent value="status" className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <StatusCard title="Mercado Libre" status="✓ Connected" icon="🟢" />
              <StatusCard title="Stripe" status="✓ Active" icon="🟢" />
              <StatusCard title="WhatsApp" status="✓ API Mode" icon="🟢" />
              <StatusCard title="Google Calendar" status="✓ Synced" icon="🟢" />
              <StatusCard title="DHL Shipping" status="✓ Ready" icon="🟢" />
              <StatusCard title="FeedIA" status="✓ Connected" icon="🟢" />
            </div>

            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">System Health</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div>
                    <div className="flex justify-between mb-1">
                      <span className="text-sm text-slate-300">API Health</span>
                      <span className="text-sm text-green-400">99.8%</span>
                    </div>
                    <div className="w-full bg-slate-700 rounded h-2">
                      <div className="bg-green-500 h-2 rounded" style={{ width: '99.8%' }} />
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between mb-1">
                      <span className="text-sm text-slate-300">Database</span>
                      <span className="text-sm text-green-400">Healthy</span>
                    </div>
                    <div className="w-full bg-slate-700 rounded h-2">
                      <div className="bg-green-500 h-2 rounded w-full" />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

function KPICard({ label, value, icon }: any) {
  return (
    <Card className="bg-slate-800 border-slate-700">
      <CardContent className="pt-6">
        <div className="flex justify-between items-start">
          <div>
            <p className="text-slate-400 text-sm">{label}</p>
            <p className="text-2xl font-bold text-white mt-2">{value}</p>
          </div>
          <span className="text-3xl">{icon}</span>
        </div>
      </CardContent>
    </Card>
  );
}

function MetricCard({ title, value }: any) {
  return (
    <Card className="bg-slate-800 border-slate-700">
      <CardContent className="pt-6">
        <p className="text-slate-400 text-sm">{title}</p>
        <p className="text-2xl font-bold text-white mt-2">{value}</p>
      </CardContent>
    </Card>
  );
}

function PlatformCard({ platform, score, commission }: any) {
  return (
    <Card className="bg-slate-800 border-slate-700">
      <CardContent className="pt-6">
        <h3 className="font-bold text-white mb-2">{platform}</h3>
        <div className="space-y-1 text-sm text-slate-300">
          <p>Score: <span className="text-green-400">{score}</span>/100</p>
          <p>Commission: <span className="text-blue-400">{commission}%</span></p>
        </div>
      </CardContent>
    </Card>
  );
}

function StatusCard({ title, status, icon }: any) {
  return (
    <Card className="bg-slate-800 border-slate-700">
      <CardContent className="pt-6">
        <div className="flex justify-between items-start">
          <div>
            <p className="text-slate-400 text-sm">{title}</p>
            <p className="text-white font-semibold mt-2">{status}</p>
          </div>
          <span className="text-2xl">{icon}</span>
        </div>
      </CardContent>
    </Card>
  );
}

function getRevenueData() {
  return [
    { day: '1', revenue: 1200 },
    { day: '2', revenue: 1500 },
    { day: '3', revenue: 1800 },
    { day: '4', revenue: 2100 },
    { day: '5', revenue: 2400 },
    { day: '6', revenue: 2200 },
    { day: '7', revenue: 2800 },
  ];
}
