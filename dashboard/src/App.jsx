import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Overview from './pages/Overview';
import TrendingFactors from './pages/TrendingFactors';
import ContentStrategy from './pages/ContentStrategy';
import VideoExplorer from './pages/VideoExplorer';
import BreakoutVideos from './pages/BreakoutVideos';
import PipelineMonitor from './pages/PipelineMonitor';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Overview />} />
          <Route path="factors" element={<TrendingFactors />} />
          <Route path="strategy" element={<ContentStrategy />} />
          <Route path="explorer" element={<VideoExplorer />} />
          <Route path="breakouts" element={<BreakoutVideos />} />
          <Route path="pipeline" element={<PipelineMonitor />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
