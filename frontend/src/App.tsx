import { useAppState } from '@/hooks/useAppState'
import { ChatPanel } from './components/chat/ChatPanel'
import { MainPanel } from './components/main/MainPanel'
import { Sidebar } from './components/sidebar/Sidebar'
export default function App() {
  const { selectedVideoId, currentTime, setCurrentTime, selectVideo } = useAppState()

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background text-foreground">
      {/* Sidebar */}
      <aside className="w-72 min-w-72 border-r flex flex-col">
        <Sidebar
          selectedVideoId={selectedVideoId}
          onSelectVideo={selectVideo}
        />
      </aside>

      {/* Main Panel */}
      <main className="flex-1 flex flex-col overflow-hidden border-r">
        <MainPanel
          videoId={selectedVideoId}
          currentTime={currentTime}
          onTimeUpdate={setCurrentTime}
        />
      </main>

      {/* Chat Panel */}
      <aside className="w-96 min-w-96 flex flex-col">
        <ChatPanel videoId={selectedVideoId} />
      </aside>
    </div>
  )
}