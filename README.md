# COSC-4353-Group-Project
Welcome to the official repository for Team Waterloo's project!

## Project Overview
This project is a **user management system**


### ER MODEL FOR DATABASE
![Screenshot1](static/screenshots/Screenshot_ERModel_FOR_DATABASE.png)

## Screenshots

### Screenshot 1
![Screenshot1](static/screenshots/Screenshot1.png)

- This is the **Login Page** where users are prompted to log in with Microsoft.
- The system uses Azure for authentication, which then opens the Microsoft portal for secure sign-in.

### Screenshot 2
![Screenshot2](static/screenshots/Screenshot2.png)

- Here, the Microsoft portal is displayed.
- Users input their credentials to authenticate via Microsoft’s secure OAuth system.

### Screenshot 3
![Screenshot3](static/screenshots/Screenshot3.png)

- After authentication, users are redirected to the **Dashboard**.
- In this view, **superusers** and **managers** can manage user roles, disable users, and promote user levels.

### Screenshot 4
![Screenshot4](static/screenshots/Screenshot4.png)

- This is the **Selected Applications** section accessed from the navigation bar.
- Users can submit applications here; however, they must first upload a signature image.
- Without uploading a signature, users cannot proceed with their application.

### Screenshot 5
![Screenshot5](static/screenshots/Screenshot5.png)

- This screen displays the user’s signature.
- A quotation placeholder was used during testing, but it shows how the uploaded signature will appear in the system.

### Screenshot 6
![Screenshot6](static/screenshots/Screenshot6.png)

- In this step, users choose which application form they wish to apply for.

### Screenshot 7
![Screenshot7](static/screenshots/Screenshot7.png)

- After selecting a form, the system opens the application form.
- The user’s name is automatically pulled from the database, and the user fills in the remaining details.

### Screenshot 8
![Screenshot8](static/screenshots/Screenshot8.png)

- This view shows an image pulled from the user table in the database.
- Users are given two options: **Submit** the application or **Save as Draft**.

### Screenshot 9
![Screenshot9](static/screenshots/Screenshot9.png)

- Once the application is successfully submitted, it appears in the **My Application** section.
- Details include statuses such as **Pending**, **Returned**, **Approved**, or **Draft**.
- Additional actions include an eye button for viewing and a PDF icon for downloading the application.

### Screenshot 10
![Screenshot10](static/screenshots/Screenshot10.png)

- This is the **Application Approvals** section from the navigation bar.
- Accessible only to superusers and managers, this view allows for application approval, return, viewing, and PDF downloads.

### Screenshot 11
![Screenshot11](static/screenshots/Screenshot11.png)

- When an application is returned, this screen allows the user to send a message back, explaining why it was returned.

### Screenshot 12
![Screenshot12](static/screenshots/Screenshot12.png)

- This screen is dedicated to **Viewing an Application** in detail.

### Screenshot 13
![Screenshot13](static/screenshots/Screenshot13.png)

- This view shows both approved and disapproved applications.
- It also displays recent activity along with key metrics at the top: total applications for today, and counts of pending, approved, and returned applications.

### Screenshot 14
![Screenshot14](static/screenshots/Screenshot14.png)

- Back in the **My Application** section, this screen shows the approved and returned applications.
- Returned applications include an **Edit and Resubmit** button for further action.