'use client'

import { useState, useMemo } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
// import { Button } from '@/components/ui/button'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell
} from 'recharts'
import { Calculator, DollarSign, Clock, TrendingUp } from 'lucide-react'

interface ROICalculatorProps {
  patterns?: Array<{
    pattern_id: string
    pattern_type: string
    frequency: number
    automation_potential: number
    time_savings_potential_minutes: number
  }>
}

export function ROICalculatorChart({ patterns = [] }: ROICalculatorProps) {
  const [hourlyRate, setHourlyRate] = useState(50)
  const [implementationCost, setImplementationCost] = useState(5000)
  const [maintenanceCostPerMonth, setMaintenanceCostPerMonth] = useState(200)

  const calculations = useMemo(() => {
    const totalMonthlySavingsMinutes = patterns.reduce((sum, pattern) => 
      sum + (pattern.frequency * pattern.time_savings_potential_minutes * 4.33), 0) // 4.33 weeks per month

    const totalMonthlySavingsHours = totalMonthlySavingsMinutes / 60
    const monthlySavingsDollars = totalMonthlySavingsHours * hourlyRate
    const annualSavingsDollars = monthlySavingsDollars * 12
    
    const totalImplementationCost = implementationCost
    const annualMaintenanceCost = maintenanceCostPerMonth * 12
    const netAnnualSavings = annualSavingsDollars - annualMaintenanceCost
    const roiPercentage = totalImplementationCost > 0 ? 
      ((netAnnualSavings - totalImplementationCost) / totalImplementationCost) * 100 : 0
    const paybackMonths = netAnnualSavings > 0 ? 
      (totalImplementationCost / (netAnnualSavings / 12)) : 0

    return {
      totalMonthlySavingsMinutes,
      totalMonthlySavingsHours,
      monthlySavingsDollars,
      annualSavingsDollars,
      totalImplementationCost,
      annualMaintenanceCost,
      netAnnualSavings,
      roiPercentage,
      paybackMonths
    }
  }, [patterns, hourlyRate, implementationCost, maintenanceCostPerMonth])

  // Chart data for monthly savings projection
  const monthlyProjection = Array.from({ length: 12 }, (_, i) => ({
    month: `Month ${i + 1}`,
    savings: calculations.monthlySavingsDollars,
    cumulative: calculations.monthlySavingsDollars * (i + 1) - calculations.totalImplementationCost,
    costs: i === 0 ? calculations.totalImplementationCost + maintenanceCostPerMonth : maintenanceCostPerMonth
  }))

  // Pattern breakdown data
  const patternBreakdown = patterns.map(pattern => ({
    name: pattern.pattern_type,
    value: (pattern.frequency * pattern.time_savings_potential_minutes * 4.33 * hourlyRate) / 60,
    frequency: pattern.frequency,
    potential: pattern.automation_potential
  })).sort((a, b) => b.value - a.value).slice(0, 10)

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D', '#FFC0CB', '#FFB6C1', '#F0E68C', '#DDA0DD']

  return (
    <div className="space-y-6">
      {/* Calculator Inputs */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calculator className="h-5 w-5" />
            ROI Calculator Configuration
          </CardTitle>
          <CardDescription>
            Adjust parameters to calculate automation ROI
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            <div className="space-y-2">
              <Label htmlFor="hourlyRate">Hourly Rate ($)</Label>
              <Input
                id="hourlyRate"
                type="number"
                min="1"
                value={hourlyRate}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setHourlyRate(parseFloat(e.target.value) || 0)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="implementationCost">Implementation Cost ($)</Label>
              <Input
                id="implementationCost"
                type="number"
                min="0"
                value={implementationCost}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setImplementationCost(parseFloat(e.target.value) || 0)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="maintenanceCost">Monthly Maintenance ($)</Label>
              <Input
                id="maintenanceCost"
                type="number"
                min="0"
                value={maintenanceCostPerMonth}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setMaintenanceCostPerMonth(parseFloat(e.target.value) || 0)}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* ROI Summary Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Monthly Savings</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              ${calculations.monthlySavingsDollars.toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground">
              {calculations.totalMonthlySavingsHours.toFixed(1)} hours saved
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Annual ROI</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {calculations.roiPercentage.toFixed(1)}%
            </div>
            <p className="text-xs text-muted-foreground">
              Return on investment
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Payback Period</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {calculations.paybackMonths.toFixed(1)}
            </div>
            <p className="text-xs text-muted-foreground">
              months to break even
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Net Annual Savings</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              ${calculations.netAnnualSavings.toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground">
              After implementation costs
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Monthly Projection Chart */}
      <Card>
        <CardHeader>
          <CardTitle>12-Month Financial Projection</CardTitle>
          <CardDescription>
            Cumulative savings vs implementation costs over time
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={350}>
            <LineChart data={monthlyProjection}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis tickFormatter={(value) => `$${value.toLocaleString()}`} />
              <Tooltip 
                formatter={(value: number, name: string) => [
                  `$${value.toLocaleString()}`, 
                  name === 'cumulative' ? 'Cumulative Net' : 
                  name === 'savings' ? 'Monthly Savings' : 'Monthly Costs'
                ]} 
              />
              <Line 
                dataKey="cumulative" 
                stroke="#3b82f6" 
                strokeWidth={3}
                name="Cumulative Net"
              />
              <Line 
                dataKey="savings" 
                stroke="#10b981" 
                strokeWidth={2}
                name="Monthly Savings"
              />
              <Line 
                dataKey="costs" 
                stroke="#ef4444" 
                strokeWidth={2}
                name="Monthly Costs"
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Pattern Breakdown */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Savings by Pattern Type</CardTitle>
            <CardDescription>
              Top automation opportunities by financial impact
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={patternBreakdown}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="name" 
                  angle={-45}
                  textAnchor="end"
                  height={80}
                />
                <YAxis tickFormatter={(value) => `$${value.toLocaleString()}`} />
                <Tooltip 
                  formatter={(value: number) => [`$${value.toLocaleString()}`, 'Monthly Value']}
                />
                <Bar dataKey="value" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Value Distribution</CardTitle>
            <CardDescription>
              Proportion of savings by pattern type
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={patternBreakdown}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {patternBreakdown.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value: number) => [`$${value.toLocaleString()}`, 'Monthly Value']} />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>
    </div>
  )
} 