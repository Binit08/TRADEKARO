import { Activity, Key, LogIn, Trash2 } from 'lucide-react';

interface BrokerListProps {
  brokers: any[];
  handleLogin: (broker: any) => void;
  handleSetActive: (id: number) => void;
  handleDelete: (id: number) => void;
  getBrokerDisplayName: (name: string) => string;
}

export function BrokerList({
  brokers,
  handleLogin,
  handleSetActive,
  handleDelete,
  getBrokerDisplayName
}: BrokerListProps) {
  return (
    <div className="bg-[#0f0f0f] border border-zinc-800/80 rounded-2xl p-6 md:p-8 h-full flex flex-col">
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 bg-zinc-800/50 rounded-xl border border-transparent">
            <Activity className="w-5 h-5 text-zinc-300" />
          </div>
          <div>
            <h2 className="text-xl font-semibold text-white">Active Integrations</h2>
            <p className="text-sm text-zinc-500 mt-0.5">Manage connected brokers</p>
          </div>
        </div>
        <div className="flex items-center gap-2 bg-zinc-900 border border-zinc-800 px-3 py-1.5 rounded-full">
          <span className="w-2 h-2 rounded-full bg-zinc-400" />
          <span className="text-xs font-medium text-zinc-300">{brokers.length} Linked</span>
        </div>
      </div>

      {brokers.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center text-center p-8 border border-dashed border-zinc-800 rounded-2xl bg-zinc-900/30">
          <div className="p-3 bg-zinc-800/50 rounded-xl mb-4">
            <Key className="w-8 h-8 text-zinc-500" />
          </div>
          <h3 className="text-lg font-medium text-white mb-1">No brokers connected</h3>
          <p className="text-zinc-500 text-sm max-w-sm">Add your credentials securely using the form to start receiving live market data.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {brokers.map((broker) => (
            <div key={broker.id} className="flex flex-col sm:flex-row items-start sm:items-center justify-between p-4 rounded-xl border bg-[#141414] border-zinc-800 transition-colors">
              <div className="flex items-center space-x-3 mb-4 sm:mb-0">
                <div className="relative flex items-center justify-center">
                  <div className={`w-2.5 h-2.5 rounded-full ${broker.is_active ? 'bg-zinc-200' : 'bg-zinc-700'}`} />
                </div>
                <div>
                  <h3 className="font-medium text-white text-base flex items-center gap-2">
                    {getBrokerDisplayName(broker.broker_name)}
                    {broker.is_active && <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-zinc-800 text-zinc-300 border border-zinc-700">Active</span>}
                  </h3>
                  <p className="text-xs text-zinc-500 mt-0.5">Added {new Date(broker.created_at).toLocaleDateString()}</p>
                </div>
              </div>
              
              <div className="flex items-center gap-2 w-full sm:w-auto">
                {broker.is_active && broker.broker_name === 'kite' && (
                  <button onClick={() => handleLogin(broker)} className="flex-1 sm:flex-none flex items-center justify-center gap-1.5 px-3 py-1.5 text-xs font-medium text-zinc-200 bg-zinc-800 hover:bg-zinc-700 rounded-lg transition-colors border border-zinc-700">
                    <LogIn className="w-3.5 h-3.5" />
                    <span>Login (Daily)</span>
                  </button>
                )}
                
                {!broker.is_active && (
                  <button onClick={() => handleSetActive(broker.id)} className="flex-1 sm:flex-none px-3 py-1.5 text-xs font-medium text-zinc-300 bg-zinc-800 hover:bg-zinc-700 rounded-lg transition-colors border border-zinc-700">
                    Set Active
                  </button>
                )}
                <button onClick={() => handleDelete(broker.id)} className="p-2 text-zinc-500 hover:text-white hover:bg-zinc-800 rounded-lg transition-colors" title="Remove Broker">
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
