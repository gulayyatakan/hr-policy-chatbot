import Chatbot from '@/components/Chatbot';
// if you still want a logo, keep this import and replace the file later
import logo from '@/assets/images/logo.svg';

function App() {
  return (
    <div className="flex flex-col min-h-full w-full max-w-3xl mx-auto px-4">
      <header className="sticky top-0 shrink-0 z-20 bg-white">
        <div className="flex flex-col h-full w-full gap-1 pt-4 pb-2">
          {/* No external link, just the logo (optional) */}
          <div className="flex items-center gap-2">
            <img src={logo} className="w-10 h-10" alt="HR Policy Chatbot logo" />
            <h1 className="font-urbanist text-[1.65rem] font-semibold">
              HR Policy Chatbot
            </h1>
          </div>
          <p className="font-urbanist text-sm text-slate-500">
            Ask questions about vacation, celebrations, remote work, and other HR policies.
          </p>
        </div>
      </header>
      <Chatbot />
    </div>
  );
}

export default App;