import { NextResponse, type NextRequest } from "next/server";
import { createServerClient } from "@supabase/ssr";

export async function middleware(request: NextRequest) {
  let supabaseResponse = NextResponse.next({ request });

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll();
        },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value }) =>
            request.cookies.set(name, value),
          );
          supabaseResponse = NextResponse.next({ request });
          cookiesToSet.forEach(({ name, value, options }) =>
            supabaseResponse.cookies.set(name, value, options),
          );
        },
      },
    },
  );

  // Use getSession() instead of getUser() to avoid a network call to Supabase
  // on every navigation. getUser() can fail transiently when the tab is
  // backgrounded and resumed, causing spurious redirects to /login.
  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (!session) {
    const url = request.nextUrl.clone();
    const returnTo = request.nextUrl.pathname + request.nextUrl.search;
    url.pathname = "/login";
    if (returnTo && returnTo !== "/dashboard") {
      url.searchParams.set("next", returnTo);
    }
    return NextResponse.redirect(url);
  }

  return supabaseResponse;
}

export const config = {
  matcher: ["/dashboard/:path*", "/import/:path*", "/labels/:path*", "/artists/:path*"],
};
