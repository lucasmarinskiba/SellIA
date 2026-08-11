'use client'

import { useEffect, useState } from 'react'
import { Zap, Play, Pause, CheckCircle, TrendingUp } from 'lucide-react'
import { Card } from '@/components/ui/Card'

interface Test {
  id: string
  name: string
  type: string
  status: string
  hypothesis: string
  started_at: string
}

interface TestResult {
  test_id: string
  test_name: string
  winning_variant: string
  uplift: string
  confidence: string
  recommendation: string
}

interface Portfolio {
  total_tests: number
  active_tests: number
  completed_tests: number
  avg_uplift: string
  total_impact: string
}

export default function TestingDashboard({ userId }: { userId: string }) {
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null)
  const [tests, setTests] = useState<Test[]>([])
  const [selectedTest, setSelectedTest] = useState<Test | null>(null)
  const [testResults, setTestResults] = useState<TestResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [newTest, setNewTest] = useState({
    name: '',
    type: 'messaging',
    hypothesis: '',
    variantA: '',
    variantB: '',
  })

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  useEffect(() => {
    fetchTestingData()
  }, [userId])

  const fetchTestingData = async () => {
    try {
      setLoading(true)
      const [portfolioRes, testsRes] = await Promise.all([
        fetch(`${apiUrl}/api/v1/testing/portfolio/${userId}`),
        fetch(`${apiUrl}/api/v1/testing/tests/${userId}`),
      ])

      if (portfolioRes.ok) {
        const data = await portfolioRes.json()
        setPortfolio(data.portfolio)
      }

      if (testsRes.ok) {
        const data = await testsRes.json()
        setTests(data.tests || [])
      }
    } catch (error) {
      console.error('Testing data fetch error:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSelectTest = async (test: Test) => {
    setSelectedTest(test)

    if (test.status === 'completed') {
      try {
        const res = await fetch(
          `${apiUrl}/api/v1/testing/results/${userId}/${test.id}`
        )
        if (res.ok) {
          const data = await res.json()
          setTestResults(data)
        }
      } catch (error) {
        console.error('Results fetch error:', error)
      }
    }
  }

  const handleCreateTest = async () => {
    if (!newTest.name || !newTest.hypothesis) return

    try {
      const res = await fetch(`${apiUrl}/api/v1/testing/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          test_name: newTest.name,
          test_type: newTest.type,
          hypothesis: newTest.hypothesis,
          variant_a_name: newTest.variantA || 'Control',
          variant_b_name: newTest.variantB || 'Variant B',
        }),
      })

      if (res.ok) {
        setNewTest({ name: '', type: 'messaging', hypothesis: '', variantA: '', variantB: '' })
        setShowCreateForm(false)
        fetchTestingData()
      }
    } catch (error) {
      console.error('Create test error:', error)
    }
  }

  const handleStartTest = async (testId: string) => {
    try {
      const res = await fetch(`${apiUrl}/api/v1/testing/${testId}/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, test_id: testId }),
      })

      if (res.ok) {
        fetchTestingData()
      }
    } catch (error) {
      console.error('Start test error:', error)
    }
  }

  const handleEndTest = async (testId: string) => {
    try {
      const res = await fetch(`${apiUrl}/api/v1/testing/${testId}/end`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, test_id: testId }),
      })

      if (res.ok) {
        fetchTestingData()
        if (selectedTest?.id === testId) {
          handleSelectTest(selectedTest)
        }
      }
    } catch (error) {
      console.error('End test error:', error)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-brand-night flex items-center gap-2">
            <Zap className="w-6 h-6" />
            A/B Testing
          </h2>
          <p className="text-sm text-slate-600 mt-1">Run experiments to optimize conversions</p>
        </div>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="px-4 py-2 bg-brand-orange text-white rounded-lg hover:bg-orange-600 text-sm font-medium"
        >
          + New Test
        </button>
      </div>

      {/* Create Form */}
      {showCreateForm && (
        <Card className="p-6 border-2 border-brand-orange">
          <h3 className="font-semibold text-brand-night mb-4">Create A/B Test</h3>
          <div className="space-y-3">
            <input
              type="text"
              value={newTest.name}
              onChange={(e) => setNewTest({ ...newTest, name: e.target.value })}
              placeholder="Test name"
              className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:border-brand-orange"
            />
            <textarea
              value={newTest.hypothesis}
              onChange={(e) => setNewTest({ ...newTest, hypothesis: e.target.value })}
              placeholder="Hypothesis (what do you expect to improve?)"
              className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:border-brand-orange"
              rows={2}
            />
            <select
              value={newTest.type}
              onChange={(e) => setNewTest({ ...newTest, type: e.target.value })}
              className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:border-brand-orange"
            >
              <option value="messaging">Messaging</option>
              <option value="pricing">Pricing</option>
              <option value="offer">Offer</option>
              <option value="timing">Timing</option>
              <option value="channel">Channel</option>
            </select>
            <div className="grid grid-cols-2 gap-2">
              <input
                type="text"
                value={newTest.variantA}
                onChange={(e) => setNewTest({ ...newTest, variantA: e.target.value })}
                placeholder="Control (A)"
                className="px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:border-brand-orange"
              />
              <input
                type="text"
                value={newTest.variantB}
                onChange={(e) => setNewTest({ ...newTest, variantB: e.target.value })}
                placeholder="Variant (B)"
                className="px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:border-brand-orange"
              />
            </div>
            <div className="flex gap-2">
              <button
                onClick={handleCreateTest}
                className="px-4 py-2 bg-brand-orange text-white rounded-lg hover:bg-orange-600 text-sm font-medium"
              >
                Create Test
              </button>
              <button
                onClick={() => setShowCreateForm(false)}
                className="px-4 py-2 bg-slate-200 text-slate-700 rounded-lg hover:bg-slate-300 text-sm font-medium"
              >
                Cancel
              </button>
            </div>
          </div>
        </Card>
      )}

      {/* Portfolio Stats */}
      {portfolio && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card className="p-4">
            <p className="text-xs text-slate-600">Total Tests</p>
            <p className="text-2xl font-bold text-brand-night">{portfolio.total_tests}</p>
          </Card>
          <Card className="p-4">
            <p className="text-xs text-slate-600">Active</p>
            <p className="text-2xl font-bold text-blue-600">{portfolio.active_tests}</p>
          </Card>
          <Card className="p-4">
            <p className="text-xs text-slate-600">Avg Uplift</p>
            <p className="text-2xl font-bold text-green-600">{portfolio.avg_uplift}</p>
          </Card>
          <Card className="p-4">
            <p className="text-xs text-slate-600">Monthly Impact</p>
            <p className="text-2xl font-bold text-orange-600">{portfolio.total_impact}</p>
          </Card>
        </div>
      )}

      {/* Tests List & Results */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Tests */}
        <Card className="p-4">
          <h3 className="font-semibold text-brand-night mb-4">Tests</h3>
          {loading ? (
            <div className="text-center py-8 text-slate-500">Loading...</div>
          ) : tests.length === 0 ? (
            <div className="text-center py-8 text-slate-500 text-sm">No tests yet</div>
          ) : (
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {tests.map((test) => (
                <button
                  key={test.id}
                  onClick={() => handleSelectTest(test)}
                  className={`w-full p-3 text-left rounded-lg transition-colors ${
                    selectedTest?.id === test.id
                      ? 'bg-orange-100 border border-brand-orange'
                      : 'bg-slate-100 hover:bg-slate-200'
                  }`}
                >
                  <p className="font-medium text-sm text-brand-night">{test.name}</p>
                  <p className="text-xs text-slate-600 mt-1">{test.type}</p>
                  <span
                    className={`inline-block mt-2 px-2 py-1 rounded text-xs font-medium ${
                      test.status === 'running'
                        ? 'bg-blue-100 text-blue-700'
                        : test.status === 'completed'
                          ? 'bg-green-100 text-green-700'
                          : 'bg-slate-100 text-slate-700'
                    }`}
                  >
                    {test.status}
                  </span>
                </button>
              ))}
            </div>
          )}
        </Card>

        {/* Test Details & Results */}
        {selectedTest && (
          <Card className="lg:col-span-2 p-6">
            <div className="mb-4">
              <h3 className="text-lg font-bold text-brand-night">{selectedTest.name}</h3>
              <p className="text-sm text-slate-600 mt-2">{selectedTest.hypothesis}</p>
            </div>

            {/* Actions */}
            {selectedTest.status === 'draft' && (
              <button
                onClick={() => handleStartTest(selectedTest.id)}
                className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium flex items-center justify-center gap-2 mb-4"
              >
                <Play className="w-4 h-4" />
                Start Test
              </button>
            )}

            {selectedTest.status === 'running' && (
              <button
                onClick={() => handleEndTest(selectedTest.id)}
                className="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm font-medium flex items-center justify-center gap-2 mb-4"
              >
                <CheckCircle className="w-4 h-4" />
                End Test & Analyze
              </button>
            )}

            {/* Results */}
            {testResults && (
              <div className="space-y-3 p-4 bg-green-50 rounded-lg border border-green-200">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-semibold text-brand-night">Winner: {testResults.winning_variant}</p>
                    <p className="text-sm text-slate-600 mt-1">{testResults.recommendation}</p>
                  </div>
                  <TrendingUp className="w-5 h-5 text-green-600" />
                </div>

                <div className="grid grid-cols-3 gap-2 text-xs">
                  <div className="bg-white p-2 rounded">
                    <p className="text-slate-600">Uplift</p>
                    <p className="font-bold text-green-600">{testResults.uplift}</p>
                  </div>
                  <div className="bg-white p-2 rounded">
                    <p className="text-slate-600">Confidence</p>
                    <p className="font-bold text-blue-600">{testResults.confidence}</p>
                  </div>
                  <div className="bg-white p-2 rounded">
                    <p className="text-slate-600">Impact</p>
                    <p className="font-bold text-orange-600">{testResults.revenue_impact}</p>
                  </div>
                </div>
              </div>
            )}

            {selectedTest.status === 'draft' && (
              <div className="mt-4 p-4 bg-slate-50 rounded-lg text-sm text-slate-600">
                <p>Ready to start experiment. Click "Start Test" to begin collecting data.</p>
              </div>
            )}

            {selectedTest.status === 'running' && !testResults && (
              <div className="mt-4 p-4 bg-blue-50 rounded-lg text-sm text-blue-700">
                <p>Test running. Click "End Test & Analyze" when ready to see results.</p>
              </div>
            )}
          </Card>
        )}
      </div>
    </div>
  )
}
