 # Resume Builder TODO
 
## Decisions Made
- **Data Format:** YAML for structured resume data (flexible, version controlled and readable)
- **Templates:** LaTeX via Jinja2 (professional output, programmable, easily read)
- **Project Management:** Obsidian with symlinked files (AI-accessible, cross-project)
- **Versioning:** Metadata in YAML + git for code versioning
- **Resume Directory:** Resumes reside in directory format (Git VC enabled)

## Questions/Research Needed
- What's the optimal application tracking granularity?
- Which job posting APIs have the best data quality and availability?
- How will AI integrate with version controlled resumes provide helpful feedback?

### In Progress
- [ ] Friction analysis framework real job applications #job-applications #user-research 📅 2026-04-03
- [ ] Add test resume for learning / building experience

### Friction Analysis
- [x] Port over template changes from Oura resume to `classic.tex`template #job-applications #user-research 📅 2026-08-19 ✅ 2026-08-24
- [x] Add new resume experience to pick from when completing a resume #job-applications #user-research 📅 2026-08-19 ✅ 2026-10-07
- [x] Find ways to get better advice on resume updates from Claude #job-applications #user-research 📅 2026-08-19 ✅ 2026-10-07
- [ ] Add education details to templates to show relevant experience #job-applications #user-research 📅 2026-08-24
- [ ] More consistent parameter flags between different package call for smoother iterations #job-applications #user-research 📅 2026-08-24
- [ ] Resume-builder does not build clean environment with PDF  #job-applications #user-research 📅 2026-08-24
- [ ] Instead of nested repository build everything in flat directory #job-applications #user-research 📅 2026-09-01 
- [ ] Make file should run the python-imploder function #job-applications #user-research 📅 2026-09-01 
- [ ] Make file should set up local pyenv #job-applications #user-research 📅 2026-09-01 
- [ ] Make file should transform job_posting to text file #job-applications #user-research 📅 2026-09-01 
- [ ] Make file should have standardized output #job-applications #user-research 📅 2026-09-01 
- [ ] Make file should make call to start application tracking #job-applications #user-research 📅 2026-09-01 
- [ ] Function call to launch pdf for viewing
- [ ] Edit and review resume flow could use less friction
- [ ] YAML file edits reconstruct key achievements file what should not be amended
- [ ] Job tracking should be surfaced directly to Obsidian files
- [ ] Incorporate application clock in and clock out calls
- [ ] Application status should be inferred from timestamp or null values (found, submitted, closed, interview)
- [ ] Re-align all function calls to be standardized and default where it matters
- [ ] Relocate the output of the pdf and resume.yaml
- [ ] Clean up the pdf outputs pre-post call to make sure that not artifacts remain and recalls are not conflicting
- [ ] Function call to launch the job-posting

### Drift fixes (resume content repo: /Users/rubicon/Development/resume)
- [x] Fix stale resume.json references -> resume.yaml in Makefile + README #cleanup

### Resume Compatibility
- [-] Functionality to update older resumes to new formats
- [ ] Integrate resume into a UI
- [x] Add resume version control test to resumes #versioning 📅 2026-04-03 ✅ 2026-08-06
- [ ] Add Compatibility for educational details
- [ ] Clarify resume metadata requirements and add test

### Usability
- [-] API service provided
- [x] CLI provided

### Github Integration
- [ ] Run test on github pushes
- [ ] Set up monitoring to make sure no PII is leaked in resume / resume history 2026-04-03 #pii #testing #python

### Comprehensive Testing Suite

## Completed ✅
- [x] \[Template\]Created LaTeX template system with Jinja2 ✅ 2026-03-15  
- [x] \[PDF\] Implemented basic PDF generation workflow ✅ 2026-03-18
- [x] \[Testing\]Resume test that confirms that specific sections are implemented in resume #testing #python 📅 2026-04-03 ✅ 2026-04-03
- [x] \[Testing\] Resume test that confirms that the resume structure is valid #testing #python 📅 2026-04-03 ✅ 2026-04-03
- [x] \[Testing\] Resume Test that confirms that the resume has correct metadata information #testing #python 📅 2026-04-03 ✅ 2026-04-03
- [x] \[Testing\] Template test that template is built correctly ✅ 2026-06-09
- [x] \[Testing\] Round-trip test: implode(explode(x)) == x using fixtures + real resume.yaml  ✅ 2026-07-31
- [x] \[Resume\] Built JSON resume structure ✅ 2026-03-08
- [x] \[Resume\] Update resumes to YAML files not JSON files 📅 2026-04-03 #yaml ✅ 2026-06-09
- [x] \[Resume\] Remove highlights sections in the resumes to improve functionality / readability 📅 🔼 ✅ 2026-06-09 #resume 
- [x] \[Resume\] Add function to update resumes to newer versions 📅 2026-04-03 ✅ 2026-06-09 #versioning
- [x] \[Resume\] Add resume versions control to resume_builder 📅 2026-04-03 ✅ 2026-06-09 #versioning 
- [x] \[Resume\] Build resume_explode and resume_implode module   ✅ 2026-07-31
- [x] \[Resume\] Add ID keys: short human-identifiable summaries to enable resume ordering   ✅ 2026-07-31
- [x] \[Resume\] Create new resume template for previous resume design   ✅ 2026-07-31
- [x] \[Workflow\] Set up Obsidian project management system ✅ 2026-03-20
- [x] \[Workflow\] Scrub PII from existing github repository #resume #PII 📅 2026-04-02 ✅ 2026-04-03
- [x] \[Workflow\] Set up a github repository for resume and versions 📅 2026-06-09 #git #workflow ✅ 2026-06-09
- [x] \[Workflow\] Make resume_builder an executable package 📅 2026-04-03 ✅ 2026-06-09 #versioning
- [x] \[Workflow\] Add CLI entry point(s) for explode/implode in pyproject.toml   ✅ 2026-07-31
