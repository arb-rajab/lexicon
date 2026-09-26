import { NextRequest } from "next/server";

import { handleCredentialsAuth } from "@/lib/auth-server";

export async function POST(request: NextRequest) {
  return handleCredentialsAuth(request, "/api/v1/auth/login", 200);
}
