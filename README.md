# timesheet-application
This is a repo to continue working on a timesheet application that I built as part of a hackathon. The project is a collaborative effort with AI tools in order to build my skills in using AI tools within engineering principles.

# The Process

1. Drafted an ERD based on knowledge of exisiting timesheet system and refined with ChatGPT
2. Worked with Codex on a business requirements doc to iterate over some requirements. The AI added questons and feedback to the doc which I edited and responsed to in the doc and added my own questions. This went on for several interations.
3. Collaborated with Codex (40% myself : 60% codex) to create a streamlit app to demo functionality based on the ERD
4. Using the streamlit demo we revisited the business requirements doc and made some further revisions
5. Updated the ERD to reflect these requirements
6. Worked with Codex to create an architecture/tech-stack doc based on the current knowledge of the proposed system
7. Using Codex with subagents. I had the main agent collaborate with a Product Owner, Developer, Solution Architect, and QA subagent to implement the application. Each agent was given a specific prompt of how to behave and its intended role in the development of the application along with the artifacts created previously for reference

# Local MVP Bootstrap

The current MVP is planned as a local Docker deployment.

You can use the published Docker image instead of building locally:

```bash
docker pull ghcr.io/rossusher147/timesheet-application:main
```

Or pull a specific released version:

```bash
docker pull ghcr.io/rossusher147/timesheet-application:VERSION
```

Note: whether you pull the published image or build locally, you still need a
local `timesheet_platform/.env` file. Copy `timesheet_platform/.env.example` to
`timesheet_platform/.env` and set the required values before starting the
container.

Suggested local setup flow:

1. Copy `timesheet_platform/.env.example` to a local `timesheet_platform/.env`.
2. Set your local Django secret key and demo HR credentials in `timesheet_platform/.env`.
3. Start the local Dockerized application.
4. Let the bootstrap process create the seeded demo HR account.
5. Check `demo-credentials.example.txt` and create a local `demo-credentials.txt` if you want your own local credential reference.
6. Log in as the demo HR user.
7. Use the HR screens to register a demo approver and a demo employee.
8. Use the HR project screens to create or retire projects and manage user assignment to them.

Important notes:

- `demo-credentials.txt` is only a local reference file for demo usernames and passwords.
- `timesheet_platform/.env` is the local Docker environment file and should stay local to your machine.
- The application must still authenticate against hashed passwords stored in the database.
- The real `demo-credentials.txt` should stay local to your machine.
