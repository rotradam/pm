"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { useQuery, keepPreviousData } from "@tanstack/react-query"
import { fetchAssets, Asset } from "@/lib/api"
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

export default function Dashboard() {
    const router = useRouter()
    const [search, setSearch] = useState("")
    const [page, setPage] = useState(0)
    const [category, setCategory] = useState("All")
    const [region, setRegion] = useState<string | undefined>(undefined)
    const [exchange, setExchange] = useState<string | undefined>(undefined)
    const [sortBy, setSortBy] = useState<string | undefined>(undefined)
    const [sortOrder, setSortOrder] = useState<"asc" | "desc">("asc")

    const limit = 20

    const { data: assets, isLoading, isError } = useQuery<Asset[]>({
        queryKey: ['assets', search, category, region, exchange, sortBy, sortOrder, page],
        queryFn: () => fetchAssets(
            search,
            category === "All" ? undefined : category,
            limit,
            page * limit,
            region === "All" ? undefined : region,
            exchange === "All" ? undefined : exchange,
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
        setRegion(undefined)
        setExchange(undefined)
        setSearch("")
        setPage(0)
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
                            <div className="h-6 w-6 rounded-full bg-gradient-to-tr from-purple-500 to-blue-500"></div>
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
                            <Popover>
                                <PopoverTrigger asChild>
                                    <Button variant="outline" size="sm" className="h-8 border-white/10 bg-white/5 hover:bg-white/10 text-xs">
                                        <Filter className="mr-2 h-3 w-3" /> Filters
                                        {(region || exchange) && <span className="ml-1 rounded-full bg-primary w-1.5 h-1.5" />}
                                    </Button>
                                </PopoverTrigger>
                                <PopoverContent className="w-80 p-4 bg-[#0F1011] border-white/10" align="end">
                                    <div className="space-y-4">
                                        <div className="space-y-2">
                                            <h4 className="font-medium leading-none text-white">Filters</h4>
                                            <p className="text-xs text-muted-foreground">Refine your asset search.</p>
                                        </div>
                                        <div className="space-y-2">
                                            <Label htmlFor="region" className="text-xs">Region</Label>
                                            <Select value={region} onValueChange={setRegion}>
                                                <SelectTrigger id="region" className="h-8 text-xs bg-white/5 border-white/10">
                                                    <SelectValue placeholder="All Regions" />
                                                </SelectTrigger>
                                                <SelectContent>
                                                    <SelectItem value="All">All Regions</SelectItem>
                                                    <SelectItem value="Global">Global</SelectItem>
                                                    <SelectItem value="US">United States</SelectItem>
                                                    <SelectItem value="EU">Europe</SelectItem>
                                                    <SelectItem value="Asia">Asia</SelectItem>
                                                </SelectContent>
                                            </Select>
                                        </div>
                                        <div className="space-y-2">
                                            <Label htmlFor="exchange" className="text-xs">Exchange</Label>
                                            <Select value={exchange} onValueChange={setExchange}>
                                                <SelectTrigger id="exchange" className="h-8 text-xs bg-white/5 border-white/10">
                                                    <SelectValue placeholder="All Exchanges" />
                                                </SelectTrigger>
                                                <SelectContent>
                                                    <SelectItem value="All">All Exchanges</SelectItem>
                                                    <SelectItem value="NYSE">NYSE</SelectItem>
                                                    <SelectItem value="NASDAQ">NASDAQ</SelectItem>
                                                    <SelectItem value="CCC">Crypto (CCC)</SelectItem>
                                                </SelectContent>
                                            </Select>
                                        </div>
                                        <div className="pt-2 flex justify-end">
                                            <Button variant="ghost" size="sm" onClick={clearFilters} className="h-7 text-xs hover:bg-white/5">
                                                Clear all
                                            </Button>
                                        </div>
                                    </div>
                                </PopoverContent>
                            </Popover>
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
                                    <TableHead className="w-[100px] text-xs uppercase tracking-wider font-medium text-muted-foreground cursor-pointer hover:text-white transition-colors" onClick={() => handleSort("ticker")}>
                                        <div className="flex items-center gap-1">
                                            Ticker
                                            {sortBy === "ticker" && <ArrowUpDown className="h-3 w-3" />}
                                        </div>
                                    </TableHead>
                                    <TableHead className="text-xs uppercase tracking-wider font-medium text-muted-foreground cursor-pointer hover:text-white transition-colors" onClick={() => handleSort("name")}>
                                        <div className="flex items-center gap-1">
                                            Name
                                            {sortBy === "name" && <ArrowUpDown className="h-3 w-3" />}
                                        </div>
                                    </TableHead>
                                    <TableHead className="w-[120px] text-xs uppercase tracking-wider font-medium text-muted-foreground cursor-pointer hover:text-white transition-colors" onClick={() => handleSort("category")}>
                                        <div className="flex items-center gap-1">
                                            Category
                                            {sortBy === "category" && <ArrowUpDown className="h-3 w-3" />}
                                        </div>
                                    </TableHead>
                                    <TableHead className="w-[150px] text-xs uppercase tracking-wider font-medium text-muted-foreground hidden md:table-cell">Subcategory</TableHead>
                                    <TableHead className="w-[100px] text-xs uppercase tracking-wider font-medium text-muted-foreground hidden md:table-cell cursor-pointer hover:text-white transition-colors" onClick={() => handleSort("region")}>
                                        <div className="flex items-center gap-1">
                                            Region
                                            {sortBy === "region" && <ArrowUpDown className="h-3 w-3" />}
                                        </div>
                                    </TableHead>
                                    <TableHead className="w-[80px] text-xs uppercase tracking-wider font-medium text-muted-foreground hidden md:table-cell">Exch</TableHead>
                                    <TableHead className="w-[50px]"></TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {assets?.map((asset) => (
                                    <TableRow
                                        key={asset.ticker}
                                        className="group cursor-pointer border-white/5 hover:bg-white/[0.04] transition-colors"
                                        onDoubleClick={() => router.push(`/asset/${asset.ticker}`)}
                                    >
                                        <TableCell className="font-mono text-xs font-medium text-white">{asset.ticker}</TableCell>
                                        <TableCell className="text-muted-foreground group-hover:text-white transition-colors">{asset.name}</TableCell>
                                        <TableCell>
                                            <Badge variant="secondary" className="bg-white/5 hover:bg-white/10 text-muted-foreground border-white/5 text-[10px] font-normal">
                                                {asset.category}
                                            </Badge>
                                        </TableCell>
                                        <TableCell className="text-xs text-muted-foreground hidden md:table-cell">{asset.subcategory}</TableCell>
                                        <TableCell className="text-xs text-muted-foreground hidden md:table-cell">{asset.region}</TableCell>
                                        <TableCell className="text-xs text-muted-foreground hidden md:table-cell">{asset.exchange}</TableCell>
                                        <TableCell className="text-right p-2">
                                            <Link href={`/asset/${asset.ticker}`} onClick={(e) => e.stopPropagation()}>
                                                <Button variant="ghost" size="icon" className="h-7 w-7 opacity-0 group-hover:opacity-100 transition-opacity hover:bg-white/10">
                                                    <ArrowUpRight className="h-3.5 w-3.5 text-muted-foreground" />
                                                </Button>
                                            </Link>
                                        </TableCell>
                                    </TableRow>
                                ))}
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
