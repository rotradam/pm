const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export interface Asset {
  ticker: string;
  name: string | null;
  category: string | null;
  subcategory: string | null;
  region: string | null;
  currency: string | null;
  exchange: string | null;
}

export interface AssetHistory {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export async function fetchAssets(
  search?: string,
  category?: string,
  limit: number = 100,
  offset: number = 0,
  region?: string,
  exchange?: string,
  sort_by?: string,
  sort_order?: "asc" | "desc"
): Promise<Asset[]> {
  const params = new URLSearchParams();
  if (search) params.append("search", search);
  if (category && category !== "All") params.append("category", category);
  if (region) params.append("region", region);
  if (exchange) params.append("exchange", exchange);
  if (sort_by) params.append("sort_by", sort_by);
  if (sort_order) params.append("sort_order", sort_order);
  
  params.append("limit", limit.toString());
  params.append("offset", offset.toString());

  const res = await fetch(`${API_URL}/assets?${params.toString()}`);
  if (!res.ok) throw new Error("Failed to fetch assets");
  return res.json();
}

export async function fetchAssetDetails(ticker: string): Promise<Asset> {
  const res = await fetch(`${API_URL}/assets/${ticker}`);
  if (!res.ok) throw new Error("Failed to fetch asset details");
  return res.json();
}

export async function fetchAssetHistory(ticker: string, period: string = "1y"): Promise<AssetHistory[]> {
  const res = await fetch(`${API_URL}/assets/${ticker}/history?period=${period}`);
  if (!res.ok) throw new Error("Failed to fetch asset history");
  return res.json();
}
