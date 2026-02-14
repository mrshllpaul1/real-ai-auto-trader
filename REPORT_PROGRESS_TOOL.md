# Report Progress Tool Guide

## Overview

The `report_progress` tool is a specialized function used in GitHub Copilot Workspaces to automatically commit and push code changes. It's the primary mechanism for saving progress and sharing updates when working with AI agents in the Emergent platform.

## What is the Report Progress Tool?

The `report_progress` tool is an automated workflow tool that:
- **Commits** all pending changes in your repository
- **Pushes** changes to your GitHub branch
- **Updates** PR descriptions with progress checklists
- **Tracks** development milestones
- **Maintains** a clear history of what was accomplished

Think of it as a "smart save" button that not only saves your work but also documents what you did.

## When to Use It

### ✅ Use `report_progress` when:

1. **Completing a Meaningful Unit of Work**
   - Fixed a bug
   - Added a new feature
   - Updated documentation
   - Refactored code

2. **Reaching Milestones**
   - Completed items on your checklist
   - Finished a phase of development
   - Made changes you want to preserve

3. **Before Major Changes**
   - Creating a checkpoint before trying something new
   - Saving stable state before experimentation

4. **Updating Stakeholders**
   - Sharing progress with team members
   - Demonstrating completed work
   - Showing incremental improvements

### ❌ Don't use it when:

- No meaningful changes have been made
- Files are in a broken/incomplete state
- Just exploring or reading code
- Making temporary test changes

## How It Works

### The Process

```
1. You make code changes
   ↓
2. Agent calls report_progress
   ↓
3. Tool runs: git add .
   ↓
4. Tool runs: git commit -m "Your message"
   ↓
5. Tool runs: git push origin <branch>
   ↓
6. PR description is updated
   ↓
7. Changes are live on GitHub
```

### Behind the Scenes

When `report_progress` is called:

1. **Stages Changes**: Runs `git add .` to stage all modified files
2. **Creates Commit**: Generates a commit with your message
3. **Pushes to Remote**: Sends changes to GitHub
4. **Updates PR**: Modifies the pull request description with progress

## Using report_progress

### Basic Syntax

```markdown
report_progress(
  commitMessage: "Brief description of what was done",
  prDescription: "Detailed checklist with progress markers"
)
```

### Parameters

#### `commitMessage` (required)
- **Type**: String
- **Purpose**: Brief, single-line commit message
- **Best Practices**:
  - Start with an action verb (Add, Fix, Update, Remove)
  - Be specific but concise
  - Describe WHAT changed, not WHY
  
**Good Examples**:
```
"Add user authentication feature"
"Fix navbar responsive layout bug"
"Update API documentation with new endpoints"
"Remove deprecated payment methods"
```

**Bad Examples**:
```
"Changes" (too vague)
"Fixed stuff" (not specific)
"Work in progress" (incomplete work shouldn't be committed)
"asdf" (meaningless)
```

#### `prDescription` (required)
- **Type**: String (Markdown formatted)
- **Purpose**: Track progress with checklists
- **Format**: Use markdown checklists

**Checklist Format**:
```markdown
- [x] Completed task 1
- [x] Completed task 2
- [ ] Pending task 3
- [ ] Pending task 4
```

**Example**:
```markdown
- [x] Set up project structure
- [x] Create database models
- [x] Implement user authentication
- [ ] Add password reset functionality
- [ ] Write unit tests
- [ ] Deploy to production
```

## Best Practices

### 1. Report Early and Often
```markdown
✅ DO: Report progress after each meaningful change
❌ DON'T: Wait until everything is perfect
```

Benefits of frequent reporting:
- Creates detailed history
- Easy to rollback if needed
- Shows steady progress
- Prevents loss of work

### 2. Write Clear Commit Messages
```markdown
✅ DO: "Add email validation to registration form"
❌ DON'T: "updated files"
```

### 3. Use Descriptive Checklists
```markdown
✅ DO:
- [x] Implement JWT authentication
- [x] Add login endpoint with email/password
- [x] Create middleware for token verification
- [ ] Add refresh token functionality

❌ DON'T:
- [x] Auth stuff
- [ ] More features
```

### 4. Keep Checklists Consistent
- Maintain the same structure between updates
- Only update completion status ([x] vs [ ])
- Add new items at the end
- Don't remove completed items

### 5. One Purpose Per Commit
Each `report_progress` should represent one logical change:
- One bug fix
- One feature addition
- One refactoring task
- One documentation update

## Real-World Examples

### Example 1: Bug Fix

```markdown
report_progress(
  commitMessage: "Fix database connection timeout in production",
  prDescription: `
- [x] Investigate timeout issues
- [x] Increase connection pool size
- [x] Add connection retry logic
- [x] Test in staging environment
- [ ] Monitor production metrics
- [ ] Update infrastructure documentation
  `
)
```

### Example 2: New Feature

```markdown
report_progress(
  commitMessage: "Add dark mode toggle to user settings",
  prDescription: `
- [x] Create theme context provider
- [x] Design dark mode color palette
- [x] Implement toggle switch UI
- [x] Save preference to localStorage
- [ ] Add theme transition animations
- [ ] Test across all pages
- [ ] Update user documentation
  `
)
```

### Example 3: Documentation Update

```markdown
report_progress(
  commitMessage: "Add comprehensive API documentation for payment endpoints",
  prDescription: `
- [x] Document payment processing endpoint
- [x] Add request/response examples
- [x] Include error code reference
- [x] Create authentication guide
- [ ] Add webhook documentation
- [ ] Review with team
  `
)
```

### Example 4: Refactoring

```markdown
report_progress(
  commitMessage: "Refactor authentication service to use TypeScript",
  prDescription: `
- [x] Convert auth.js to auth.ts
- [x] Add type definitions for user objects
- [x] Update imports in dependent files
- [x] Fix TypeScript compilation errors
- [ ] Add JSDoc comments
- [ ] Update tests
  `
)
```

## Integration with Emergent Platform

### How Emergent Tracks Progress

The Emergent AI platform uses `report_progress` to:
1. **Monitor Development**: Track what's being built in real-time
2. **Session Handoffs**: Pass context between agent sessions
3. **Quality Control**: Review commit history and code changes
4. **Project Analytics**: Understand development velocity

### The `.emergent` Directory

Your repository's `.emergent/` folder contains:
- `emergent.yml` - Job configuration and environment details
- `summary.txt` - Comprehensive project status and progress analysis

These files work together with `report_progress` to maintain project state.

## Common Scenarios

### Scenario 1: Starting a New Task
```markdown
# First call - outline the plan
report_progress(
  commitMessage: "Initial plan for user profile feature",
  prDescription: `
- [ ] Design profile page UI
- [ ] Create profile API endpoints
- [ ] Implement profile update logic
- [ ] Add profile image upload
- [ ] Write tests
  `
)
```

### Scenario 2: Mid-Development
```markdown
# Update as you complete items
report_progress(
  commitMessage: "Complete profile page UI and API endpoints",
  prDescription: `
- [x] Design profile page UI
- [x] Create profile API endpoints
- [ ] Implement profile update logic
- [ ] Add profile image upload
- [ ] Write tests
  `
)
```

### Scenario 3: Task Complete
```markdown
# Final update
report_progress(
  commitMessage: "Complete user profile feature with tests",
  prDescription: `
- [x] Design profile page UI
- [x] Create profile API endpoints
- [x] Implement profile update logic
- [x] Add profile image upload
- [x] Write tests
  `
)
```

## Troubleshooting

### Problem: "Nothing to commit"
**Cause**: No files have changed since last commit  
**Solution**: Make some changes first, or skip reporting

### Problem: "Push rejected"
**Cause**: Remote branch has changes you don't have locally  
**Solution**: The agent will typically handle this automatically

### Problem: "Commit message too long"
**Cause**: Commit message exceeds recommended length  
**Solution**: Keep commit messages under 72 characters, use prDescription for details

### Problem: "Checklist format broken"
**Cause**: Incorrect markdown syntax  
**Solution**: Use `- [x]` for completed, `- [ ]` for pending (note the space after hyphen)

## Tips for Success

### 1. Start with a Plan
Your first `report_progress` should outline the complete plan:
```markdown
- [ ] All tasks you plan to complete
```

### 2. Report Regularly
Don't wait too long between reports:
- ✅ Every 1-3 meaningful changes
- ❌ Only at the end of the day

### 3. Be Specific
Vague updates don't help:
- ✅ "Fix race condition in payment processing"
- ❌ "Fixed a bug"

### 4. Include Context
Help future readers understand:
- What was changed
- Why it was changed (in PR description)
- What remains to be done

### 5. Review Before Reporting
Always check:
- ✅ Files you want to commit are modified
- ✅ No unwanted files will be committed
- ✅ Code is in a working state
- ✅ Commit message is clear

## Comparison with Manual Git

### Using report_progress
```markdown
✅ Automated: report_progress()
   - Stages files
   - Commits with message
   - Pushes to remote
   - Updates PR
   
One command does everything!
```

### Manual Git Workflow
```bash
❌ Manual: Multiple steps required
git add .
git commit -m "message"
git push origin branch
# Then manually update PR description
```

**Advantage**: `report_progress` is faster and ensures consistency

## Advanced Usage

### Handling Multiple Changes
If you have multiple independent changes, create separate reports:

```markdown
# Report 1: Backend changes
report_progress(
  commitMessage: "Add database indexes for performance",
  prDescription: "..."
)

# Report 2: Frontend changes  
report_progress(
  commitMessage: "Update UI components to use new design system",
  prDescription: "..."
)
```

### Strategic Checkpointing
Create checkpoints before risky changes:

```markdown
# Before major refactor
report_progress(
  commitMessage: "Checkpoint: Working state before authentication refactor",
  prDescription: "Current working state saved"
)

# Make risky changes...

# After successful refactor
report_progress(
  commitMessage: "Complete authentication refactor with improved security",
  prDescription: "..."
)
```

## Security Considerations

### What Gets Committed?

When `report_progress` runs `git add .`, it stages:
- ✅ All modified tracked files
- ✅ New files (unless in .gitignore)
- ❌ Files listed in .gitignore

### Best Practices:

1. **Use .gitignore** for:
   - Secrets and credentials
   - Build artifacts (node_modules/, dist/, etc.)
   - IDE-specific files
   - Local environment files (.env.local)
   - Temporary files

2. **Never commit**:
   - API keys
   - Passwords
   - Private keys
   - Personal data
   - Large binary files

3. **Review changes**:
   Ask the agent to show you what will be committed if you're unsure

## Related Documentation

- [PUSHING_TO_EMERGENT.md](./PUSHING_TO_EMERGENT.md) - Git workflow and Emergent integration
- [DOCUMENTATION_INDEX.md](./DOCUMENTATION_INDEX.md) - Complete documentation index
- [README.md](./README.md) - Project overview

## Quick Reference Card

```
╔══════════════════════════════════════════════════════════════╗
║                 REPORT_PROGRESS QUICK GUIDE                  ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  PURPOSE: Commit and push changes automatically             ║
║                                                              ║
║  WHEN TO USE:                                               ║
║    ✓ After completing a task                                ║
║    ✓ Reaching a milestone                                   ║
║    ✓ Creating a checkpoint                                  ║
║    ✓ Before major changes                                   ║
║                                                              ║
║  PARAMETERS:                                                ║
║    • commitMessage: Brief one-line description              ║
║    • prDescription: Markdown checklist of progress          ║
║                                                              ║
║  CHECKLIST FORMAT:                                          ║
║    - [x] Completed item                                     ║
║    - [ ] Pending item                                       ║
║                                                              ║
║  BEST PRACTICES:                                            ║
║    • Report early and often                                 ║
║    • Write clear commit messages                            ║
║    • Keep checklists consistent                             ║
║    • One purpose per commit                                 ║
║                                                              ║
║  WHAT IT DOES:                                              ║
║    1. git add .                                             ║
║    2. git commit -m "message"                               ║
║    3. git push origin branch                                ║
║    4. Update PR description                                 ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

## Summary

The `report_progress` tool is your primary way to save and share work in GitHub Copilot Workspaces. Use it frequently to:
- ✅ Create a clear development history
- ✅ Track progress with checklists
- ✅ Share updates with team members
- ✅ Maintain safe checkpoints
- ✅ Enable smooth session handoffs

**Remember**: Report early, report often, and write clear messages!

---

**Questions or Issues?** See [DOCUMENTATION_INDEX.md](./DOCUMENTATION_INDEX.md) for more guides.
