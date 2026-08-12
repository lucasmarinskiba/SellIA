import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from 'recharts';

interface TestResult {
  test_name: string;
  element_type: string;
  variants: number;
  conversions: number;
  conversion_rates: Record<string, number>;
  statistical_significance: Record<string, number>;
  winner?: string;
  winner_rate?: number;
}

interface ABTestData {
  active_tests: TestResult[];
}

const ABTestDashboard: React.FC = () => {
  const [tests, setTests] = useState<TestResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTest, setSelectedTest] = useState<TestResult | null>(null);

  useEffect(() => {
    const fetchTests = async () => {
      try {
        const response = await fetch('/api/v1/monetization/ab-tests');
        const data = await response.json();

        const mockTests: TestResult[] = [
          {
            test_name: 'urgency_v1',
            element_type: 'urgency',
            variants: 3,
            conversions: 1250,
            conversion_rates: {
              'variant_a': 0.28,
              'variant_b': 0.35,
              'variant_c': 0.32,
            },
            statistical_significance: {
              'variant_a': 0.5,
              'variant_b': 0.02,
              'variant_c': 0.15,
            },
            winner: 'variant_b',
            winner_rate: 0.35,
          },
          {
            test_name: 'offer_discount_v1',
            element_type: 'offer',
            variants: 3,
            conversions: 980,
            conversion_rates: {
              'variant_a': 0.20,
              'variant_b': 0.32,
              'variant_c': 0.18,
            },
            statistical_significance: {
              'variant_a': 0.3,
              'variant_b': 0.01,
              'variant_c': 0.4,
            },
            winner: 'variant_b',
            winner_rate: 0.32,
          },
          {
            test_name: 'cta_text_v1',
            element_type: 'cta',
            variants: 5,
            conversions: 1120,
            conversion_rates: {
              'variant_a': 0.22,
              'variant_b': 0.25,
              'variant_c': 0.28,
              'variant_d': 0.30,
              'variant_e': 0.24,
            },
            statistical_significance: {
              'variant_a': 0.2,
              'variant_b': 0.15,
              'variant_c': 0.08,
              'variant_d': 0.03,
              'variant_e': 0.25,
            },
            winner: 'variant_d',
            winner_rate: 0.30,
          },
        ];

        setTests(mockTests);
        if (mockTests.length > 0) {
          setSelectedTest(mockTests[0]);
        }
      } catch (error) {
        console.error('Failed to fetch tests:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchTests();
  }, []);

  if (loading) return <div className="p-8">Loading A/B tests...</div>;

  const chartData = selectedTest
    ? Object.entries(selectedTest.conversion_rates).map(([variant, rate]) => ({
        variant,
        conversion_rate: rate * 100,
        significance: selectedTest.statistical_significance[variant],
        is_winner: variant === selectedTest.winner,
      }))
    : [];

  return (
    <div className="p-8 bg-gradient-to-br from-gray-50 to-gray-100">
      <h1 className="text-3xl font-bold mb-8 text-gray-900">A/B Test Dashboard</h1>

      <div className="grid grid-cols-3 gap-6 mb-8">
        {/* Test List */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Active Tests ({tests.length})</h2>
          <div className="space-y-3">
            {tests.map((test, idx) => (
              <div
                key={idx}
                onClick={() => setSelectedTest(test)}
                className={`p-4 rounded cursor-pointer transition ${
                  selectedTest?.test_name === test.test_name
                    ? 'bg-blue-100 border-2 border-blue-500'
                    : 'bg-gray-50 border-2 border-gray-200 hover:bg-gray-100'
                }`}
              >
                <p className="font-semibold text-gray-900">{test.test_name}</p>
                <p className="text-sm text-gray-600">{test.element_type} • {test.variants} variants</p>
                {test.winner && (
                  <p className="text-xs text-green-600 font-semibold mt-2">
                    ✓ Winner: {test.winner} ({(test.winner_rate! * 100).toFixed(1)}%)
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Test Details */}
        {selectedTest && (
          <div className="col-span-2 bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">{selectedTest.test_name}</h2>
            <div className="grid grid-cols-2 gap-4 mb-6">
              <div>
                <p className="text-gray-600 text-sm">Element Type</p>
                <p className="text-lg font-bold text-gray-900">{selectedTest.element_type}</p>
              </div>
              <div>
                <p className="text-gray-600 text-sm">Total Variants</p>
                <p className="text-lg font-bold text-gray-900">{selectedTest.variants}</p>
              </div>
              <div>
                <p className="text-gray-600 text-sm">Total Conversions</p>
                <p className="text-lg font-bold text-green-600">{selectedTest.conversions.toLocaleString()}</p>
              </div>
              <div>
                <p className="text-gray-600 text-sm">Winner</p>
                <p className="text-lg font-bold text-blue-600">{selectedTest.winner || 'TBD'}</p>
              </div>
            </div>

            <h3 className="text-sm font-semibold text-gray-700 mb-3">Conversion Rates by Variant</h3>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="variant" />
                <YAxis label={{ value: 'Conversion %', angle: -90, position: 'insideLeft' }} />
                <Tooltip formatter={(value) => `${(value as number).toFixed(2)}%`} />
                <Bar dataKey="conversion_rate" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Variant Details Table */}
      {selectedTest && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Variant Results</h2>
          <table className="w-full">
            <thead>
              <tr className="border-b">
                <th className="text-left py-2 px-4 text-gray-700 font-semibold">Variant</th>
                <th className="text-center py-2 px-4 text-gray-700 font-semibold">Conversion Rate</th>
                <th className="text-center py-2 px-4 text-gray-700 font-semibold">P-Value (Significance)</th>
                <th className="text-center py-2 px-4 text-gray-700 font-semibold">Status</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(selectedTest.conversion_rates).map(([variant, rate], idx) => {
                const pValue = selectedTest.statistical_significance[variant];
                const isSignificant = pValue < 0.05;
                const isWinner = variant === selectedTest.winner;

                return (
                  <tr key={idx} className={`border-b ${isWinner ? 'bg-green-50' : ''} hover:bg-gray-50`}>
                    <td className="py-3 px-4 text-gray-900 font-medium">{variant}</td>
                    <td className="text-center py-3 px-4 text-gray-700 font-semibold">{(rate * 100).toFixed(2)}%</td>
                    <td className="text-center py-3 px-4">
                      <span className={`inline-block px-3 py-1 rounded text-sm font-semibold ${
                        isSignificant ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                      }`}>
                        {pValue < 0.01 ? 'p < 0.01' : `p = ${pValue.toFixed(2)}`}
                      </span>
                    </td>
                    <td className="text-center py-3 px-4">
                      {isWinner && <span className="inline-block px-3 py-1 rounded bg-green-100 text-green-800 text-sm font-semibold">✓ Winner</span>}
                      {!isWinner && isSignificant && <span className="text-gray-500 text-sm">Significant</span>}
                      {!isSignificant && <span className="text-gray-400 text-sm">Not significant</span>}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default ABTestDashboard;
