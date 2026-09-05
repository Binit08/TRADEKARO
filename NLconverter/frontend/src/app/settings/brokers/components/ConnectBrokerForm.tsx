import { ChevronRight, RefreshCw, Link as LinkIcon } from 'lucide-react';

interface ConnectBrokerFormProps {
  selectedBroker: string;
  setSelectedBroker: (b: string) => void;
  credentials: any;
  setCredentials: (c: any) => void;
  isConnecting: boolean;
  handleConnect: (e: React.FormEvent) => void;
}

export function ConnectBrokerForm({ 
  selectedBroker, setSelectedBroker, 
  credentials, setCredentials, 
  isConnecting, handleConnect 
}: ConnectBrokerFormProps) {
  return (
    <div className="bg-[#0f0f0f] border border-zinc-800/80 rounded-2xl p-6 md:p-8">
      <div className="flex items-center space-x-3 mb-8">
        <div className="p-2.5 bg-zinc-800/50 rounded-xl">
          <LinkIcon className="w-5 h-5 text-zinc-300" />
        </div>
        <div>
          <h2 className="text-xl font-semibold text-white">Connect Broker</h2>
          <p className="text-sm text-zinc-500 mt-0.5">API access configuration</p>
        </div>
      </div>

      <form onSubmit={handleConnect} className="space-y-6">
        <div className="space-y-2">
          <label className="text-sm font-medium text-zinc-300 ml-1">Platform</label>
          <div className="relative">
            <select 
              value={selectedBroker}
              onChange={(e) => setSelectedBroker(e.target.value)}
              className="w-full bg-[#141414] border border-zinc-800 rounded-xl px-4 py-3 appearance-none outline-none focus:border-zinc-500 focus:ring-1 focus:ring-zinc-500 transition-colors text-white shadow-sm"
            >
              <option value="kite">Zerodha Kite</option>
              <option value="upstox">Upstox</option>
              <option value="dhan">Dhan</option>
            </select>
            <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-zinc-500">
              <ChevronRight className="w-4 h-4 rotate-90" />
            </div>
          </div>
        </div>

        <div className="space-y-5">
          {(selectedBroker === 'kite' || selectedBroker === 'upstox') && (
            <>
              <div className="space-y-2">
                <label className="text-sm font-medium text-zinc-300 ml-1">API Key</label>
                <input type="text" required
                  value={credentials.api_key} onChange={e => setCredentials({...credentials, api_key: e.target.value})}
                  className="w-full bg-[#141414] border border-zinc-800 rounded-xl px-4 py-3 outline-none focus:border-zinc-500 focus:ring-1 focus:ring-zinc-500 transition-colors text-white shadow-sm" 
                  placeholder={selectedBroker === 'kite' ? "enxxxxx..." : ""} />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-zinc-300 ml-1">API Secret</label>
                <input type="password" required
                  value={credentials.api_secret} onChange={e => setCredentials({...credentials, api_secret: e.target.value})}
                  className="w-full bg-[#141414] border border-zinc-800 rounded-xl px-4 py-3 outline-none focus:border-zinc-500 focus:ring-1 focus:ring-zinc-500 transition-colors text-white shadow-sm" 
                  placeholder={selectedBroker === 'kite' ? "••••••••••••••••" : ""} />
              </div>
            </>
          )}

          {selectedBroker === 'dhan' && (
            <>
              <div className="space-y-2">
                <label className="text-sm font-medium text-zinc-300 ml-1">Client ID</label>
                <input type="text" required
                  value={credentials.client_id} onChange={e => setCredentials({...credentials, client_id: e.target.value})}
                  className="w-full bg-[#141414] border border-zinc-800 rounded-xl px-4 py-3 outline-none focus:border-zinc-500 focus:ring-1 focus:ring-zinc-500 transition-colors text-white shadow-sm" />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-zinc-300 ml-1">Access Token</label>
                <input type="password" required
                  value={credentials.access_token} onChange={e => setCredentials({...credentials, access_token: e.target.value})}
                  className="w-full bg-[#141414] border border-zinc-800 rounded-xl px-4 py-3 outline-none focus:border-zinc-500 focus:ring-1 focus:ring-zinc-500 transition-colors text-white shadow-sm" />
              </div>
            </>
          )}
        </div>

        <div className="pt-2">
          <button type="submit" disabled={isConnecting} className="w-full flex justify-center items-center py-3.5 px-4 font-semibold rounded-xl text-black bg-zinc-100 hover:bg-white focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-[#050505] focus:ring-zinc-400 disabled:opacity-70 transition-colors shadow-sm">
            {isConnecting ? (
              <RefreshCw className="w-5 h-5 animate-spin" />
            ) : (
              <span>Secure Connect</span>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
