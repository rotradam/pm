"use client"

import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { fetchAssetDetails, fetchAssetHistory, fetchAssetSources } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { ArrowLeft, TrendingUp, TrendingDown, Layers } from "lucide-react"
import Link from "next/link"
import { useParams } from "next/navigation"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import {
    ResponsiveContainer,
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
} from "recharts"

export default function AssetPage() {
    const params = useParams()
    const ticker = params.ticker as string
    const [selectedSource, setSelectedSource] = useState<string | undefined>(undefined)

    const { data: asset, isLoading: isAssetLoading } = useQuery({
        queryKey: ['asset', ticker],
        queryFn: () => fetchAssetDetails(ticker)
    })

    const { data: sources } = useQuery({
        queryKey: ['sources', ticker],
        queryFn: () => fetchAssetSources(ticker)
    })

    const { data: history, isLoading: isHistoryLoading } = useQuery({
        queryKey: ['history', ticker, selectedSource],
        queryFn: () => fetchAssetHistory(ticker, "1y", selectedSource)
    })

    if (isAssetLoading || isHistoryLoading) {
        return (
            <div className="flex min-h-screen items-center justify-center bg-[#08090A] text-white">
                <div className="animate-pulse text-muted-foreground text-sm">Loading asset data...</div>
            </div>
        )
    }

    if (!asset) {
        return (
            <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-[#08090A] text-white">
                <h1 className="text-xl font-medium">Asset Not Found</h1>
                <Link href="/dashboard">
                    <Button variant="outline" className="border-white/10 hover:bg-white/5">Back to Dashboard</Button>
                </Link>
            </div>
        )
    }

    // Calculate simple change
    const lastPrice = history && history.length > 0 ? history[history.length - 1].close : 0
    const prevPrice = history && history.length > 1 ? history[history.length - 2].close : 0
    const change = lastPrice - prevPrice
    const changePercent = prevPrice ? (change / prevPrice) * 100 : 0
    const isPositive = change >= 0

    return (
        <div className="min-h-screen bg-[#08090A] text-foreground">
            {/* Header */}
            <header className="border-b border-white/5 bg-[#08090A]/80 backdrop-blur-md sticky top-0 z-10">
                <div className="container flex h-14 items-center justify-between">
                    <div className="flex items-center gap-4">
                        <Link href="/dashboard">
                            <Button variant="ghost" size="sm" className="h-8 w-8 p-0 hover:bg-white/5 rounded-full">
                                <ArrowLeft className="h-4 w-4 text-muted-foreground" />
                            </Button>
                        </Link>
                        <div className="h-6 w-[1px] bg-white/10"></div>
                        <span className="font-mono text-sm font-medium text-white">{asset.ticker}</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <div className="h-6 w-6 rounded-full bg-gradient-to-tr from-purple-500 to-blue-500"></div>
                    </div>
                </div>
            </header>

            <main className="container py-8 max-w-5xl">
                <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-6 mb-12">
                    <div>
                        <div className="flex items-center gap-3 mb-2">
                            <h1 className="text-3xl font-medium tracking-tight text-white">{asset.name}</h1>
                            <span className="inline-flex items-center rounded-md border border-white/10 bg-white/5 px-2 py-0.5 text-xs font-medium text-muted-foreground">
                                {asset.category}
                            </span>
                        </div>
                        <div className="flex gap-4 text-sm text-muted-foreground">
                            <span>{asset.exchange || 'Exchange N/A'}</span>
                            <span>•</span>
                            <span>{asset.region || 'Global'}</span>
                            <span>•</span>
                            <span>{asset.currency || 'USD'}</span>
                        </div>
                    </div>

                    <div className="text-right">
                        <div className="text-4xl font-medium tracking-tight text-white">
                            ${lastPrice.toFixed(2)}
                        </div>
                        <div className={`flex items-center justify-end text-sm font-medium mt-1 ${isPositive ? 'text-green-500' : 'text-red-500'}`}>
                            {isPositive ? <TrendingUp className="mr-1 h-3 w-3" /> : <TrendingDown className="mr-1 h-3 w-3" />}
                            {change > 0 ? '+' : ''}{change.toFixed(2)} ({changePercent.toFixed(2)}%)
                            <span className="text-muted-foreground ml-2 font-normal">Today</span>
                        </div>
                    </div>
                </div>

                {/* Chart Section */}
                <div className="rounded-xl border border-white/5 bg-white/[0.02] p-6 mb-8">
                    <div className="flex items-center justify-between mb-6">
                        <h3 className="text-sm font-medium text-muted-foreground">Price History (1Y)</h3>
                        <div className="flex items-center gap-2">
                            <Select value={selectedSource} onValueChange={setSelectedSource}>
                                <SelectTrigger className="w-[140px] h-8 text-xs bg-white/5 border-white/10">
                                    <SelectValue placeholder="Select Source" />
                                </SelectTrigger>
                                <SelectContent className="bg-[#0F1011] border-white/10 text-white">
                                    {sources?.map(s => (
                                        <SelectItem key={s.id} value={s.id} className="text-xs focus:bg-white/10 focus:text-white cursor-pointer">
                                            {s.name}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>
                    </div>
                    <div className="h-[400px] w-full">
                        {history && history.length > 0 ? (
                            <ResponsiveContainer width="100%" height="100%">
                                <AreaChart data={history}>
                                    <defs>
                                        <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor={isPositive ? "#22c55e" : "#ef4444"} stopOpacity={0.2} />
                                            <stop offset="95%" stopColor={isPositive ? "#22c55e" : "#ef4444"} stopOpacity={0} />
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.05)" />
                                    <XAxis
                                        dataKey="date"
                                        tick={{ fontSize: 11, fill: '#525252' }}
                                        axisLine={false}
                                        tickLine={false}
                                        tickFormatter={(val) => {
                                            const d = new Date(val);
                                            return `${d.getMonth() + 1}/${d.getDate()}`
                                        }}
                                        minTickGap={40}
                                        dy={10}
                                    />
                                    <YAxis
                                        domain={['auto', 'auto']}
                                        tick={{ fontSize: 11, fill: '#525252' }}
                                        axisLine={false}
                                        tickLine={false}
                                        tickFormatter={(val) => `$${val.toFixed(0)}`}
                                        dx={-10}
                                    />
                                    <Tooltip
                                        contentStyle={{
                                            backgroundColor: '#08090A',
                                            borderColor: 'rgba(255,255,255,0.1)',
                                            borderRadius: '8px',
                                            color: '#fff',
                                            boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.5)'
                                        }}
                                        itemStyle={{ color: '#fff' }}
                                        formatter={(value: number) => [`$${value.toFixed(2)}`, 'Price']}
                                        labelFormatter={(label) => new Date(label).toLocaleDateString()}
                                    />
                                    <Area
                                        type="monotone"
                                        dataKey="close"
                                        stroke={isPositive ? "#22c55e" : "#ef4444"}
                                        fillOpacity={1}
                                        fill="url(#colorPrice)"
                                        strokeWidth={2}
                                    />
                                </AreaChart>
                            </ResponsiveContainer>
                        ) : (
                            <div className="flex h-full items-center justify-center text-muted-foreground text-sm">
                                No price data available
                            </div>
                        )}
                    </div>
                </div>

                {/* Stats Grid */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="p-4 rounded-lg border border-white/5 bg-white/[0.02]">
                        <div className="text-xs text-muted-foreground mb-1">Market Cap</div>
                        <div className="text-lg font-medium text-white">-</div>
                    </div>
                    <div className="p-4 rounded-lg border border-white/5 bg-white/[0.02]">
                        <div className="text-xs text-muted-foreground mb-1">Volume (24h)</div>
                        <div className="text-lg font-medium text-white">
                            {history && history.length > 0 ? `$${(history[history.length - 1].volume / 1000000).toFixed(2)}M` : '-'}
                        </div>
                    </div>
                    <div className="p-4 rounded-lg border border-white/5 bg-white/[0.02]">
                        <div className="text-xs text-muted-foreground mb-1">Subcategory</div>
                        <div className="text-lg font-medium text-white">{asset.subcategory || '-'}</div>
                    </div>
                </div>
            </main>
        </div>
    )
}
