/** Server-only federation. No service-account key is stored on Vercel. */
import { getVercelOidcToken } from "@vercel/oidc";

export async function backendIdentityHeaders(): Promise<
  Record<string, string>
> {
  if (process.env.BACKEND_AUTH_MODE !== "gcp-oidc") return {};
  const provider = process.env.GCP_WORKLOAD_IDENTITY_PROVIDER;
  const account = process.env.GCP_INVOKER_SERVICE_ACCOUNT;
  const audience = process.env.BACKEND_URL;
  if (!provider || !account || !audience)
    throw new Error("Cloud identity configuration is incomplete");
  const subjectToken = await getVercelOidcToken();
  const exchange = await fetch("https://sts.googleapis.com/v1/token", {
    method: "POST",
    cache: "no-store",
    signal: AbortSignal.timeout(10000),
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      grantType: "urn:ietf:params:oauth:grant-type:token-exchange",
      audience: provider,
      scope: "https://www.googleapis.com/auth/cloud-platform",
      requestedTokenType: "urn:ietf:params:oauth:token-type:access_token",
      subjectToken,
      subjectTokenType: "urn:ietf:params:oauth:token-type:jwt",
    }),
  });
  if (!exchange.ok) throw new Error("Cloud identity exchange failed");
  const { access_token } = await exchange.json();
  if (!access_token) throw new Error("Missing federated access token");
  const identity = await fetch(
    `https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/${encodeURIComponent(account)}:generateIdToken`,
    {
      method: "POST",
      cache: "no-store",
      signal: AbortSignal.timeout(10000),
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${access_token}`,
      },
      body: JSON.stringify({
        audience: new URL(audience).origin,
        includeEmail: true,
      }),
    },
  );
  if (!identity.ok) throw new Error("Cloud invocation identity failed");
  const { token } = await identity.json();
  if (!token) throw new Error("Missing invocation token");
  return { Authorization: `Bearer ${token}` };
}
