'use server'

import { createClient } from "@/lib/supabase/server"
import { createAdminClient } from "@/lib/supabase/admin"
import { revalidatePath } from "next/cache"
import { redirect } from "next/navigation"

export async function updatePreferences(preferences: string[]) {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) {
    throw new Error("Not authenticated")
  }

  const { error } = await supabase
    .from('profiles')
    .update({ preferred_exchanges: preferences })
    .eq('id', user.id)

  if (error) {
    throw new Error("Failed to update preferences")
  }

  revalidatePath('/dashboard')
}

export async function deleteAccount() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) {
    throw new Error("Not authenticated")
  }

  if (!process.env.SUPABASE_SERVICE_ROLE_KEY) {
    throw new Error("Server configuration error: Missing Service Role Key")
  }

  const adminAuthClient = createAdminClient()
  
  const { error } = await adminAuthClient.auth.admin.deleteUser(user.id)

  if (error) {
    console.error("Delete account error:", error)
    throw new Error("Failed to delete account")
  }

  await supabase.auth.signOut()
  redirect('/login')
}
