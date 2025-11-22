'use server'

import { revalidatePath } from 'next/cache'
import { redirect } from 'next/navigation'

import { createClient } from '@/lib/supabase/server'

export async function login(formData: FormData) {
  const supabase = await createClient()

  const loginIdentifier = formData.get('email') as string
  const password = formData.get('password') as string

  let email = loginIdentifier

  // Check if input is not an email (simple check)
  if (!loginIdentifier.includes('@')) {
    // Lookup email by username
    const { data: profile } = await supabase
      .from('profiles')
      .select('email')
      .eq('username', loginIdentifier)
      .single()
    
    if (profile && profile.email) {
      email = profile.email
    } else {
      // If username not found, we can either fail here or let signInWithPassword fail
      // Letting it fail with the username as email will result in invalid login, which is fine
    }
  }

  const { error } = await supabase.auth.signInWithPassword({
    email,
    password,
  })

  if (error) {
    console.error(error)
    // We should probably return the error to the client instead of redirecting
    // But for now, keeping existing behavior but maybe we can improve it later
    redirect('/login?error=Invalid login credentials')
  }

  revalidatePath('/', 'layout')
  redirect('/dashboard')
}

export async function signup(formData: FormData) {
  const supabase = await createClient()

  const email = formData.get('email') as string
  const password = formData.get('password') as string
  const fullName = formData.get('fullName') as string

  const { error } = await supabase.auth.signUp({
    email,
    password,
    options: {
      emailRedirectTo: `${process.env.NEXT_PUBLIC_BASE_URL || 'http://localhost:3000'}/auth/callback`,
      data: {
        full_name: fullName,
      }
    },
  })

  if (error) {
    console.error(error)
    redirect('/login?error=Signup failed')
  }

  revalidatePath('/', 'layout')
  redirect('/dashboard')
}

export async function signOut() {
  const supabase = await createClient()
  await supabase.auth.signOut()
  revalidatePath('/', 'layout')
  redirect('/login')
}

export async function resetPassword(email: string) {
  const supabase = await createClient()
  
  const { error } = await supabase.auth.resetPasswordForEmail(email, {
    redirectTo: `${process.env.NEXT_PUBLIC_BASE_URL || 'http://localhost:3000'}/auth/callback?next=/login/reset-password`,
  })

  if (error) {
    console.error(error)
    throw error
  }
}

export async function updatePassword(password: string) {
  const supabase = await createClient()
  
  const { error } = await supabase.auth.updateUser({
    password: password
  })

  if (error) {
    console.error(error)
    throw error
  }

  revalidatePath('/', 'layout')
  redirect('/dashboard')
}
