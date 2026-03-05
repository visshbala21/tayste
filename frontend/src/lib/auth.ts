import NextAuth from "next-auth";
import Google from "next-auth/providers/google";
import Credentials from "next-auth/providers/credentials";

const BACKEND_URL = process.env.INTERNAL_API_URL || "http://backend:8000";

export const { handlers, signIn, signOut, auth } = NextAuth({
  secret: process.env.AUTH_SECRET,
  providers: [
    Google({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),
    Credentials({
      name: "credentials",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) return null;

        try {
          const res = await fetch(`${BACKEND_URL}/api/auth/signin`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              email: credentials.email,
              password: credentials.password,
            }),
          });

          if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || "Invalid credentials");
          }

          const data = await res.json();
          return {
            id: data.user.id,
            email: data.user.email,
            name: data.user.name,
            image: data.user.picture,
            backendToken: data.access_token,
            backendUser: data.user,
          };
        } catch (e) {
          throw e;
        }
      },
    }),
  ],
  pages: {
    signIn: "/login",
  },
  callbacks: {
    async jwt({ token, account, user }) {
      // Google sign-in: exchange ID token for backend JWT
      if (account?.provider === "google" && account?.id_token) {
        try {
          const res = await fetch(`${BACKEND_URL}/api/auth/google`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ token: account.id_token }),
          });
          if (res.ok) {
            const data = await res.json();
            token.backendToken = data.access_token;
            token.backendUser = data.user;
          }
        } catch (e) {
          console.error("Backend auth exchange failed:", e);
        }
      }

      // Credentials sign-in: user object already has backend data
      if (account?.provider === "credentials" && user) {
        const u = user as { backendToken?: string; backendUser?: Record<string, unknown> };
        token.backendToken = u.backendToken as string;
        token.backendUser = u.backendUser as typeof token.backendUser;
      }

      return token;
    },
    async session({ session, token }) {
      session.backendToken = token.backendToken as string;
      session.backendUser = token.backendUser as typeof session.backendUser;
      return session;
    },
  },
});
