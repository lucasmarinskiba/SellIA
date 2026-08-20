import React, { useState } from 'react';
import Dashboard from './components/Dashboard';
import SalesFunnel from './components/SalesFunnel';
import Customer360 from './components/Customer360';
import AutomationBuilder from './components/AutomationBuilder';
import Analytics from './components/Analytics';

type ViewType = 'dashboard' | 'funnel' | 'customer' | 'automation' | 'analytics';

function App() {
  const [currentView, setCurrentView] = useState<ViewType>('dashboard');
  const [notifications] = useState(3);

  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: '📊' },
    { id: 'funnel', label: 'Sales Pipeline', icon: '🔄' },
    { id: 'customer', label: 'Customer 360', icon: '👥' },
    { id: 'automation', label: 'Automations', icon: '🤖' },
    { id: 'analytics', label: 'Analytics', icon: '📈' },
  ];

  const renderView = () => {
    switch (currentView) {
      case 'dashboard':
        return <Dashboard />;
      case 'funnel':
        return <SalesFunnel />;
      case 'customer':
        return <Customer360 />;
      case 'automation':
        return <AutomationBuilder />;
      case 'analytics':
        return <Analytics />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <div className="flex h-screen bg-slate-900">
      {/* Sidebar */}
      <div className="w-64 bg-gradient-to-b from-slate-900 to-slate-800 border-r border-slate-700 flex flex-col">
        {/* Logo */}
        <div className="p-6 border-b border-slate-700">
          <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-600">
            SellIA
          </h1>
          <p className="text-slate-400 text-sm mt-1">AI Sales Platform</p>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-2">
          {menuItems.map(item => (
            <button
              key={item.id}
              onClick={() => setCurrentView(item.id as ViewType)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition ${
                currentView === item.id
                  ? 'bg-blue-600 text-white shadow-lg'
                  : 'text-slate-300 hover:bg-slate-700'
              }`}
            >
              <span className="text-xl">{item.icon}</span>
              <span className="font-semibold">{item.label}</span>
            </button>
          ))}
        </nav>

        {/* Bottom Section */}
        <div className="p-4 border-t border-slate-700 space-y-3">
          <button className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-slate-300 hover:bg-slate-700 transition">
            <span className="text-xl">⚙️</span>
            <span className="font-semibold">Settings</span>
          </button>
          <button className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-slate-300 hover:bg-slate-700 transition">
            <span className="text-xl">👤</span>
            <span className="font-semibold">Profile</span>
          </button>
          <button className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-slate-300 hover:bg-slate-700 transition">
            <span className="text-xl">🚪</span>
            <span className="font-semibold">Logout</span>
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Top Bar */}
        <div className="bg-slate-800 border-b border-slate-700 px-8 py-4 flex items-center justify-between">
          <div className="flex-1">
            <input
              type="text"
              placeholder="Search customers, deals, or automations..."
              className="w-64 px-4 py-2 bg-slate-700 text-white rounded-lg placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="flex items-center gap-6">
            {/* Notifications */}
            <div className="relative cursor-pointer">
              <span className="text-2xl hover:opacity-80 transition">🔔</span>
              {notifications > 0 && (
                <div className="absolute -top-2 -right-2 bg-red-500 text-white text-xs rounded-full w-6 h-6 flex items-center justify-center font-bold">
                  {notifications}
                </div>
              )}
            </div>

            {/* Help */}
            <div className="cursor-pointer text-2xl hover:opacity-80 transition">
              ❓
            </div>

            {/* User Menu */}
            <div className="flex items-center gap-3 pl-6 border-l border-slate-600">
              <div className="text-right">
                <p className="text-white font-semibold text-sm">John Doe</p>
                <p className="text-slate-400 text-xs">Premium Plan</p>
              </div>
              <div className="w-10 h-10 bg-gradient-to-br from-blue-400 to-purple-600 rounded-full flex items-center justify-center text-white font-bold">
                JD
              </div>
            </div>
          </div>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-auto">
          {renderView()}
        </div>
      </div>

      {/* AI Assistant Float */}
      <div className="fixed bottom-8 right-8">
        <button className="w-16 h-16 bg-gradient-to-br from-blue-600 to-purple-600 rounded-full shadow-lg hover:shadow-xl transition flex items-center justify-center text-2xl hover:scale-110">
          🤖
        </button>
      </div>
    </div>
  );
}

export default App;
