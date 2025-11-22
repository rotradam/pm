"use client"

import { Inter } from "next/font/google"
import "./globals.css"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { useState } from "react"
import { cn } from "@/lib/utils"

const inter = Inter({ subsets: ["latin"], variable: "--font-sans" })

import { SearchCommand } from "@/components/search-command";

import { Toaster } from "@/components/ui/sonner"

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    const queryClient = new QueryClient();

    return (
        <html lang="en">
            <body className={cn("min-h-screen bg-background font-sans antialiased", inter.variable)}>
                <QueryClientProvider client={queryClient}>
                    <SearchCommand />
                    {children}
                    <Toaster />
                </QueryClientProvider>
            </body>
        </html>
    )
}

