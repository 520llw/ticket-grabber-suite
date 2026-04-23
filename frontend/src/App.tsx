import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import TaskList from './pages/TaskList';
import TaskNew from './pages/TaskNew';
import TaskDetail from './pages/TaskDetail';
import Settings from './pages/Settings';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/tasks" element={<TaskList />} />
          <Route path="/tasks/new" element={<TaskNew />} />
          <Route path="/tasks/:id" element={<TaskDetail />} />
          <Route path="/settings" element={<Settings />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
