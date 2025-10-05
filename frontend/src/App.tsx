import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Landing } from './pages/Landing';
import { StudentSession } from './pages/StudentSession';
import { AdminDashboard } from './pages/AdminDashboard';
import { SessionMonitoring } from './pages/SessionMonitoring';
import { useToast } from './hooks/useToast';
import { Toast, ToastContainer } from './components/Toast';

function App() {
  const { toasts, removeToast } = useToast();

  return (
    <Router>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/student/session" element={<StudentSession />} />
        <Route path="/admin/dashboard" element={<AdminDashboard />} />
        <Route path="/admin/session/:sessionId" element={<SessionMonitoring />} />
      </Routes>
      <ToastContainer>
        {toasts.map((toast) => (
          <Toast
            key={toast.id}
            message={toast.message}
            type={toast.type}
            onClose={() => removeToast(toast.id)}
          />
        ))}
      </ToastContainer>
    </Router>
  );
}

export default App;
