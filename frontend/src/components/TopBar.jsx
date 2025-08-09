import UserMenu from "./UserMenu";

export default function TopBar({ activeMenu, setActiveMenu }) {
  return (
    <header className="sticky top-0 z-40 bg-white/80 backdrop-blur border-b">
      <div className="grid grid-cols-3 items-center h-10 px-4">
        {/* left spacer (keeps center truly centered) */}
        <div />

        {/* center: nav */}
        <nav className="justify-self-center flex items-center">
          <button onClick={() => setActiveMenu('training')}  className="px-4 mx-2 rounded hover:bg-gray-200">🏃‍♂️ Training</button>
          <div className="text-gray-300">|</div>
          <button onClick={() => setActiveMenu('stats')}     className="px-4 mx-2 rounded hover:bg-gray-200">📈 Stats</button>
          <div className="text-gray-300">|</div>
          <button onClick={() => setActiveMenu('settings')}  className="px-4 mx-2 rounded hover:bg-gray-200">⚙️ Settings</button>
        </nav>

        {/* right: user */}
        <div className="justify-self-end">
          <UserMenu onSettings={() => setActiveMenu('settings')} />
        </div>
      </div>
    </header>
  );
}
