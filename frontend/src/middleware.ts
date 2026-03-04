export { auth as middleware } from "@/lib/auth";

export const config = {
  matcher: ["/dashboard/:path*", "/import/:path*", "/labels/:path*", "/artists/:path*"],
};
