import {
  LineChart as RechartsLineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'

const LINE_COLORS = ['#2563eb', '#dc2626', '#16a34a', '#d97706', '#7c3aed']

interface LineChartProps {
  data: Record<string, unknown>[]
  xKey: string
  yKeys: string[]
  title?: string
  height?: number
}

export const LineChart = ({ data, xKey, yKeys, title, height = 300 }: LineChartProps) => (
  <div className="w-full">
    {title && <h3 className="text-sm font-medium text-gray-700 mb-2">{title}</h3>}
    <ResponsiveContainer width="100%" height={height}>
      <RechartsLineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey={xKey} />
        <YAxis />
        <Tooltip />
        <Legend />
        {yKeys.map((key, i) => (
          <Line
            key={key}
            type="monotone"
            dataKey={key}
            stroke={LINE_COLORS[i % LINE_COLORS.length]}
            strokeWidth={2}
          />
        ))}
      </RechartsLineChart>
    </ResponsiveContainer>
  </div>
)

export default LineChart
