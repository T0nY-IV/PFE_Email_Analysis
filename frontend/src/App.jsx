import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Layout from './components/Layout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Reclamations from './pages/Reclamations';
import Demandes from './pages/Demandes';
import AllMails from './pages/AllMails';

// Protected Route Wrapper
const ProtectedRoute = ({ children, allowedRoles }) => {
  const { user, isAuthenticated } = useAuth();
  
  if (!isAuthenticated) return <Navigate to="/login" />;
  
  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to="/" />; // Redirect to dashboard if not authorized
  }

  return children;
};

const AppRoutes = () => {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      
      <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
        <Route index element={<Dashboard />} />
        
        <Route path="reclamations" element={
          <ProtectedRoute allowedRoles={['admin', 'responsable_reclamations']}>
            <Reclamations />
          </ProtectedRoute>
        } />
        
        <Route path="demandes" element={
          <ProtectedRoute allowedRoles={['admin', 'responsable_demandes']}>
            <Demandes />
          </ProtectedRoute>
        } />
        
        <Route path="all" element={
          <ProtectedRoute allowedRoles={['admin']}>
            <AllMails />
          </ProtectedRoute>
        } />
      </Route>
      
      <Route path="*" element={<Navigate to="/" />} />
    </Routes>
  );
};

const App = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
};

export default App;
