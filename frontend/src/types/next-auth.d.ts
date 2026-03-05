import "next-auth";

declare module "next-auth" {
  interface Session {
    backendToken?: string;
    backendUser?: {
      id: string;
      email: string;
      name: string | null;
      picture: string | null;
      email_verified: boolean;
      auth_provider: string;
    };
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    backendToken?: string;
    backendUser?: {
      id: string;
      email: string;
      name: string | null;
      picture: string | null;
      email_verified: boolean;
      auth_provider: string;
    };
  }
}
