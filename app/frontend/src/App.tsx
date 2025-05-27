import { useState } from 'react';
import { Flow } from './components/Flow';
import { Layout } from './components/Layout';
import { Portfolio } from './components/Portfolio';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';

export default function App() {
  const [showLeftSidebar] = useState(false);
  const [showRightSidebar] = useState(false);

  return (
    <Layout
      leftSidebar={showLeftSidebar ? <div className="p-4 text-white">Left Sidebar Content</div> : undefined}
      rightSidebar={showRightSidebar ? <div className="p-4 text-white">Right Sidebar Content</div> : undefined}
    >
      <div className="h-full w-full">
        <Tabs defaultValue="portfolio" className="h-full">
          <div className="border-b">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="portfolio">Portfolio Monitor</TabsTrigger>
              <TabsTrigger value="agents">AI Agents Flow</TabsTrigger>
            </TabsList>
          </div>
          <TabsContent value="portfolio" className="h-full p-6">
            <Portfolio />
          </TabsContent>
          <TabsContent value="agents" className="h-full">
            <Flow />
          </TabsContent>
        </Tabs>
      </div>
    </Layout>
  );
}
