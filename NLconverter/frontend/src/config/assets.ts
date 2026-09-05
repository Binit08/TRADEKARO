export interface AssetOption {
  value: string;
  label: string;
}

export interface AssetsMetadata {
  indices: AssetOption[];
  stocks: AssetOption[];
  timeframes: string[];
}

const FALLBACK_METADATA: AssetsMetadata = {
  indices: [
    { value: '^NSEI', label: 'NIFTY 50' },
    { value: '^NSEBANK', label: 'BANK NIFTY' },
  ],
  stocks: [
    { value: 'AAPL', label: 'Apple Inc.' },
    { value: 'RELIANCE.NS', label: 'Reliance Industries Ltd' },
    { value: 'TCS.NS', label: 'Tata Consultancy Services Ltd' },
    { value: 'HDFCBANK.NS', label: 'HDFC Bank Ltd' },
  ],
  timeframes: ['1d', '1wk', '1mo'],
};

export const fetchAssetsMetadata = async (): Promise<AssetsMetadata> => {
  try {
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/metadata/assets`);
    if (!response.ok) {
      throw new Error('Failed to fetch asset metadata');
    }
    const data = await response.json();
    return data;
  } catch (error) {
    console.warn('Using fallback asset metadata due to fetch failure:', error);
    return FALLBACK_METADATA;
  }
};
