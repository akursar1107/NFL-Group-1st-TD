import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import '../styles/EditUsers.css';

interface User {
  id: number;
  username: string;
  display_name: string;
  email: string;
  is_active: boolean;
}

const EditUsers: React.FC = () => {
  const navigate = useNavigate();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [showNewUserForm, setShowNewUserForm] = useState(false);
  
  const [formData, setFormData] = useState({
    username: '',
    display_name: '',
    email: '',
    is_active: true
  });

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('http://localhost:5000/api/users/all');
      if (!response.ok) throw new Error('Failed to fetch users');
      const data = await response.json();
      setUsers(data.users);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    
    try {
      const response = await fetch('http://localhost:5000/api/users', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Failed to create user');
      
      setSuccess(`User "${formData.username}" created successfully!`);
      setFormData({ username: '', display_name: '', email: '', is_active: true });
      setShowNewUserForm(false);
      loadUsers();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleUpdateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingUser) return;
    
    setError(null);
    setSuccess(null);
    
    try {
      const response = await fetch(`http://localhost:5000/api/users/${editingUser.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Failed to update user');
      
      setSuccess(`User "${formData.username}" updated successfully!`);
      setEditingUser(null);
      setFormData({ username: '', display_name: '', email: '', is_active: true });
      loadUsers();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleDeleteUser = async (userId: number, username: string) => {
    if (!window.confirm(`Are you sure you want to delete user "${username}"? This will also delete all their picks.`)) {
      return;
    }
    
    setError(null);
    setSuccess(null);
    
    try {
      const response = await fetch(`http://localhost:5000/api/users/${userId}`, {
        method: 'DELETE'
      });
      
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Failed to delete user');
      
      setSuccess(`User "${username}" deleted successfully!`);
      loadUsers();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const startEdit = (user: User) => {
    setEditingUser(user);
    setFormData({
      username: user.username,
      display_name: user.display_name,
      email: user.email,
      is_active: user.is_active
    });
    setShowNewUserForm(false);
  };

  const cancelEdit = () => {
    setEditingUser(null);
    setShowNewUserForm(false);
    setFormData({ username: '', display_name: '', email: '', is_active: true });
  };

  return (
    <div className="edit-users-container">
      <div className="edit-users-header">
        <h1>👥 Manage Users</h1>
        <button onClick={() => navigate('/admin')} className="btn-back">
          ← Back to Admin
        </button>
      </div>

      {error && (
        <div className="message error-message">
          <strong>Error:</strong> {error}
        </div>
      )}

      {success && (
        <div className="message success-message">
          <strong>Success!</strong> {success}
        </div>
      )}

      {/* New User / Edit User Form */}
      {(showNewUserForm || editingUser) && (
        <div className="user-form-card">
          <h2>{editingUser ? 'Edit User' : 'Create New User'}</h2>
          <form onSubmit={editingUser ? handleUpdateUser : handleCreateUser}>
            <div className="form-group">
              <label>
                Username <span className="required">*</span>
              </label>
              <input
                type="text"
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                required
                placeholder="e.g., Phil"
              />
            </div>

            <div className="form-group">
              <label>
                Display Name <span className="required">*</span>
              </label>
              <input
                type="text"
                value={formData.display_name}
                onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
                required
                placeholder="e.g., Phil Johnson"
              />
            </div>

            <div className="form-group">
              <label>
                Email <span className="required">*</span>
              </label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                required
                placeholder="e.g., phil@example.com"
              />
            </div>

            <div className="form-group checkbox-group">
              <label>
                <input
                  type="checkbox"
                  checked={formData.is_active}
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                />
                <span>Active User</span>
              </label>
            </div>

            <div className="form-actions">
              <button type="button" onClick={cancelEdit} className="btn-cancel">
                Cancel
              </button>
              <button type="submit" className="btn-submit">
                {editingUser ? 'Update User' : 'Create User'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Add New User Button */}
      {!showNewUserForm && !editingUser && (
        <button
          onClick={() => setShowNewUserForm(true)}
          className="btn-add-user"
        >
          ➕ Add New User
        </button>
      )}

      {/* Users List */}
      <div className="users-list">
        <h2>All Users ({users.length})</h2>
        {loading ? (
          <p>Loading users...</p>
        ) : users.length === 0 ? (
          <p>No users found.</p>
        ) : (
          <table className="users-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Username</th>
                <th>Display Name</th>
                <th>Email</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id} className={!user.is_active ? 'inactive' : ''}>
                  <td>{user.id}</td>
                  <td>{user.username}</td>
                  <td>{user.display_name}</td>
                  <td>{user.email}</td>
                  <td>
                    <span className={`status-badge ${user.is_active ? 'active' : 'inactive'}`}>
                      {user.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="actions-cell">
                    <button
                      onClick={() => startEdit(user)}
                      className="btn-edit"
                      title="Edit user"
                    >
                      ✏️ Edit
                    </button>
                    <button
                      onClick={() => handleDeleteUser(user.id, user.username)}
                      className="btn-delete"
                      title="Delete user"
                    >
                      🗑️ Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default EditUsers;
