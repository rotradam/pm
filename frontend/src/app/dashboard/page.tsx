"use client"

import { useState } from "react"
import { useQuery, keepPreviousData } from "@tanstack/react-query"
import { fetchAssets, Asset } from "@/lib/api"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Search, Filter, ChevronLeft, ChevronRight, Layers, ArrowUpRight } from "lucide-react"
import Link from "next/link"

export default function Dashboard() {
    const [search, setSearch] = useState("")
    const [page, setPage] = useState(0)
    const limit = 20

    const { data: assets, isLoading, isError } = useQuery<Asset[]>({
        queryKey: ['assets', search, page],
        queryFn: () => fetchAssets(search, undefined, limit, page * limit),
        placeholderData: keepPreviousData
    })

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
                <div className="flex items-end justify-between mb-8">
                    <div>
                        <h1 className="text-2xl font-medium tracking-tight text-white">Asset Universe</h1>
                        <p className="text-sm text-muted-foreground mt-1">Explore and analyze thousands of assets.</p>
                    </div>
                    <Button variant="outline" size="sm" className="h-8 border-white/10 bg-white/5 hover:bg-white/10 text-xs">
                        <Filter className="mr-2 h-3 w-3" /> Filters
                    </Button>
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
                        <div className="relative w-full overflow-auto">
                            <table className="w-full caption-bottom text-sm text-left">
                                <thead className="[&_tr]:border-b [&_tr]:border-white/5">
                                    <tr className="border-b border-white/5 transition-colors hover:bg-white/[0.02]">
                                        <th className="h-10 px-4 align-middle font-medium text-muted-foreground text-xs uppercase tracking-wider w-[120px]">Ticker</th>
                                        <th className="h-10 px-4 align-middle font-medium text-muted-foreground text-xs uppercase tracking-wider">Name</th>
                                        <th className="h-10 px-4 align-middle font-medium text-muted-foreground text-xs uppercase tracking-wider w-[150px]">Category</th>
                                        <th className="h-10 px-4 align-middle font-medium text-muted-foreground text-xs uppercase tracking-wider w-[150px]">Region</th>
                                        <th className="h-10 px-4 align-middle font-medium text-muted-foreground text-xs uppercase tracking-wider text-right w-[100px]"></th>
                                    </tr>
                                </thead>
                                <tbody className="[&_tr:last-child]:border-0 divide-y divide-white/5">
                                    {assets?.map((asset) => (
                                        <tr key={asset.ticker} className="group transition-colors hover:bg-white/[0.04]">
                                            <td className="p-4 align-middle font-medium text-white font-mono text-xs">{asset.ticker}</td>
                                            <td className="p-4 align-middle text-muted-foreground group-hover:text-white transition-colors">{asset.name}</td>
                                            <td className="p-4 align-middle">
                                                <span className="inline-flex items-center rounded-md border border-white/5 bg-white/5 px-2 py-0.5 text-[10px] font-medium text-muted-foreground">
                                                    {asset.category}
                                                </span>
                                            </td>
                                            <td className="p-4 align-middle text-muted-foreground text-xs">{asset.region}</td>
                                            <td className="p-4 align-middle text-right">
                                                <Link href={`/asset/${asset.ticker}`} className="opacity-0 group-hover:opacity-100 transition-opacity">
                                                    <Button variant="ghost" size="sm" className="h-7 w-7 p-0 hover:bg-white/10">
                                                        <ArrowUpRight className="h-4 w-4 text-muted-foreground" />
                                                    </Button>
                                                </Link>
                                            </td>
                                        </tr>
                                    ))}
                                    {assets?.length === 0 && (
                                        <tr>
                                            <td colSpan={5} className="p-12 text-center text-muted-foreground text-sm">
                                                No assets found matching your search.
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
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
