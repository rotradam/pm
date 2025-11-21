"use client"

import * as React from "react"
import { useRouter } from "next/navigation"
import { useQuery } from "@tanstack/react-query"
import { Calculator, Calendar, CreditCard, Settings, Smile, User } from "lucide-react"

import {
    CommandDialog,
    CommandEmpty,
    CommandGroup,
    CommandInput,
    CommandItem,
    CommandList,
    CommandSeparator,
    CommandShortcut,
} from "@/components/ui/command"
import { fetchAssets } from "@/lib/api"
import { Asset } from "@/lib/api"

export function SearchCommand() {
    const [open, setOpen] = React.useState(false)
    const [search, setSearch] = React.useState("")
    const router = useRouter()

    React.useEffect(() => {
        const down = (e: KeyboardEvent) => {
            if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
                e.preventDefault()
                setOpen((open) => !open)
            }
        }

        document.addEventListener("keydown", down)
        return () => document.removeEventListener("keydown", down)
    }, [])

    const { data: assets } = useQuery<Asset[]>({
        queryKey: ["assets", "search", search],
        queryFn: () => fetchAssets(search, undefined, 20), // Fetch top 20 matches
        enabled: open, // Only fetch when open
        staleTime: 1000 * 60,
    })

    const runCommand = React.useCallback((command: () => unknown) => {
        setOpen(false)
        command()
    }, [])

    return (
        <>
            <CommandDialog open={open} onOpenChange={setOpen} shouldFilter={false}>
                <CommandInput
                    placeholder="Type a command or search assets..."
                    value={search}
                    onValueChange={setSearch}
                />
                <CommandList>
                    <CommandEmpty>No results found.</CommandEmpty>
                    <CommandGroup heading="Suggestions">
                        <CommandItem onSelect={() => runCommand(() => router.push("/dashboard"))}>
                            <Calendar className="mr-2 h-4 w-4" />
                            <span>Dashboard</span>
                        </CommandItem>
                        <CommandItem onSelect={() => runCommand(() => router.push("/"))}>
                            <Smile className="mr-2 h-4 w-4" />
                            <span>Home</span>
                        </CommandItem>
                    </CommandGroup>
                    <CommandSeparator />
                    <CommandGroup heading="Assets">
                        {assets?.map((asset) => (
                            <CommandItem
                                key={asset.ticker}
                                onSelect={() => runCommand(() => router.push(`/asset/${asset.ticker}`))}
                                value={`${asset.ticker} ${asset.name}`}
                            >
                                <div className="flex flex-col">
                                    <span className="font-medium">{asset.ticker}</span>
                                    <span className="text-xs text-muted-foreground">{asset.name}</span>
                                </div>
                                <span className="ml-auto text-xs text-muted-foreground">{asset.category}</span>
                            </CommandItem>
                        ))}
                    </CommandGroup>
                </CommandList>
            </CommandDialog>
        </>
    )
}
