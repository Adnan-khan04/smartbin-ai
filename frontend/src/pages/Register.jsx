import { Navigate } from 'react-router-dom';

// Register is now merged into the Login page — redirect there.
export default function Register() {
  return <Navigate to="/login" replace />;
}