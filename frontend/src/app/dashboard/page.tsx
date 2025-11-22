"use client"


import { useRouter } from "next/navigation"
import { useQuery, keepPreviousData } from "@tanstack/react-query"
import { fetchAssets, Asset } from "@/lib/api"
import { createClient } from "@/lib/supabase/client"
import { useEffect, useState } from "react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Search, Filter, ChevronLeft, ChevronRight, Layers, ArrowUpRight, ArrowUpDown, Check } from "lucide-react"
import Link from "next/link"
import { cn } from "@/lib/utils"

import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from "@/components/ui/dialog"
import { Checkbox } from "@/components/ui/checkbox"
import { Separator } from "@/components/ui/separator"
import { SettingsModal } from "@/components/settings-modal"

// Simple Sparkline Component
function Sparkline({ data, color = "#10b981" }: { data: number[], color?: string }) {
    if (!data || data.length < 2) return null

    const min = Math.min(...data)
    const max = Math.max(...data)
    const range = max - min || 1
    const width = 60
    const height = 20

    const points = data.map((d, i) => {
        const x = (i / (data.length - 1)) * width
        const y = height - ((d - min) / range) * height
        return `${x},${y}`
    }).join(" ")

    return (
        <svg width={width} height={height} className="overflow-visible">
            <polyline
                points={points}
                fill="none"
                stroke={color}
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
            />
        </svg>
    )
}

const CATEGORY_COLORS: Record<string, string> = {
    "Crypto": "bg-orange-500/10 text-orange-500 border-orange-500/20",
    "Stock": "bg-blue-500/10 text-blue-500 border-blue-500/20",
    "ETF": "bg-purple-500/10 text-purple-500 border-purple-500/20",
    "Bond": "bg-emerald-500/10 text-emerald-500 border-emerald-500/20",
    "Commodity": "bg-yellow-500/10 text-yellow-500 border-yellow-500/20",
}

export default function Dashboard() {
    const router = useRouter()
    const [search, setSearch] = useState("")
    const [page, setPage] = useState(0)
    const [category, setCategory] = useState("All")
    const [userProfile, setUserProfile] = useState<any>(null)

    useEffect(() => {
        const getUser = async () => {
            const supabase = createClient()
            const { data: { user } } = await supabase.auth.getUser()
            if (user) {
                const { data: profile } = await supabase
                    .from('profiles')
                    .select('*')
                    .eq('id', user.id)
                    .single()
                setUserProfile(profile)
            }
        }
        getUser()
    }, [])

    // Advanced Filters State
    const [selectedRegions, setSelectedRegions] = useState<string[]>([])
    const [selectedExchanges, setSelectedExchanges] = useState<string[]>([])
    const [isFilterOpen, setIsFilterOpen] = useState(false)

    const [sortBy, setSortBy] = useState<string | undefined>(undefined)
    const [sortOrder, setSortOrder] = useState<"asc" | "desc">("asc")

    const limit = 20

    // Derived filters for API
    const regionFilter = selectedRegions.length > 0 ? selectedRegions[0] : undefined // API currently supports single region, need to update API for multi or just pick first for now
    const exchangeFilter = selectedExchanges.length > 0 ? selectedExchanges[0] : undefined

    const { data: assets, isLoading, isError, refetch } = useQuery<Asset[]>({
        queryKey: ['assets', search, category, regionFilter, exchangeFilter, sortBy, sortOrder, page],
        queryFn: () => fetchAssets(
            search,
            category === "All" ? undefined : category,
            limit,
            page * limit,
            regionFilter,
            exchangeFilter,
            sortBy,
            sortOrder
        ),
        placeholderData: keepPreviousData
    })

    const handleSort = (column: string) => {
        if (sortBy === column) {
            setSortOrder(sortOrder === "asc" ? "desc" : "asc")
        } else {
            setSortBy(column)
            setSortOrder("asc")
        }
    }

    const clearFilters = () => {
        setCategory("All")
        setSelectedRegions([])
        setSelectedExchanges([])
        setSearch("")
        setPage(0)
        setIsFilterOpen(false)
    }

    const toggleRegion = (region: string) => {
        setSelectedRegions(prev =>
            prev.includes(region) ? prev.filter(r => r !== region) : [...prev, region]
        )
    }

    const toggleExchange = (exch: string) => {
        setSelectedExchanges(prev =>
            prev.includes(exch) ? prev.filter(e => e !== exch) : [...prev, exch]
        )
    }

    return (
        <div className="flex min-h-screen flex-col bg-[#08090A] text-foreground">
            <header className="border-b border-white/5 bg-[#08090A]/80 backdrop-blur-md sticky top-0 z-10">
                <div className="container flex h-14 items-center justify-between">
                    <Link href="/" className="flex items-center gap-2 font-medium text-sm">
                        <div className="h-6 w-6 rounded-md bg-white/10 flex items-center justify-center">
                            <Layers className="h-3.5 w-3.5 text-white" />
                        </div>
                        <span>Portfolio<span className="text-muted-foreground">Builder</span></span>
                    </Link>
                    {userProfile && (
                        <span className="text-xs text-muted-foreground ml-4">Welcome, {userProfile.full_name || 'User'}</span>
                    )}
                    <div className="flex items-center gap-4">
                        <div className="relative w-64 hidden md:block group">
                            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground group-focus-within:text-white transition-colors" />
                            <Input
                                placeholder="Search assets..."
                                className="pl-8 h-8 bg-white/5 border-transparent focus:border-white/10 text-xs rounded-md transition-all"
                                value={search}
                                onChange={(e) => {
                                    setSearch(e.target.value)
                                    setPage(0)
                                }}
                            />
                        </div>
                        <div className="h-6 w-[1px] bg-white/10 mx-2"></div>
                        <div className="flex items-center gap-2">
                            <Button variant="ghost" size="icon" className="h-8 w-8 hover:bg-white/5" onClick={() => refetch()}>
                                <ArrowUpDown className="h-3.5 w-3.5 text-muted-foreground" />
                            </Button>
                            <SettingsModal>
                                <Button variant="ghost" size="icon" className="h-8 w-8 hover:bg-white/5">
                                    <div className="h-6 w-6 rounded-full bg-gradient-to-tr from-purple-500 to-blue-500 flex items-center justify-center overflow-hidden">
                                        {userProfile?.avatar_url ? (
                                            <img src={userProfile.avatar_url} alt="Profile" className="h-full w-full object-cover" />
                                        ) : userProfile?.full_name ? (
                                            <span className="text-[10px] font-bold text-white">{userProfile.full_name.charAt(0)}</span>
                                        ) : (
                                            <div className="h-2 w-2 rounded-full bg-white/50" />
                                        )}
                                    </div>
                                </Button>
                            </SettingsModal>
                        </div>
                    </div>
                </div>
            </header>

            <main className="container py-8 flex-1">
                <div className="flex flex-col space-y-4 mb-8">
                    <div className="flex items-end justify-between">
                        <div>
                            <h1 className="text-2xl font-medium tracking-tight text-white">Asset Universe</h1>
                            <p className="text-sm text-muted-foreground mt-1">Explore and analyze thousands of assets.</p>
                        </div>
                        <div className="flex items-center gap-2">
                            <Dialog open={isFilterOpen} onOpenChange={setIsFilterOpen}>
                                <DialogTrigger asChild>
                                    <Button variant="outline" size="sm" className="h-8 border-white/10 bg-white/5 hover:bg-white/10 text-xs">
                                        <Filter className="mr-2 h-3 w-3" /> Filters
                                        {(selectedRegions.length > 0 || selectedExchanges.length > 0) && (
                                            <span className="ml-1 rounded-full bg-primary w-1.5 h-1.5" />
                                        )}
                                    </Button>
                                </DialogTrigger>
                                <DialogContent className="sm:max-w-[425px] bg-[#0F1011] border-white/10 text-foreground">
                                    <DialogHeader>
                                        <DialogTitle className="text-white">Filter Assets</DialogTitle>
                                    </DialogHeader>
                                    <div className="grid gap-4 py-4">
                                        <div className="space-y-2">
                                            <h4 className="font-medium text-xs text-muted-foreground uppercase tracking-wider">Regions</h4>
                                            <div className="grid grid-cols-2 gap-2">
                                                {["Global", "US", "EU", "Asia"].map((r) => (
                                                    <div key={r} className="flex items-center space-x-2">
                                                        <Checkbox
                                                            id={`region-${r}`}
                                                            checked={selectedRegions.includes(r)}
                                                            onCheckedChange={() => toggleRegion(r)}
                                                            className="border-white/20 data-[state=checked]:bg-primary data-[state=checked]:border-primary"
                                                        />
                                                        <label
                                                            htmlFor={`region-${r}`}
                                                            className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 text-white/80"
                                                        >
                                                            {r}
                                                        </label>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                        <Separator className="bg-white/10" />
                                        <div className="space-y-2">
                                            <h4 className="font-medium text-xs text-muted-foreground uppercase tracking-wider">Exchanges</h4>
                                            <div className="grid grid-cols-2 gap-2">
                                                {["NYSE", "NASDAQ", "CCC", "XETRA"].map((e) => (
                                                    <div key={e} className="flex items-center space-x-2">
                                                        <Checkbox
                                                            id={`exch-${e}`}
                                                            checked={selectedExchanges.includes(e)}
                                                            onCheckedChange={() => toggleExchange(e)}
                                                            className="border-white/20 data-[state=checked]:bg-primary data-[state=checked]:border-primary"
                                                        />
                                                        <label
                                                            htmlFor={`exch-${e}`}
                                                            className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 text-white/80"
                                                        >
                                                            {e}
                                                        </label>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    </div>
                                    <DialogFooter>
                                        <Button variant="ghost" size="sm" onClick={clearFilters} className="text-xs hover:bg-white/5 text-muted-foreground">
                                            Clear all
                                        </Button>
                                        <Button size="sm" onClick={() => setIsFilterOpen(false)} className="text-xs">
                                            Apply Filters
                                        </Button>
                                    </DialogFooter>
                                </DialogContent>
                            </Dialog>
                        </div>
                    </div>

                    <Tabs defaultValue="All" value={category} onValueChange={(v) => { setCategory(v); setPage(0); }} className="w-full">
                        <TabsList className="bg-transparent p-0 h-auto border-b border-white/5 w-full justify-start rounded-none">
                            {["All", "Crypto", "Stock", "ETF", "Bond", "Commodity"].map((tab) => (
                                <TabsTrigger
                                    key={tab}
                                    value={tab}
                                    className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent px-4 py-2 text-xs font-medium text-muted-foreground data-[state=active]:text-white transition-all hover:text-white"
                                >
                                    {tab}
                                </TabsTrigger>
                            ))}
                        </TabsList>
                    </Tabs>
                </div>

                <div className="md:hidden mb-6">
                    <Input
                        placeholder="Search assets..."
                        className="bg-white/5 border-white/10"
                        value={search}
                        onChange={(e) => {
                            setSearch(e.target.value)
                            setPage(0)
                        }}
                    />
                </div>

                <div className="rounded-lg border border-white/5 bg-white/[0.02] overflow-hidden">
                    {isLoading ? (
                        <div className="space-y-0 divide-y divide-white/5">
                            {[...Array(10)].map((_, i) => (
                                <div key={i} className="h-10 w-full bg-white/[0.02] animate-pulse" />
                            ))}
                        </div>
                    ) : isError ? (
                        <div className="text-center py-12 text-red-400 text-sm">
                            Error loading assets. Please try again.
                        </div>
                    ) : (
                        <Table>
                            <TableHeader className="bg-white/[0.02]">
                                <TableRow className="hover:bg-transparent border-white/5">
                                    <TableHead className="w-[250px] text-xs uppercase tracking-wider font-medium text-muted-foreground cursor-pointer hover:text-white transition-colors" onClick={() => handleSort("name")}>
                                        <div className="flex items-center gap-1">
                                            Asset Name
                                            {sortBy === "name" && <ArrowUpDown className="h-3 w-3" />}
                                        </div>
                                    </TableHead>
                                    <TableHead className="w-[100px] text-xs uppercase tracking-wider font-medium text-muted-foreground text-right cursor-pointer hover:text-white transition-colors" onClick={() => handleSort("price")}>
                                        <div className="flex items-center justify-end gap-1">
                                            Price
                                            {sortBy === "price" && <ArrowUpDown className="h-3 w-3" />}
                                        </div>
                                    </TableHead>
                                    <TableHead className="w-[100px] text-xs uppercase tracking-wider font-medium text-muted-foreground text-right cursor-pointer hover:text-white transition-colors" onClick={() => handleSort("change_24h")}>
                                        <div className="flex items-center justify-end gap-1">
                                            24h Change
                                            {sortBy === "change_24h" && <ArrowUpDown className="h-3 w-3" />}
                                        </div>
                                    </TableHead>
                                    <TableHead className="w-[100px] text-xs uppercase tracking-wider font-medium text-muted-foreground hidden md:table-cell">7d Trend</TableHead>
                                    <TableHead className="w-[120px] text-xs uppercase tracking-wider font-medium text-muted-foreground cursor-pointer hover:text-white transition-colors hidden md:table-cell" onClick={() => handleSort("category")}>
                                        <div className="flex items-center gap-1">
                                            Category
                                            {sortBy === "category" && <ArrowUpDown className="h-3 w-3" />}
                                        </div>
                                    </TableHead>
                                    <TableHead className="w-[100px] text-xs uppercase tracking-wider font-medium text-muted-foreground hidden md:table-cell cursor-pointer hover:text-white transition-colors" onClick={() => handleSort("region")}>
                                        <div className="flex items-center gap-1">
                                            Region
                                            {sortBy === "region" && <ArrowUpDown className="h-3 w-3" />}
                                        </div>
                                    </TableHead>
                                    <TableHead className="w-[50px]"></TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {assets?.map((asset) => {
                                    const change = asset.change_24h || 0
                                    const isPositive = change >= 0
                                    const sparklineData = asset.sparkline_7d ? JSON.parse(asset.sparkline_7d) : []
                                    const categoryColor = CATEGORY_COLORS[asset.category || ""] || "bg-white/5 text-muted-foreground border-white/5"

                                    return (
                                        <TableRow
                                            key={asset.ticker}
                                            className="group cursor-pointer border-white/5 hover:bg-white/[0.04] transition-colors"
                                            onClick={() => router.push(`/asset/${asset.ticker}`)}
                                        >
                                            <TableCell>
                                                <div className="flex items-center gap-3">
                                                    {asset.logo_url ? (
                                                        <img src={asset.logo_url} alt={asset.ticker} className="h-6 w-6 rounded-full" />
                                                    ) : (
                                                        <div className="h-6 w-6 rounded-full bg-white/10 flex items-center justify-center text-[10px] font-bold text-white/50">
                                                            {asset.ticker.substring(0, 1)}
                                                        </div>
                                                    )}
                                                    <div className="flex flex-col">
                                                        <span className="font-medium text-sm text-white">{asset.name}</span>
                                                        <span className="text-xs text-muted-foreground font-mono">{asset.ticker}</span>
                                                    </div>
                                                </div>
                                            </TableCell>
                                            <TableCell className="text-right font-mono text-sm text-white">
                                                {asset.price ? `$${asset.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : "-"}
                                            </TableCell>
                                            <TableCell className="text-right">
                                                <div className={cn("flex items-center justify-end gap-1 font-mono text-xs", isPositive ? "text-emerald-400" : "text-rose-400")}>
                                                    {change !== 0 && (isPositive ? "+" : "")}
                                                    {change.toFixed(2)}%
                                                </div>
                                            </TableCell>
                                            <TableCell className="hidden md:table-cell py-2">
                                                <Sparkline data={sparklineData} color={isPositive ? "#34d399" : "#fb7185"} />
                                            </TableCell>
                                            <TableCell className="hidden md:table-cell">
                                                <Badge variant="secondary" className={cn("text-[10px] font-normal border", categoryColor)}>
                                                    {asset.category}
                                                </Badge>
                                            </TableCell>
                                            <TableCell className="text-xs text-muted-foreground hidden md:table-cell">{asset.region}</TableCell>
                                            <TableCell className="text-right p-2">
                                                <Link href={`/asset/${asset.ticker}`} onClick={(e) => e.stopPropagation()}>
                                                    <Button variant="ghost" size="icon" className="h-7 w-7 opacity-0 group-hover:opacity-100 transition-opacity hover:bg-white/10">
                                                        <ArrowUpRight className="h-3.5 w-3.5 text-muted-foreground" />
                                                    </Button>
                                                </Link>
                                            </TableCell>
                                        </TableRow>
                                    )
                                })}
                                {assets?.length === 0 && (
                                    <TableRow>
                                        <TableCell colSpan={7} className="h-24 text-center text-muted-foreground">
                                            No assets found matching your search.
                                        </TableCell>
                                    </TableRow>
                                )}
                            </TableBody>
                        </Table>
                    )}

                    <div className="flex items-center justify-between border-t border-white/5 px-4 py-3 bg-white/[0.02]">
                        <div className="text-xs text-muted-foreground">
                            Showing {page * limit + 1}-{Math.min((page + 1) * limit, 10000)} assets
                        </div>
                        <div className="flex items-center space-x-2">
                            <Button
                                variant="ghost"
                                size="sm"
                                className="h-7 px-2 text-xs hover:bg-white/5 disabled:opacity-30"
                                onClick={() => setPage((p) => Math.max(0, p - 1))}
                                disabled={page === 0 || isLoading}
                            >
                                <ChevronLeft className="h-3 w-3 mr-1" /> Previous
                            </Button>
                            <Button
                                variant="ghost"
                                size="sm"
                                className="h-7 px-2 text-xs hover:bg-white/5 disabled:opacity-30"
                                onClick={() => setPage((p) => p + 1)}
                                disabled={!assets || assets.length < limit || isLoading}
                            >
                                Next <ChevronRight className="h-3 w-3 ml-1" />
                            </Button>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    )
}
