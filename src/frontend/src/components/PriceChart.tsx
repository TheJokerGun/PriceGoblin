import React from "react";
import {
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
} from "recharts";
import { LuTrendingDown } from "react-icons/lu";
import { formatCurrency } from "../utils/formatters";

interface PriceChartProps {
  prices: { date: string; fullDate: string; price: number }[];
}

const PriceChart: React.FC<PriceChartProps> = ({ prices }) => {
  return (
    <div className="lg:col-span-2">
      <div className="dark:bg-gray-900/50 bg-white backdrop-blur-md border dark:border-gray-800 border-gray-200 rounded-[2.5rem] p-8 shadow-2xl h-full flex flex-col transition-colors duration-300">
        <div className="flex items-center justify-between mb-8">
          <h2 className="text-xl font-black dark:text-white text-gray-900">Price Volatility</h2>
          <div className="flex gap-2">
            <span className="px-3 py-1 dark:bg-gray-800 bg-gray-100 rounded-lg text-xs font-bold dark:text-gray-400 text-gray-500">Real-time Data</span>
          </div>
        </div>
        
        <div className="flex-1 min-h-[400px]">
          {prices.length > 1 ? (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={prices}>
                <defs>
                  <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" vertical={false} />
                <XAxis 
                  dataKey="date" 
                  stroke="var(--chart-text)" 
                  fontSize={10} 
                  fontWeight="bold"
                  tickLine={false} 
                  axisLine={false} 
                  dy={10}
                />
                <YAxis 
                  stroke="var(--chart-text)" 
                  fontSize={10} 
                  fontWeight="bold"
                  tickLine={false} 
                  axisLine={false} 
                  tickFormatter={(val) => formatCurrency(val)}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "var(--tooltip-bg)",
                    border: "1px solid var(--tooltip-border)",
                    borderRadius: "16px",
                    boxShadow: "0 10px 15px -3px rgba(0, 0, 0, 0.1)",
                  }}
                  itemStyle={{ color: "#3b82f6", fontWeight: 800 }}
                  labelStyle={{ color: "#9ca3af", marginBottom: "4px" }}
                  labelFormatter={(label, payload) => payload[0]?.payload?.fullDate || label}
                />
                <Area
                  type="monotone"
                  dataKey="price"
                  stroke="#3b82f6"
                  strokeWidth={4}
                  fillOpacity={1}
                  fill="url(#colorPrice)"
                />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-center space-y-4 opacity-40 grayscale">
              <div className="p-6 dark:bg-gray-800 bg-gray-100 rounded-full">
                <LuTrendingDown size={48} className="dark:text-white text-gray-900" />
              </div>
              <p className="max-w-xs font-medium dark:text-white text-gray-900">Accumulating more data points to generate your price trajectory chart.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PriceChart;
