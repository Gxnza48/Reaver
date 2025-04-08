import React from 'react';
import { Terminal, Shield, Lock, Cpu, Download, DiscIcon } from 'lucide-react';

function App() {
  return (
    <div className="min-h-screen bg-black text-purple-500 font-mono">
      {/* Hero Section */}
      <div className="relative">
        <div className="container mx-auto px-4 py-20">
          <div className="text-center max-w-3xl mx-auto">
            <div className="mb-6 inline-block">
              <Terminal className="h-16 w-16" />
            </div>
            <pre className="text-purple-500 font-bold mb-6 text-lg md:text-xl leading-none">
{` ___  ___  ___  _ _  ___  ___   ___           _ 
| . \\| __>| . || | || __>| . \\ |_ _|___  ___ | |
|   /| _> |   || ' || _> |   /  | |/ . \\/ . \\| |
|_\\_\\|___>|_|_||__/ |___>|_\\_\\  |_|\\___/\\___/|_|`}
            </pre>
            <p className="text-lg text-purple-400 mb-8 font-mono">
              [*] Pyton pyshing tool
            </p>
            <a
  href="/reaver.rar"
  download
  className="bg-transparent border-2 border-purple-500 hover:bg-purple-500/10 text-purple-500 font-mono py-3 px-8 transition-all duration-300 flex items-center gap-2 mx-auto group"
>
  <Download className="group-hover:animate-bounce" size={20} />
  ./download.rar
</a>


          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="container mx-auto px-4 py-20">
        <div className="max-w-3xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-8">
          {[
            { icon: Shield, title: "Penetration", desc: "[+] IP and geo tracker" },
            { icon: Lock, title: "Protection", desc: "[+] Real time listening for new victims" },
            { icon: Terminal, title: "CLI Interface", desc: "[+] Nice interface and easy use" },
            { icon: Cpu, title: "Integration", desc: "[+] pyinstaller (You do not have to install python to use these tool)" }
          ].map((feature, index) => (
            <div key={index} 
                 className="border border-purple-500/20 p-6 hover:border-purple-500/50 transition-all duration-300">
              <feature.icon className="text-purple-500 mb-4 h-6 w-6" />
              <h3 className="text-lg font-bold mb-2">{feature.title}</h3>
              <p className="text-purple-400/70 font-mono text-sm">{feature.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Terminal Preview */}
      <div className="container mx-auto px-4 py-10">
        <div className="max-w-3xl mx-auto">
          <div className="border border-purple-500/20 rounded bg-black p-4 font-mono text-sm">
            <p className="text-purple-500">&gt; ./reaver --init</p>
            <p className="text-purple-400/70">[*] Loading modules...</p>
            <p className="text-purple-400/70">[+] Tracking target</p>
            <p className="text-purple-400/70">[+] IP Adress: *.***.***.*</p>
            <p className="text-purple-500">&gt; _</p>
          </div>
        </div>
      </div>

      {/* Credits Section */}
      <footer className="container mx-auto px-4 py-8 border-t border-purple-500/20">
        <div className="flex items-center justify-center gap-2 text-purple-400/70 text-sm">
          <span>// discord:</span>
          <span className="text-purple-500">gxnza.48</span>
        </div>
      </footer>
    </div>
  );
}

export default App;