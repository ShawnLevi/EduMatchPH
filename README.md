 🎓 Scholarship Matching System

An AI-powered scholarship matching system designed to help students discover scholarship opportunities that match their academic profile, skills, and qualifications.

---

 📌 Project Overview

This project is a group software engineering and data science project that aims to make finding suitable scholarships easier for students.

The system will allow students to provide information about their academic background, skills, and other relevant information. The system will then analyze the student's profile and recommend scholarship opportunities that best match their qualifications.

---

 👥 Team Git Workflow

To keep the project organized and prevent unfinished code from breaking the main project, **DO NOT directly push to `main`.**

 Our basic workflow:

```text
main
 │
 ├── Your Feature Branch
 │       ↓
 │    Work & Commit
 │       ↓
 │    Push Branch
 │       ↓
 │   Pull Request
 │       ↓
 │     Review
 │       ↓
 └──── MERGE → main
```

 Important Rule

> 🚨 **Never push directly to `main`.**

Always create or use your own feature branch.

---

 🌿 Branches

Branches allow everyone to work on different parts of the project without immediately changing the main code.

 Example

```text
main
│
├── login-system
├── student-profile
├── scholarship-database
├── recommendation-system
└── frontend-dashboard
```

Try to name your branch according to the feature you are working on.

 Good branch names

```text
login-system
student-profile
scholarship-search
recommendation-model
database-setup
frontend-dashboard
```

 Avoid names like

```text
mybranch
test
stuff
new
final
final-final
please-work
```

---

 💻 Basic Git Commands

You don't need to memorize everything. These are the commands you'll use most often.

 Clone the repository

Do this once when you first download the project:

```bash
git clone <repository-url>
```

Then enter the project folder:

```bash
cd Scholarship-Matching-System
```

---

 Check your current branch

```bash
git branch
```

The branch with `*` is your current branch.

Example:

```text
* student-profile
  main
```

---

 Create a new branch

```bash
git switch -c <branch-name>
```

Example:

```bash
git switch -c student-profile
```

---

 Switch branches

```bash
git switch <branch-name>
```

Example:

```bash
git switch main
```

or:

```bash
git switch student-profile
```

---

 Get the latest changes from GitHub

Before starting new work:

```bash
git switch main
git pull
```

This makes sure your local `main` is up to date.

---

 Check your changes

```bash
git status
```

This shows which files you've changed.

---

 Add your changes

```bash
git add .
```

This prepares your changes for a commit.

---

 Commit your changes

```bash
git commit -m "Describe what you changed"
```

Example:

```bash
git commit -m "Added student profile form"
```

Try to make commit messages describe the actual change.

 Good commit messages

```text
Added login form
Fixed scholarship filtering
Updated database schema
Added recommendation algorithm
Fixed navbar layout
```

 Avoid

```text
update
changes
asdf
final
done
```

---

 Push your branch to GitHub

```bash
git push -u origin <branch-name>
```

Example:

```bash
git push -u origin student-profile
```

After the first push, you can usually just use:

```bash
git push
```

---

 🔄 Recommended Workflow

Whenever you start working on something:

 1. Update your local `main`

```bash
git switch main
git pull
```

 2. Create your feature branch

```bash
git switch -c my-feature
```

Example:

```bash
git switch -c scholarship-search
```

 3. Work on your feature

Write your code normally.

 4. Check your changes

```bash
git status
```

 5. Add your changes

```bash
git add .
```

 6. Commit

```bash
git commit -m "Added scholarship search"
```

 7. Push your branch

```bash
git push -u origin scholarship-search
```

 8. Create a Pull Request

Go to GitHub and create a **Pull Request** from:

```text
scholarship-search → main
```

 9. Have another member review your code

Check that:

* The feature works
* Existing features still work
* There are no obvious bugs
* No unnecessary files were added
* The code is understandable

 10. Merge

Once the feature is approved, merge the Pull Request into `main`.

---

 🔀 What To Do After Your Feature Is Merged

Once your feature has been successfully merged into `main`, **do not keep using the old branch indefinitely.**

You can delete the old branch on GitHub after it has been merged.

Then update your local repository:

```bash
git switch main
git pull
```

For your next feature, create a **new branch**:

```bash
git switch -c another-feature
```

---

 ⚠️ If Someone Else Added a Feature

Before starting new work, always make sure your local `main` has the latest version:

```bash
git switch main
git pull
```

Then create your new branch from the updated `main`:

```bash
git switch -c my-new-feature
```

This helps prevent conflicts and makes sure you're working with the newest version of the project.

---

 🚨 If You Made Changes to the Wrong Branch

Don't panic.

First, **don't push anything**.

Tell the team and ask for help before attempting complicated Git commands.

Git can usually recover your work, so don't randomly delete files or use commands you don't understand.

---

 ⚠️ Avoid These Things

 ❌ Don't push directly to `main`

```bash
git push origin main
```

 ❌ Don't use force push

Avoid:

```bash
git push --force
```

 ❌ Don't commit sensitive information

Never commit:

```text
passwords
API keys
database credentials
private tokens
.env files containing secrets
```

 ❌ Don't commit unnecessary files

Avoid committing things such as:

```text
node_modules/
temporary files
IDE settings
personal files
large generated files
```

Use a `.gitignore` file when appropriate.

---

 🧩 Adding Your Feature to the Project

When you finish a feature, make sure it is actually integrated properly.

Before creating your Pull Request:

 Check that:

* [ ] The feature works
* [ ] The project still runs
* [ ] Existing features still work
* [ ] No unnecessary files are included
* [ ] Your code is committed
* [ ] Your branch is pushed to GitHub
* [ ] Your Pull Request clearly describes what you added

 Pull Request description example

```text
 What I Added

- Added student registration form
- Added input validation
- Connected the form to the database

 Testing

- Tested registration with valid information
- Tested empty fields
- Tested invalid email addresses

 Notes

No known issues.
```

---

 📁 Suggested Project Structure

The exact structure may change as development continues, but try to keep related files organized.

```text
Scholarship-Matching-System/
│
├── frontend/
│
├── backend/
│
├── database/
│
├── model/
│
├── documentation/
│
├── README.md
└── .gitignore
```

---

 🤝 Team Rule

 **Communicate before making major changes.**

If you're planning to:

* Change the database structure
* Rewrite an existing feature
* Change the project's architecture
* Remove someone else's code
* Install/change major dependencies
* Rename important files or folders

Tell the group first.

Small changes can be made independently, but major changes should be discussed.

---

 🧠 Quick Git Cheat Sheet

```bash
 Get the project
git clone <repository-url>

 Check your branch
git branch

 Update main
git switch main
git pull

 Create a feature branch
git switch -c <feature-name>

 Check changes
git status

 Add changes
git add .

 Commit changes
git commit -m "Description of changes"

 Push branch
git push -u origin <feature-name>

 Switch branches
git switch <branch-name>

 Get latest changes
git pull
```

---

 ⭐ Golden Rule

```text
                    DON'T PUSH TO MAIN
                           ↓
                   Create a branch
                           ↓
                      Write code
                           ↓
                       Commit
                           ↓
                        Push
                           ↓
                   Create Pull Request
                           ↓
                        Review
                           ↓
                     Merge to main
```

**`main` = stable project**

**Branches = your workspace**

**Pull Requests = how we safely add completed features to the project**

---

 📚 Remember

Git is not just a place to upload your code.

It allows the team to:

* Work on different features simultaneously
* Keep track of changes
* Recover previous versions
* Review each other's code
* Prevent unfinished code from breaking `main`
* Combine everyone's work safely

**When in doubt: create a branch first.**
