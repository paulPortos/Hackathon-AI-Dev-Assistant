Sr dev-ish conversation with scrum automation and task distribution

Problem: Since in this day of age, vibe coding is becoming/already a trend. Which is why technical and non technical people dive into it. But  the problem is vibe coders tend to not check somethings or even not included in their project like security, scalability and some business fit (In the next 3 months will our budget sustain this feature).  Also about project meetings, its a hastle in scrum methodology to rank each tasks/features by priority. 

Solution: A application that acts as a sr dev and a project manager. It will question you in your code application like how did you do it, did you also do this, and why did you do that, etc. Also arrange each meetings and rank AI does this for you where it notify meetings and rank the tasks/features based on priority (New feature -> Business fit -> Scalability -> Security)

Features:
Talk with the AI about your project, the AI will ask you in reply "Did you implement CORS" etc
If AI found a vulnerability or gap within the project during the convo. It will create a task and distribute that to the most fitting dev
Invite other devs/user in the project
Automate scrum meetings and rank task from critical to low
User Profile will be used by the AI as context for project distribution
Github OAuth + Github Integration + Possible Github MCP

Techstack:
Backend : Django (Since it uses python and python is the lead language of AI)
Frontend : Sir @core and sir @TLEV will decide what platforms are we targeting (Web for universal accessability, Mobile, Desktop, etc)
Database : Postgres and
OAuth : Github
Email Provider : Twillio
Frontend Infra : Vercel
Backend Infra : Render
Agentic Framework : Agno
LLM/Agent Provider : Ollama

Agent Plan: 

SR Dev Agent
Project Manager Agent
Scrum Agent
