document.addEventListener("DOMContentLoaded", function() {
  fetchUsers(); // Load users when page loads
});

/*
function fetchUsers() {
  // MOCK DATA - Replace this with an actual API call later
  const users = [
      //{ id: 1, name: "Alice", email: "alice@example.com", role: "User", status: "Active" },
      //{ id: 2, name: "Bob", email: "bob@example.com", role: "Admin", status: "Active" }
  ];

  const userTable = document.getElementById("user-list");
  userTable.innerHTML = ""; // Clear table before inserting new data

  users.forEach(user => {
      const row = document.createElement("tr");

      row.innerHTML = `
          <td>${user.id}</td>
          <td>${user.name}</td>
          <td>${user.email}</td>
          <td>
              <select onchange="updateUserRole(${user.id}, this.value)">
                  <option value="User" ${user.role === "User" ? "selected" : ""}>User</option>
                  <option value="Admin" ${user.role === "Admin" ? "selected" : ""}>Admin</option>
              </select>
          </td>
          <td>${user.status}</td>
          <td>
              <button onclick="toggleUserStatus(${user.id}, '${user.status}')">
                  ${user.status === "Active" ? "Deactivate" : "Reactivate"}
              </button>
              <button onclick="deleteUser(${user.id})" class="delete-btn">Delete</button>
          </td>
      `;
      userTable.appendChild(row);
  });
} */

document.addEventListener('DOMContentLoaded', function() {
    var toggleButton = document.getElementById('toggle-add-user');
    if (toggleButton) {
        toggleButton.addEventListener('click', function() {
            var formDiv = document.getElementById('add-user-form');
            // Check current display state; default to 'none' if not set
            if (formDiv.style.display === 'none' || formDiv.style.display === '') {
                formDiv.style.display = 'block';
            } else {
                formDiv.style.display = 'none';
            }
        });
    }
});

function updateUserRole(userId, newRole) {
  console.log(`Updating role for User ${userId} to ${newRole}`);
  alert(`User role updated to ${newRole}`);
}

function toggleUserStatus(userId, currentStatus) {
  const newStatus = currentStatus === "Active" ? "Deactivated" : "Active";
  console.log(`Toggling status for User ${userId} to ${newStatus}`);
  alert(`User status changed to ${newStatus}`);
}

function deleteUser(userId) {
  if (!confirm("Are you sure you want to delete this user?")) return;
  console.log(`Deleting user ${userId}`);
  alert("User deleted successfully");
}
