import React, { useEffect, useState } from "react";

interface User {
  _id: string;
  email: string;
  name?: string;
  role: "admin" | "pending";
  createdAt?: string;
  lastLogin?: string;
}

const ManageAdmins: React.FC = () => {
  const [pendingUsers, setPendingUsers] = useState<User[]>([]);
  const [adminUsers, setAdminUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/admin-users");
      const data = await res.json();
      setPendingUsers(data.pending || []);
      setAdminUsers(data.admins || []);
    } catch (err) {
      console.error("Failed to fetch users", err);
    }
    setLoading(false);
  };

  const handleApprove = async (id: string) => {
    await fetch(`/api/admin-users/${id}/approve`, { method: "PATCH" });
    fetchUsers();
  };

  const handleDeny = async (id: string) => {
    await fetch(`/api/admin-users/${id}`, { method: "DELETE" });
    fetchUsers();
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  return (
    <div className="p-4 border rounded shadow">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold">Admin Request</h2>
        <button
          onClick={fetchUsers}
          className="bg-yellow-500 hover:bg-yellow-600 text-white px-4 py-2 rounded"
        >
          Refresh
        </button>
      </div>

      {loading ? (
        <p>Loading...</p>
      ) : (
        <>
          <div className="mb-4">
            <h3 className="text-lg font-semibold mb-2">Pending Approval</h3>
            {pendingUsers.length > 0 ? (
              <div className="space-y-2">
                {pendingUsers.map((user) => (
                  <div
                    key={user._id}
                    className="border p-3 rounded flex justify-between items-center bg-gray-50"
                  >
                    <span>
                      {user.name || "Unnamed"} — {user.email}
                    </span>
                    <div className="space-x-2">
                      <button
                        onClick={() => handleApprove(user._id)}
                        className="bg-green-500 hover:bg-green-600 text-white px-3 py-1 rounded"
                      >
                        Approve
                      </button>
                      <button
                        onClick={() => handleDeny(user._id)}
                        className="bg-red-500 hover:bg-red-600 text-white px-3 py-1 rounded"
                      >
                        Deny
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p>No pending users.</p>
            )}
          </div>

          <div>
            <h3 className="text-lg font-semibold mb-2">Approved Admins</h3>
            {adminUsers.length > 0 ? (
              <div className="space-y-2">
                {adminUsers.map((user) => (
                  <div
                    key={user._id}
                    className="border p-3 rounded bg-white shadow-sm"
                  >
                    {user.name || "Unnamed"} — {user.email}
                  </div>
                ))}
              </div>
            ) : (
              <p>No admins found.</p>
            )}
          </div>
        </>
      )}
    </div>
  );
};

export default ManageAdmins;
