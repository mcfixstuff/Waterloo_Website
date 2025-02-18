# COSC-4353-Group-Project
Welcome to the official repository for Team Waterloo's project!

## Project Overview
This project is a **user management system**

## Screenshots

Here are some screenshots of the project:

### Screenshot 1
![Screenshot1](static/screenshots/Screenshot1.png)

- This is the **Login Page** where users initiate authentication.
- Users must click the **"Login with Microsoft"** button.
- Clicking this button redirects users to **Microsoft's authentication system** for secure login.

### Screenshot 2
![Screenshot2](static/screenshots/Screenshot2.png)

- After clicking **"Login with Microsoft,"** users are taken to **Microsoft’s authentication page**.
- Users must choose which Microsoft account they want to log in with.
- This step ensures secure and authorized access using OAuth authentication.

### Screenshot 3
![Screenshot3](static/screenshots/Screenshot3.png)

- Once authentication is successful, Microsoft redirects the user to the **Admin Dashboard**.
- The **superuser** has control over user management.
- Superusers can:
- Disable users.
- Assign roles such as **Superuser, Manager, or Common User**.
- This dashboard provides complete control over user access and permissions.

### Screenshot 4
![Screenshot3](static/screenshots/Screenshot4.png)

- This flowchart visually represents the **Admin Dashboard's full authentication and user management flow**.
- It starts with a user visiting `/admin/login/` and clicking the **"Login with Microsoft"** button.
- The system:
  1. Redirects the user to **Microsoft OAuth**.
  2. Microsoft authenticates the user and returns an **access token**.
  3. The system fetches **user details** and stores the token & email in the session.
  4. Users are redirected to the **Admin Dashboard**.
  5. Superusers can **toggle user status** or **change user roles**.
  6. Logout clears the session and redirects back to login.
- This diagram provides a **clear overview of how authentication and user role management work** in the system.
