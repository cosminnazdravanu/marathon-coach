import { useState, useRef, useCallback } from 'react';
import CalendarGrid from './components/CalendarGrid';

export default function App() {
  const [activeMenu, setActiveMenu] = useState('training');
  
  // Pixel widths for panels
  const [leftWidth, setLeftWidth] = useState(200);
  const [rightWidth, setRightWidth] = useState(200);
  // Collapsed state
  const [leftCollapsed, setLeftCollapsed] = useState(false);
  const [rightCollapsed, setRightCollapsed] = useState(false);
  
  // Drag data ref
  const dragData = useRef({ startX: 0, startLeft: 0, startRight: 0, side: null });

  const onMouseDown = useCallback((side) => (e) => {
    e.preventDefault();
    if ((side === 'left' && leftCollapsed) || (side === 'right' && rightCollapsed)) {
      return;
    }
    dragData.current = {
      side,
      startX: e.clientX,
      startLeft: leftWidth,
      startRight: rightWidth,
    };
    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', onMouseUp);
  }, [leftWidth, rightWidth, leftCollapsed, rightCollapsed]);

  const onMouseMove = useCallback((e) => {
    const { side, startX, startLeft, startRight } = dragData.current;
    const dx = e.clientX - startX;
    if (side === 'left') {
      setLeftWidth(Math.min(Math.max(startLeft + dx, 50), 350));
    } else {
      setRightWidth(Math.min(Math.max(startRight - dx, 50), 350));
    }
  }, []);

  const onMouseUp = useCallback(() => {
    document.removeEventListener('mousemove', onMouseMove);
    document.removeEventListener('mouseup', onMouseUp);
  }, [onMouseMove]);

  const renderContent = () => {
    switch (activeMenu) {
      case 'training': return <CalendarGrid />;
      case 'stats':    return <div>Stats Placeholder</div>;
      case 'settings': return <div>Settings Placeholder</div>;
      default:         return <div>Select an option</div>;
    }
  };

  return (
    <div className="h-screen flex flex-col bg-gray-100">
      {/* Top Menu */}
      <div className="h-[40px] mt-1 flex items-center justify-center bg-white shadow-md"> {/* outline outline-gray-600 */}
        <button onClick={() => setActiveMenu('training')}  className="px-4 mx-2 rounded hover:bg-gray-200">🏃‍♂️ Training</button><div className="text-gray-300">|</div>
        <button onClick={() => setActiveMenu('stats')}     className="px-4 mx-2 rounded hover:bg-gray-200">📈 Stats</button><div className="text-gray-300">|</div>
        <button onClick={() => setActiveMenu('settings')}  className="px-4 mx-2 rounded hover:bg-gray-200">⚙️ Settings</button>
      </div>

      {/* Bottom Section */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left Panel */}
        <div
          className="relative bg-white p-2 overflow-auto border-r border-gray-300
                     transition-all duration-300 ease-in-out"
          style={{ width: leftCollapsed ? 40 : leftWidth }}
        >
          <div className={`transition-opacity duration-200 ease-in-out
                         ${leftCollapsed ? 'opacity-0 pointer-events-none' : 'opacity-100'}`}>
            <h2 className="text-xl font-semibold mb-4">Left Container</h2>
            <div className="text-gray-500">Future left-side components</div>
          </div>
          <button
            onClick={() => setLeftCollapsed((f) => !f)}
            className="absolute top-2 right-0 -mr-2 w-6 h-6 flex items-center justify-center
                       bg-gray-200 rounded-l hover:bg-gray-300 transition"
            title={leftCollapsed ? 'Expand' : 'Collapse'}
          >
            {leftCollapsed ? '»' : '«'}
          </button>
        </div>

        {/* Divider */}
        <div
          onMouseDown={onMouseDown('left')}
          className="cursor-ew-resize bg-gray-300 hover:bg-blue-400 transition duration-200"
          style={{ width: 2 }}
        />

        {/* Center Panel */}
        <div className="flex-1 bg-gray-50 p-2 overflow-auto">
          {renderContent()}
        </div>

        {/* Divider */}
        <div
          onMouseDown={onMouseDown('right')}
          className="cursor-ew-resize bg-gray-300 hover:bg-blue-400 transition duration-200"
          style={{ width: 2 }}
        />

        {/* Right Panel */}
        <div
          className="relative bg-white p-2 overflow-auto border-l border-gray-300
                     transition-all duration-300 ease-in-out"
          style={{ width: rightCollapsed ? 40 : rightWidth }}
        >
          <div className={`transition-opacity duration-200 ease-in-out
                         ${rightCollapsed ? 'opacity-0 pointer-events-none' : 'opacity-100'}`}>
            <h2 className="text-xl font-semibold mb-4">Right Container</h2>
            <div className="text-gray-500">Future right-side components</div>
          </div>
          <button
            onClick={() => setRightCollapsed((f) => !f)}
            className="absolute top-2 left-0 -ml-2 w-6 h-6 flex items-center justify-center
                       bg-gray-200 rounded-r hover:bg-gray-300 transition"
            title={rightCollapsed ? 'Expand' : 'Collapse'}
          >
            {rightCollapsed ? '«' : '»'}
          </button>
        </div>
      </div>
    </div>
  );
}
