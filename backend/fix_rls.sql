-- SQL to fix RLS policy for development
-- Execute this in your Supabase SQL editor

-- Option 1: Temporarily disable RLS for development
-- ALTER TABLE public.watchlists DISABLE ROW LEVEL SECURITY;

-- Option 2: Create a more permissive policy for development
DROP POLICY IF EXISTS "Allow all operations for development" ON public.watchlists;
CREATE POLICY "Allow all operations for development" ON public.watchlists
    FOR ALL 
    USING (true)
    WITH CHECK (true);

-- Option 3: If you want to keep user isolation but allow anon access
-- DROP POLICY IF EXISTS "Users can only access their own watchlist items" ON public.watchlists;
-- CREATE POLICY "Users can access their own items or anon can access all" ON public.watchlists
--     FOR ALL 
--     USING (auth.uid() = user_id OR auth.role() = 'anon')
--     WITH CHECK (auth.uid() = user_id OR auth.role() = 'anon');

-- Check current policies
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual, with_check
FROM pg_policies 
WHERE tablename = 'watchlists';