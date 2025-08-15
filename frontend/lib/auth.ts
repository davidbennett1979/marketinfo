import { createClient } from '@/lib/supabase/client'

export interface AuthenticatedFetchOptions extends RequestInit {
  headers?: Record<string, string>
}

/**
 * Make an authenticated API request with JWT token from Supabase
 */
export async function authenticatedFetch(
  url: string, 
  options: AuthenticatedFetchOptions = {}
): Promise<Response> {
  const supabase = createClient()
  
  // Get current session and token
  const { data: { session }, error } = await supabase.auth.getSession()
  
  if (error) {
    throw new Error(`Auth error: ${error.message}`)
  }
  
  if (!session?.access_token) {
    throw new Error('No active session - user must be logged in')
  }
  
  // Add Authorization header with JWT token
  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${session.access_token}`,
    ...options.headers,
  }
  
  // Make the request with proper auth headers
  return fetch(url, {
    ...options,
    headers,
  })
}

/**
 * Get current user info from Supabase
 */
export async function getCurrentUser() {
  const supabase = createClient()
  const { data: { user }, error } = await supabase.auth.getUser()
  
  if (error) {
    throw new Error(`Failed to get user: ${error.message}`)
  }
  
  return user
}

/**
 * Check if user is authenticated
 */
export async function isAuthenticated(): Promise<boolean> {
  try {
    const user = await getCurrentUser()
    return !!user
  } catch {
    return false
  }
}