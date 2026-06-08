import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Layout } from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import LiveDetection from "./pages/LiveDetection";
import TrafficDetail from "./pages/TrafficDetail";
import BigScreen from "./pages/BigScreen";
import History from "./pages/History";
import ModelManagement from "./pages/ModelManagement";

export default function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/live" element={<LiveDetection />} />
          <Route path="/traffic/:id" element={<TrafficDetail />} />
          <Route path="/bigscreen" element={<BigScreen />} />
          <Route path="/history" element={<History />} />
          <Route path="/model" element={<ModelManagement />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}
