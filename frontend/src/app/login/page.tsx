'use client'

import { login, signup, resetPassword } from './actions'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { createClient } from "@/lib/supabase/client"
import { Chrome, Loader2, ArrowRight, CheckCircle2 } from "lucide-react"
import { toast } from "sonner"
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog"

export default function LoginPage() {
    const router = useRouter()
    const [isLoading, setIsLoading] = useState(false)
    const [resetEmail, setResetEmail] = useState("")
    const [isResetOpen, setIsResetOpen] = useState(false)
    const [isResetSent, setIsResetSent] = useState(false)

    const handleGoogleLogin = async () => {
        const supabase = createClient()
        const { error } = await supabase.auth.signInWithOAuth({
            provider: 'google',
            options: {
                redirectTo: `${window.location.origin}/auth/callback`,
            },
        })
        if (error) {
            toast.error("Failed to initiate Google Login")
        }
    }

    const handleLogin = async (formData: FormData) => {
        setIsLoading(true)
        try {
            const result = await login(formData)
            if (result?.error) {
                toast.error(result.error)
            } else {
                toast.success("Logged in successfully")
                router.push('/dashboard')
            }
        } catch (e) {
            toast.error("Login failed. Please check your credentials.")
        } finally {
            setIsLoading(false)
        }
    }

    const handleSignup = async (formData: FormData) => {
        setIsLoading(true)
        try {
            const result = await signup(formData)
            if (result?.error) {
                toast.error(result.error)
            } else {
                toast.success("Signup successful! Please check your email to confirm.")
                router.push('/dashboard')
            }
        } catch (e) {
            toast.error("Signup failed. Please try again.")
        } finally {
            setIsLoading(false)
        }
    }

    const handleResetPassword = async (e: React.FormEvent) => {
        e.preventDefault()
        setIsLoading(true)
        try {
            await resetPassword(resetEmail)
            setIsResetSent(true)
            toast.success("Reset link sent to your email")
        } catch (error) {
            toast.error("Failed to send reset link. Please try again.")
        } finally {
            setIsLoading(false)
        }
    }

    return (
        <div className="w-full lg:grid lg:min-h-screen lg:grid-cols-2 xl:min-h-screen bg-background">
            <div className="flex items-center justify-center py-12">
                <div className="mx-auto grid w-[350px] gap-6">
                    <div className="grid gap-2 text-center">
                        <h1 className="text-3xl font-bold">Welcome back</h1>
                        <p className="text-balance text-muted-foreground">
                            Enter your credentials to access your portfolio
                        </p>
                    </div>
                    <Tabs defaultValue="login" className="w-full">
                        <TabsList className="grid w-full grid-cols-2 mb-4">
                            <TabsTrigger value="login">Login</TabsTrigger>
                            <TabsTrigger value="signup">Sign Up</TabsTrigger>
                        </TabsList>
                        <TabsContent value="login">
                            <form action={handleLogin}>
                                <div className="grid gap-4">
                                    <div className="grid gap-2">
                                        <Label htmlFor="email">Email or Username</Label>
                                        <Input
                                            id="email"
                                            name="email"
                                            type="text"
                                            placeholder="m@example.com"
                                            required
                                        />
                                    </div>
                                    <div className="grid gap-2">
                                        <div className="flex items-center">
                                            <Label htmlFor="password">Password</Label>
                                            <Dialog open={isResetOpen} onOpenChange={(open) => {
                                                setIsResetOpen(open)
                                                if (!open) setIsResetSent(false)
                                            }}>
                                                <DialogTrigger asChild>
                                                    <Button variant="link" className="ml-auto inline-block text-sm underline px-0 h-auto font-normal text-muted-foreground hover:text-primary">
                                                        Forgot your password?
                                                    </Button>
                                                </DialogTrigger>
                                                <DialogContent className="sm:max-w-md bg-[#0F1011] border-white/10">
                                                    <DialogHeader>
                                                        <DialogTitle>Reset Password</DialogTitle>
                                                        <DialogDescription>
                                                            Enter your email address and we'll send you a link to reset your password.
                                                        </DialogDescription>
                                                    </DialogHeader>
                                                    {isResetSent ? (
                                                        <div className="flex flex-col items-center justify-center py-6 space-y-4 text-center">
                                                            <div className="h-12 w-12 rounded-full bg-green-500/10 flex items-center justify-center">
                                                                <CheckCircle2 className="h-6 w-6 text-green-500" />
                                                            </div>
                                                            <div className="space-y-2">
                                                                <h4 className="font-medium text-white">Check your email</h4>
                                                                <p className="text-sm text-muted-foreground">
                                                                    We've sent a password reset link to <strong>{resetEmail}</strong>
                                                                </p>
                                                            </div>
                                                            <Button variant="outline" onClick={() => setIsResetOpen(false)} className="mt-4">
                                                                Close
                                                            </Button>
                                                        </div>
                                                    ) : (
                                                        <form onSubmit={handleResetPassword} className="space-y-4">
                                                            <div className="space-y-2">
                                                                <Label htmlFor="reset-email">Email</Label>
                                                                <Input
                                                                    id="reset-email"
                                                                    type="email"
                                                                    placeholder="m@example.com"
                                                                    value={resetEmail}
                                                                    onChange={(e) => setResetEmail(e.target.value)}
                                                                    required
                                                                    className="bg-white/5 border-white/10"
                                                                />
                                                            </div>
                                                            <div className="flex justify-end">
                                                                <Button type="submit" disabled={isLoading}>
                                                                    {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                                                                    Send Reset Link
                                                                </Button>
                                                            </div>
                                                        </form>
                                                    )}
                                                </DialogContent>
                                            </Dialog>
                                        </div>
                                        <Input id="password" name="password" type="password" required />
                                    </div>
                                    <Button type="submit" className="w-full" disabled={isLoading}>
                                        {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                                        Login
                                    </Button>
                                    <div className="relative">
                                        <div className="absolute inset-0 flex items-center">
                                            <span className="w-full border-t" />
                                        </div>
                                        <div className="relative flex justify-center text-xs uppercase">
                                            <span className="bg-background px-2 text-muted-foreground">
                                                Or continue with
                                            </span>
                                        </div>
                                    </div>
                                    <Button variant="outline" type="button" className="w-full" onClick={handleGoogleLogin}>
                                        <Chrome className="mr-2 h-4 w-4" /> Google
                                    </Button>
                                </div>
                            </form>
                        </TabsContent>
                        <TabsContent value="signup">
                            <form action={handleSignup}>
                                <div className="grid gap-4">
                                    <div className="grid gap-2">
                                        <Label htmlFor="fullName">Full Name</Label>
                                        <Input id="fullName" name="fullName" placeholder="John Doe" required />
                                    </div>
                                    <div className="grid gap-2">
                                        <Label htmlFor="email">Email</Label>
                                        <Input id="email" name="email" type="email" placeholder="m@example.com" required />
                                    </div>
                                    <div className="grid gap-2">
                                        <Label htmlFor="password">Password</Label>
                                        <Input id="password" name="password" type="password" required />
                                    </div>
                                    <Button type="submit" className="w-full" disabled={isLoading}>
                                        {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                                        Create Account
                                    </Button>
                                    <div className="relative">
                                        <div className="absolute inset-0 flex items-center">
                                            <span className="w-full border-t" />
                                        </div>
                                        <div className="relative flex justify-center text-xs uppercase">
                                            <span className="bg-background px-2 text-muted-foreground">
                                                Or continue with
                                            </span>
                                        </div>
                                    </div>
                                    <Button variant="outline" type="button" className="w-full" onClick={handleGoogleLogin}>
                                        <Chrome className="mr-2 h-4 w-4" /> Google
                                    </Button>
                                </div>
                            </form>
                        </TabsContent>
                    </Tabs>
                </div>
            </div>
            <div className="hidden bg-muted lg:block relative overflow-hidden">
                <div className="absolute inset-0 bg-zinc-900/20 z-10" />
                <img
                    src="https://images.pexels.com/photos/21766388/pexels-photo-21766388.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1"
                    alt="Financial Abstract"
                    className="h-full w-full object-cover dark:brightness-[0.2] dark:grayscale"
                />
                <div className="absolute bottom-10 left-10 z-20 text-white max-w-md">
                    <h2 className="text-2xl font-bold mb-2">Institutional Grade Analytics</h2>
                    <p className="text-sm text-white/80">
                        Access professional portfolio management tools and real-time market data in a secure, enterprise-ready environment.
                    </p>
                </div>
            </div>
        </div>
    )
}
