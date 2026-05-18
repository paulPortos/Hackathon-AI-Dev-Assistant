<div align="center">
  <h1>👁️ Visor</h1>
  <p><strong>Your AI-Powered Senior Developer & Agile Project Manager</strong></p>
  <p><i>Bridging the gap between rapid "vibe coding" and production-ready engineering.</i></p>
</div>

---

## 📖 About The Project

In the era of AI-assisted development ("vibe coding"), building applications has never been easier. Both technical and non-technical founders are shipping products at unprecedented speeds. However, this rapid pace often comes at a cost: **crucial software engineering principles like security, scalability, and long-term business viability are frequently overlooked.**

**Visor** (short for *Supervisor*) is an autonomous, multi-agent development assistant designed to act as your virtual Senior Developer and Project Manager. 

It reviews your work, asks the hard questions, and automates your agile workflow—ensuring that your fast-paced development doesn't result in technical debt, architectural bottlenecks, or security vulnerabilities.

### 🌍 Real-World Impact & Benefits
- **Safety Net for "Vibe Coders":** Prevents prototype code from reaching production with glaring security holes (e.g., missing CORS, exposed keys, or unescaped database queries).
- **Automated Project Management:** Eliminates the overhead of manual backlog grooming and task management. Visor automatically identifies technical gaps, creates tasks, and prioritizes them without human intervention.
- **Smart Resource Allocation:** By understanding the unique profile and strengths of every developer in your workspace, Visor delegates the right tasks to the right people.
- **Continuous Mentorship:** Acts as an on-demand mentor for starting programmers, asking probing questions that teach industry best practices (*"How did you handle rate limiting?"*, *"Why did you choose this architecture?"*).

---

## ✨ Key Features

- 🕵️ **Interactive Code Verification:** Report your recent changes to the **Senior Dev Agent**. It analyzes your latest commit on the current branch, verifies your claims, and initiates an intelligent dialogue to uncover missed edge cases.
- 📋 **Automated Task Generation:** When the Senior Dev Agent identifies vulnerabilities, missing functionality, or scalability issues, it passes the context to the **Project Manager Agent**, which automatically drafts actionable tickets.
- 🎯 **Intelligent Task Delegation:** Tasks are routed to the most fitting developer based on their historically built User Profile, current context, and skill set.
- 📊 **Autonomous Scrum Management:** The **Scrum Agent** handles the orchestration of meetings, notifications, and dynamically ranks tasks based on critical priority paths *(New Feature → Business Fit → Scalability → Security)*.
- 🤝 **Seamless Collaboration:** Easily invite other developers or stakeholders into the project workspace to streamline team communication.
- 🔗 **Deep GitHub Integration:** Built-in GitHub OAuth and seamless repository integration to monitor commits and branches directly in real-time.

---

## 🤖 The Agentic Architecture

Visor utilizes a highly collaborative multi-agent system powered by the **Agno** agentic framework and **Ollama**:
1. **Senior Dev Agent:** Your technical gatekeeper. Inspects commits, interrogates implementation details, and enforces engineering standards.
2. **Project Manager (PM) Agent:** The organizer. Takes technical findings from the Senior Dev and translates them into scoped, assignable tasks.
3. **Scrum Agent:** The facilitator. Automates the agile lifecycle, handles dynamic priority ranking, and manages team meetings and notifications.

---

## 🛠️ Technology Stack

**Frontend**
- React.js
- Deployed on Vercel

**Backend**
- Django (Python - Leveraging Python's AI ecosystem)
- PostgreSQL
- Deployed on Render

**AI & Agents**
- Agno (Agentic Framework)
- Ollama (LLM/Agent Provider)

**Authentication**
- GitHub OAuth
