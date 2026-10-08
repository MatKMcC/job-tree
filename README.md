# Job Tree
A tool to manage a git based resume repository. This project implodes resumes into a readable format and builds them using templated latex files. Any job specific changes are exploded and pushed to preserve the application state and help evolve the resume over time.

## ;TLDR
Typical resume formats (word documents) are in tension with resume requirements; flexibility to the job posting, traceability and ease of incorporating job specific in improvements into the **main** body of work. This project attempts to simplify this work by separating resume content and resume design and introducing a system to customize job-specific resumes and migrate improvements back into general or role specific resumes.

1. Resume As A Git Repository
Resume content is tracked in a file based git repository. This allows job specific edits, such as new achievements, skills and content rewording to be smoothly incorporated back into the **main** body of work. This also allows a simple tracking of applications via branches and the changeling and a corpus of work that is easily interpreted by LLMs. 
3. Key Value Based Resume Format (YAML)
A simple extendable resume structure that allows for component wise updates or improvements to a resume and programatic resume manipulations when updating, reading or tracking applications.
5. Latex Templates For Resume Presentation
Resume agnostic latex file(s) that can be easily applied to any resume with the correct YAML format. Making aesthetic updates persistent, config based changes that require minimal effort to apply. 

## Current Status
- **Phase:** Application testing
- **Progress:** Initial templating, resume generation, and end-to-end testing complete. Shared online and working on integration with my application process, command line beta
- **Target:** Useable and shareable application that truly streamlines the application process

## Components
- ✅ **YAML Resume Structure** - Structured resume data 
- ✅ **LaTeX Template System** - PDF generation via Jinja2
- ✅ **End to End testing** - Validate resume and template compatibility (in progress)
- ✅ **Resume Versioning** - Structured resume data  (in progress)
- ✅ **Template Versioning** - Structured resume data  (in progress)
- ✅ **Additional Templates** - Structured resume data  (planned)
- ⏳ **CLI Endpoints** - CLI workflow integration to quickly create an application (planned)
- ⏳ **AI Optimization** - Canned prompts for simple and cheap suggestions to improve resumes for an application (future)
- ⏳ **Application UI** - A resume UI that suggest and incorporates application specific  (future)
- ⏳ **Job Status Tracking** - Aggregate information from application files to track job applications (future)

## Quick Start
```bash
# initialize a job from a new posting
job-tree init --company XYZ --url 'XYZ.com/jobs-posting' --role 'astronaut'
# Generate resume PDF from a resume repository
job-tree build --template classic.tex
```

## Architecture
- **Data:** YAML resume structure with metadata and versioning and file based git repository
- **Templates:** LaTeX templates with Jinja2 for customization
- **Output:** PDF resumes via LaTeX compilation

## Links
- **Resume Data:** [resume/resume.json](resume/resume.json)
- **Main Builder:** [resume_builder.py](resume_builder/resume_builder.py)
- **Templates:** [templates/](resume_builder/templates/)
- **Tests:** [tests/](tests/)
