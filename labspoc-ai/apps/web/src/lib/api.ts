const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
export async function api<T>(path:string, init?:RequestInit):Promise<T>{
  const r=await fetch(`${API}${path}`,{...init,headers:{...(init?.headers||{})}});
  if(!r.ok){const body=await r.json().catch(()=>({detail:r.statusText}));throw new Error(body.detail||"Request failed")}
  return r.json();
}
export { API };
