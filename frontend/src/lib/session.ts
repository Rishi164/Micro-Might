import { useQuery } from "@tanstack/react-query";
import { apiGet, apiPost } from "@/lib/api";
import { queryClient } from "@/lib/queryClient";
import type { SessionState, User } from "@/lib/types";

const SESSION_KEY = ["auth-session"] as const;

export function useSession() {
  return useQuery({
    queryKey: SESSION_KEY,
    queryFn: () => apiGet<SessionState>("/auth/session"),
    retry: false,
    staleTime: 60_000,
  });
}

export function beginSession(user: User) {
  queryClient.clear();
  queryClient.setQueryData<SessionState>(SESSION_KEY, { user });
}

export async function endSession() {
  try {
    await apiPost<void>("/auth/logout");
  } finally {
    queryClient.clear();
  }
}
