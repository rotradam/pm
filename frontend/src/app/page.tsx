import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ArrowRight, Search, BarChart3, Globe, Zap, Layers } from "lucide-react"

export default function Home() {
    return (
        <div className="flex min-h-screen flex-col bg-[#08090A] text-foreground selection:bg-primary/20">
            {/* Navbar */}
            <header className="fixed top-0 w-full z-50 border-b border-white/5 bg-[#08090A]/80 backdrop-blur-md">
                <div className="container flex h-14 items-center justify-between">
                    <div className="flex items-center gap-2 font-medium text-sm tracking-tight">
                        <div className="h-6 w-6 rounded-md bg-white/10 flex items-center justify-center">
                            <Layers className="h-3.5 w-3.5 text-white" />
                        </div>
                        <span>Portfolio<span className="text-muted-foreground">Builder</span></span>
                    </div>
                    <nav className="flex items-center gap-4 text-sm font-medium">
                        <Link href="/dashboard" className="text-muted-foreground hover:text-foreground transition-colors">
                            Dashboard
                        </Link>
                        <Link href="/dashboard">
                            <Button size="sm" variant="secondary" className="h-8 px-4 rounded-full bg-white text-black hover:bg-white/90 font-medium">
                                Get Started
                            </Button>
                        </Link>
                    </nav>
                </div>
            </header>

            <main className="flex-1 pt-32 pb-16">
                {/* Hero Section */}
                <section className="container relative flex flex-col items-center justify-center text-center gap-8">
                    {/* Background Glow */}
                    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-purple-500/10 rounded-full blur-[120px] -z-10" />

                    <div className="inline-flex items-center rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-medium text-primary backdrop-blur-xl animate-in fade-in slide-in-from-bottom-4 duration-1000">
                        <span className="flex h-2 w-2 rounded-full bg-green-500 mr-2 animate-pulse"></span>
                        v1.0 Now Available
                    </div>

                    <h1 className="text-5xl md:text-7xl font-medium tracking-tight text-white max-w-4xl animate-in fade-in slide-in-from-bottom-8 duration-1000 delay-100">
                        Build your portfolio with <br />
                        <span className="text-transparent bg-clip-text bg-gradient-to-b from-white to-white/40">
                            precision and speed.
                        </span>
                    </h1>

                    <p className="max-w-xl text-lg text-muted-foreground leading-relaxed animate-in fade-in slide-in-from-bottom-8 duration-1000 delay-200">
                        Access thousands of assets across Crypto, Stocks, and ETFs.
                        Analyze, optimize, and deploy strategies in seconds with a workspace designed for focus.
                    </p>

                    <div className="flex flex-col sm:flex-row gap-3 w-full max-w-md mt-8 animate-in fade-in slide-in-from-bottom-8 duration-1000 delay-300">
                        <div className="relative flex-1 group">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground group-focus-within:text-white transition-colors" />
                            <Input
                                placeholder="Search assets (e.g. AAPL)..."
                                className="pl-10 h-12 bg-white/5 border-white/10 text-white placeholder:text-muted-foreground focus-visible:ring-0 focus-visible:border-white/20 rounded-lg transition-all"
                            />
                            <div className="absolute right-3 top-1/2 -translate-y-1/2 flex gap-1">
                                <kbd className="pointer-events-none inline-flex h-5 select-none items-center gap-1 rounded border border-white/10 bg-white/5 px-1.5 font-mono text-[10px] font-medium text-muted-foreground opacity-100">
                                    <span className="text-xs">⌘</span>K
                                </kbd>
                            </div>
                        </div>
                        <Link href="/dashboard">
                            <Button size="lg" className="h-12 px-6 w-full sm:w-auto bg-white text-black hover:bg-white/90 rounded-lg font-medium">
                                Explore <ArrowRight className="ml-2 h-4 w-4" />
                            </Button>
                        </Link>
                    </div>
                </section>

                {/* Features Grid */}
                <section className="container mt-32">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        {[
                            {
                                icon: Globe,
                                title: "Global Assets",
                                desc: "Access S&P 500, NASDAQ, and Top 500 Crypto assets in one unified interface."
                            },
                            {
                                icon: Zap,
                                title: "Real-time Analysis",
                                desc: "Run advanced OLPS algorithms like DOLPS and WAEG with instant feedback."
                            },
                            {
                                icon: Search,
                                title: "Instant Search",
                                desc: "Find any asset instantly with our local, optimized database engine."
                            }
                        ].map((feature, i) => (
                            <div key={i} className="group p-6 rounded-xl border border-white/5 bg-white/[0.02] hover:bg-white/[0.04] transition-colors">
                                <div className="h-10 w-10 rounded-lg bg-white/5 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                                    <feature.icon className="h-5 w-5 text-white" />
                                </div>
                                <h3 className="text-lg font-medium text-white mb-2">{feature.title}</h3>
                                <p className="text-sm text-muted-foreground leading-relaxed">{feature.desc}</p>
                            </div>
                        ))}
                    </div>
                </section>
            </main>

            <footer className="border-t border-white/5 py-8">
                <div className="container flex items-center justify-between text-xs text-muted-foreground">
                    <span>&copy; 2025 PortfolioBuilder</span>
                    <div className="flex gap-4">
                        <Link href="#" className="hover:text-white transition-colors">Privacy</Link>
                        <Link href="#" className="hover:text-white transition-colors">Terms</Link>
                        <Link href="#" className="hover:text-white transition-colors">Twitter</Link>
                    </div>
                </div>
            </footer>
        </div>
    )
}
