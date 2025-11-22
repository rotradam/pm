"use client"

import { useState, useEffect, useRef } from "react"
import { createClient } from "@/lib/supabase/client"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { toast } from "sonner"
import { User, Lock, Upload, Camera, Loader2, Settings, CreditCard, Check } from "lucide-react"
import { deleteAccount, updatePreferences } from "@/app/settings/actions"
import { cn } from "@/lib/utils"

interface SettingsModalProps {
    children: React.ReactNode
}

const AVAILABLE_EXCHANGES = [
    { id: "binance", name: "Binance" },
    { id: "coinbase", name: "Coinbase" },
    { id: "kraken", name: "Kraken" },
    { id: "kucoin", name: "KuCoin" },
    { id: "okx", name: "OKX" },
    { id: "bybit", name: "Bybit" },
    { id: "gateio", name: "Gate.io" },
    { id: "bitstamp", name: "Bitstamp" },
]

export function SettingsModal({ children }: SettingsModalProps) {
    const [open, setOpen] = useState(false)
    const [user, setUser] = useState<any>(null)
    const [profile, setProfile] = useState<any>(null)
    const [loading, setLoading] = useState(false)
    const [uploading, setUploading] = useState(false)

    // Form states
    const [fullName, setFullName] = useState("")
    const [username, setUsername] = useState("")
    const [avatarUrl, setAvatarUrl] = useState("")
    const [preferredExchanges, setPreferredExchanges] = useState<string[]>([])

    const fileInputRef = useRef<HTMLInputElement>(null)
    const supabase = createClient()

    useEffect(() => {
        if (open) {
            getProfile()
        }
    }, [open])

    const getProfile = async () => {
        setLoading(true)
        const { data: { user } } = await supabase.auth.getUser()
        setUser(user)
        if (user) {
            const { data } = await supabase
                .from('profiles')
                .select('*')
                .eq('id', user.id)
                .single()

            if (data) {
                setProfile(data)
                setFullName(data.full_name || "")
                setUsername(data.username || "")
                setAvatarUrl(data.avatar_url || "")
                setPreferredExchanges(data.preferred_exchanges || [])
            }
        }
        setLoading(false)
    }

    const updateProfile = async () => {
        try {
            setLoading(true)
            const updates = {
                id: user.id,
                full_name: fullName,
                username: username,
                avatar_url: avatarUrl,
                updated_at: new Date().toISOString(),
            }

            const { error } = await supabase
                .from('profiles')
                .upsert(updates)

            if (error) throw error
            toast.success("Profile updated successfully")
        } catch (error: any) {
            toast.error("Error updating profile")
            console.error("Profile update error:", error.message || error)
        } finally {
            setLoading(false)
        }
    }

    const handleAvatarUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
        try {
            setUploading(true)
            if (!event.target.files || event.target.files.length === 0) {
                throw new Error('You must select an image to upload.')
            }

            const file = event.target.files[0]
            const fileExt = file.name.split('.').pop()
            const filePath = `${user.id}-${Math.random()}.${fileExt}`

            const { error: uploadError } = await supabase.storage
                .from('avatars')
                .upload(filePath, file)

            if (uploadError) {
                throw uploadError
            }

            const { data } = supabase.storage.from('avatars').getPublicUrl(filePath)
            setAvatarUrl(data.publicUrl)
            toast.success("Avatar uploaded successfully")
        } catch (error) {
            toast.error("Error uploading avatar")
            console.error(error)
        } finally {
            setUploading(false)
        }
    }

    const updatePassword = async (formData: FormData) => {
        const password = formData.get("password") as string
        const confirmPassword = formData.get("confirmPassword") as string

        if (password !== confirmPassword) {
            toast.error("Passwords do not match")
            return
        }

        try {
            const { error } = await supabase.auth.updateUser({ password })
            if (error) throw error
            toast.success("Password updated successfully")
        } catch (error) {
            toast.error("Error updating password")
        }
    }

    const toggleExchange = (exchangeId: string) => {
        setPreferredExchanges(prev =>
            prev.includes(exchangeId)
                ? prev.filter(id => id !== exchangeId)
                : [...prev, exchangeId]
        )
    }

    const handleSavePreferences = async () => {
        try {
            setLoading(true)
            await updatePreferences(preferredExchanges)
            toast.success("Preferences saved successfully")
        } catch (error) {
            toast.error("Failed to save preferences")
        } finally {
            setLoading(false)
        }
    }

    const handleDeleteAccount = async () => {
        if (confirm("Are you sure you want to delete your account? This action cannot be undone.")) {
            try {
                setLoading(true)
                await deleteAccount()
                toast.success("Account deleted")
            } catch (error) {
                toast.error("Failed to delete account. Please contact support.")
                console.error(error)
                setLoading(false)
            }
        }
    }

    return (
        <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
                {children}
            </DialogTrigger>
            <DialogContent className="sm:max-w-4xl bg-[#0F1011] border-white/10 text-foreground p-0 gap-0 overflow-hidden shadow-2xl">
                <DialogHeader className="sr-only">
                    <DialogTitle>Settings</DialogTitle>
                    <DialogDescription>Manage your account settings</DialogDescription>
                </DialogHeader>
                <div className="flex h-[600px]">
                    <Tabs defaultValue="profile" className="flex w-full">
                        <div className="w-[240px] border-r border-white/10 bg-white/[0.02] p-6 flex flex-col gap-6">
                            <div className="px-2">
                                <h2 className="text-xl font-semibold tracking-tight text-white">Settings</h2>
                                <p className="text-xs text-muted-foreground mt-1">Manage your preferences</p>
                            </div>
                            <TabsList className="flex flex-col w-full h-auto bg-transparent space-y-1 p-0">
                                <TabsTrigger
                                    value="profile"
                                    className="w-full justify-start px-3 py-2 font-medium text-sm text-muted-foreground data-[state=active]:text-white data-[state=active]:bg-white/5 hover:bg-white/5 hover:text-white transition-colors rounded-md"
                                >
                                    <User className="mr-3 h-4 w-4" />
                                    Profile
                                </TabsTrigger>
                                <TabsTrigger
                                    value="preferences"
                                    className="w-full justify-start px-3 py-2 font-medium text-sm text-muted-foreground data-[state=active]:text-white data-[state=active]:bg-white/5 hover:bg-white/5 hover:text-white transition-colors rounded-md"
                                >
                                    <Settings className="mr-3 h-4 w-4" />
                                    Preferences
                                </TabsTrigger>
                                <TabsTrigger
                                    value="billing"
                                    className="w-full justify-start px-3 py-2 font-medium text-sm text-muted-foreground data-[state=active]:text-white data-[state=active]:bg-white/5 hover:bg-white/5 hover:text-white transition-colors rounded-md"
                                >
                                    <CreditCard className="mr-3 h-4 w-4" />
                                    Billing
                                </TabsTrigger>
                                <TabsTrigger
                                    value="account"
                                    className="w-full justify-start px-3 py-2 font-medium text-sm text-muted-foreground data-[state=active]:text-white data-[state=active]:bg-white/5 hover:bg-white/5 hover:text-white transition-colors rounded-md"
                                >
                                    <Lock className="mr-3 h-4 w-4" />
                                    Account
                                </TabsTrigger>
                            </TabsList>

                            <div className="mt-auto px-2">
                                <p className="text-[10px] text-muted-foreground uppercase tracking-wider font-semibold">Version 1.1.0</p>
                            </div>
                        </div>

                        <div className="flex-1 overflow-y-auto bg-[#0F1011]">
                            {/* Profile Tab */}
                            <TabsContent value="profile" className="mt-0 p-8 space-y-8 max-w-2xl mx-auto">
                                <div className="space-y-1">
                                    <h3 className="text-2xl font-semibold text-white">Profile</h3>
                                    <p className="text-sm text-muted-foreground">Manage your public profile and personal details.</p>
                                </div>

                                <div className="flex items-start gap-8 pb-8 border-b border-white/5">
                                    <div className="relative group">
                                        <Avatar className="h-24 w-24 border-4 border-[#0F1011] shadow-lg ring-1 ring-white/10">
                                            <AvatarImage src={avatarUrl} className="object-cover" />
                                            <AvatarFallback className="text-2xl bg-white/5 text-white/50">
                                                {fullName?.charAt(0) || user?.email?.charAt(0)}
                                            </AvatarFallback>
                                        </Avatar>
                                        <div
                                            className="absolute inset-0 flex items-center justify-center bg-black/60 rounded-full opacity-0 group-hover:opacity-100 transition-all duration-200 cursor-pointer backdrop-blur-sm"
                                            onClick={() => fileInputRef.current?.click()}
                                        >
                                            {uploading ? (
                                                <Loader2 className="h-8 w-8 text-white animate-spin" />
                                            ) : (
                                                <Camera className="h-8 w-8 text-white" />
                                            )}
                                        </div>
                                        <input
                                            type="file"
                                            ref={fileInputRef}
                                            className="hidden"
                                            accept="image/*"
                                            onChange={handleAvatarUpload}
                                            disabled={uploading}
                                        />
                                    </div>
                                    <div className="space-y-2 pt-2">
                                        <h4 className="font-medium text-white">Profile Picture</h4>
                                        <p className="text-xs text-muted-foreground max-w-[200px] leading-relaxed">
                                            Upload a new avatar. Recommended size 400x400px. JPG, PNG or GIF. Max 2MB.
                                        </p>
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            className="h-8 text-xs border-white/10 hover:bg-white/5 hover:text-white"
                                            onClick={() => fileInputRef.current?.click()}
                                        >
                                            Upload new picture
                                        </Button>
                                    </div>
                                </div>

                                <div className="space-y-6">
                                    <div className="grid gap-2">
                                        <Label htmlFor="username" className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Username</Label>
                                        <Input
                                            id="username"
                                            value={username}
                                            onChange={(e) => setUsername(e.target.value)}
                                            placeholder="username"
                                            className="bg-white/5 border-white/10 h-11 focus-visible:ring-offset-0 focus-visible:ring-1 focus-visible:ring-white/20"
                                        />
                                        <p className="text-[11px] text-muted-foreground">This is your public display name.</p>
                                    </div>

                                    <div className="grid gap-6 grid-cols-2">
                                        <div className="grid gap-2">
                                            <Label htmlFor="name" className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Full Name</Label>
                                            <Input
                                                id="name"
                                                value={fullName}
                                                onChange={(e) => setFullName(e.target.value)}
                                                placeholder="Your Name"
                                                className="bg-white/5 border-white/10 h-11 focus-visible:ring-offset-0 focus-visible:ring-1 focus-visible:ring-white/20"
                                            />
                                        </div>
                                        <div className="grid gap-2">
                                            <Label htmlFor="email" className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Email</Label>
                                            <Input
                                                id="email"
                                                value={user?.email || ""}
                                                disabled
                                                className="bg-white/5 border-white/10 opacity-50 h-11 cursor-not-allowed"
                                            />
                                        </div>
                                    </div>
                                </div>

                                <div className="flex justify-end pt-6 border-t border-white/5">
                                    <Button onClick={updateProfile} disabled={loading} className="min-w-[120px]">
                                        {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                                        Save Changes
                                    </Button>
                                </div>
                            </TabsContent>

                            {/* Preferences Tab */}
                            <TabsContent value="preferences" className="mt-0 p-8 space-y-8 max-w-2xl mx-auto">
                                <div className="space-y-1">
                                    <h3 className="text-2xl font-semibold text-white">Preferences</h3>
                                    <p className="text-sm text-muted-foreground">Customize your asset universe and dashboard experience.</p>
                                </div>

                                <div className="space-y-6">
                                    <div>
                                        <h4 className="font-medium text-white mb-4">Asset Universe</h4>
                                        <p className="text-sm text-muted-foreground mb-4">Select the exchanges you want to see data from.</p>

                                        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                                            {AVAILABLE_EXCHANGES.map((exchange) => (
                                                <div
                                                    key={exchange.id}
                                                    onClick={() => toggleExchange(exchange.id)}
                                                    className={cn(
                                                        "cursor-pointer rounded-lg border p-3 flex items-center justify-between transition-all duration-200",
                                                        preferredExchanges.includes(exchange.id)
                                                            ? "bg-white/10 border-white/20 text-white"
                                                            : "bg-white/[0.02] border-white/5 text-muted-foreground hover:bg-white/5 hover:text-white"
                                                    )}
                                                >
                                                    <span className="text-sm font-medium">{exchange.name}</span>
                                                    {preferredExchanges.includes(exchange.id) && (
                                                        <Check className="h-4 w-4 text-emerald-500" />
                                                    )}
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                </div>

                                <div className="flex justify-end pt-6 border-t border-white/5">
                                    <Button onClick={handleSavePreferences} disabled={loading} className="min-w-[120px]">
                                        {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                                        Save Preferences
                                    </Button>
                                </div>
                            </TabsContent>

                            {/* Billing Tab */}
                            <TabsContent value="billing" className="mt-0 p-8 space-y-8 max-w-2xl mx-auto">
                                <div className="space-y-1">
                                    <h3 className="text-2xl font-semibold text-white">Billing</h3>
                                    <p className="text-sm text-muted-foreground">Manage your subscription and payment methods.</p>
                                </div>

                                <div className="flex flex-col items-center justify-center py-12 text-center space-y-4 border border-dashed border-white/10 rounded-lg bg-white/[0.02]">
                                    <CreditCard className="h-12 w-12 text-muted-foreground/50" />
                                    <div className="space-y-2">
                                        <h4 className="font-medium text-white">No Active Subscription</h4>
                                        <p className="text-sm text-muted-foreground max-w-sm">
                                            You are currently on the free plan. Upgrade to access premium features and advanced analytics.
                                        </p>
                                    </div>
                                    <Button variant="secondary" className="mt-4">
                                        View Plans
                                    </Button>
                                </div>
                            </TabsContent>

                            {/* Account Tab */}
                            <TabsContent value="account" className="mt-0 p-8 space-y-8 max-w-2xl mx-auto">
                                <div className="space-y-1">
                                    <h3 className="text-2xl font-semibold text-white">Account Security</h3>
                                    <p className="text-sm text-muted-foreground">Manage your password and security settings.</p>
                                </div>

                                <div className="space-y-6">
                                    <div className="p-4 rounded-lg border border-white/5 bg-white/[0.02]">
                                        <h4 className="font-medium text-white mb-4">Change Password</h4>
                                        <form action={updatePassword} className="space-y-4">
                                            <div className="grid gap-2">
                                                <Label htmlFor="password">New Password</Label>
                                                <Input
                                                    id="password"
                                                    name="password"
                                                    type="password"
                                                    required
                                                    className="bg-white/5 border-white/10 h-10"
                                                />
                                            </div>
                                            <div className="grid gap-2">
                                                <Label htmlFor="confirmPassword">Confirm Password</Label>
                                                <Input
                                                    id="confirmPassword"
                                                    name="confirmPassword"
                                                    type="password"
                                                    required
                                                    className="bg-white/5 border-white/10 h-10"
                                                />
                                            </div>
                                            <div className="flex justify-end pt-2">
                                                <Button type="submit" variant="secondary">Update Password</Button>
                                            </div>
                                        </form>
                                    </div>

                                    <div className="pt-6 border-t border-white/5">
                                        <h4 className="text-red-500 font-medium mb-2">Danger Zone</h4>
                                        <p className="text-sm text-muted-foreground mb-4">
                                            Irreversible actions related to your account.
                                        </p>
                                        <div className="p-4 rounded-lg border border-red-500/20 bg-red-500/5 flex items-center justify-between">
                                            <div>
                                                <h5 className="text-white font-medium">Delete Account</h5>
                                                <p className="text-xs text-muted-foreground">Permanently delete your account and all data.</p>
                                            </div>
                                            <Button
                                                variant="destructive"
                                                size="sm"
                                                onClick={handleDeleteAccount}
                                                disabled={loading}
                                            >
                                                {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Delete Account"}
                                            </Button>
                                        </div>
                                    </div>
                                </div>
                            </TabsContent>
                        </div>
                    </Tabs>
                </div>
            </DialogContent>
        </Dialog>
    )
}
