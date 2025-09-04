# FamlyPortal Git Branching Strategy

## Overview
FamlyPortal follows a **GitFlow-inspired** branching strategy optimized for family-focused development with proper staging and deployment workflows.

## Branch Structure

### 🌳 **Main Branches**

#### 1. `main`
- **Purpose**: Stable production releases
- **Protection**: Protected branch, no direct pushes
- **Merges From**: `production` branch only
- **Deployment**: Automatic production deployment
- **Status**: Currently at initial project setup

#### 2. `develop`
- **Purpose**: Main development integration branch
- **Protection**: Semi-protected, PR required
- **Merges From**: Feature branches, hotfixes
- **Merges To**: `staging` for testing
- **Status**: **CURRENT ACTIVE** - All features integrated
- **Latest**: Admin interface setup complete

#### 3. `staging`
- **Purpose**: Pre-production testing and QA
- **Protection**: Protected, automated testing
- **Merges From**: `develop` branch
- **Merges To**: `production` after testing
- **Deployment**: Staging environment deployment
- **Status**: Ready for testing

#### 4. `production`
- **Purpose**: Production-ready code awaiting release
- **Protection**: Highly protected, release manager only
- **Merges From**: `staging` after QA approval
- **Merges To**: `main` for production release
- **Status**: Ready for production deployment

### 🔧 **Supporting Branches**

#### Feature Branches (`feature/*`)
- **Naming**: `feature/[app-name]/[feature-description]` or `feature/[feature-description]`
- **Examples**: 
  - `feature/timesheet-app/validation-logic`
  - `feature/admin-interface-setup`
  - `feature/user-auth-family-system`
- **Lifecycle**: Create → Develop → PR to `develop` → Delete after merge
- **Status**: Multiple completed features ready for cleanup

#### Hotfix Branches (`hotfix/*`)
- **Naming**: `hotfix/[issue-description]`
- **Lifecycle**: Create from `main` → Fix → PR to `main` AND `develop`
- **Usage**: Critical production fixes only

#### Release Branches (`release/*`)
- **Naming**: `release/v[version-number]`
- **Lifecycle**: Create from `develop` → Finalize → Merge to `main` and `develop`
- **Usage**: Prepare releases, final testing, version bumping

## 🚀 **Development Workflow**

### Current Development Flow
```
feature/* → develop → staging → production → main
```

### Step-by-Step Process

#### 1. **Feature Development**
```bash
# Start new feature
git checkout develop
git pull origin develop
git checkout -b feature/new-feature-name

# Develop and commit
git add .
git commit -m "feat: implement new feature"

# Push and create PR
git push origin feature/new-feature-name
# Create PR to develop branch
```

#### 2. **Integration Testing**
```bash
# Merge approved features to develop
git checkout develop
git merge feature/new-feature-name --no-ff

# Deploy to staging for testing
git checkout staging
git merge develop --no-ff
git push origin staging
```

#### 3. **Production Release**
```bash
# After successful staging tests
git checkout production
git merge staging --no-ff
git push origin production

# Create production release
git checkout main
git merge production --no-ff
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin main --tags
```

## 📋 **Current Branch Status**

### ✅ **Completed Features** (All in `develop`)
1. **Initial Django Setup** - Project foundation
2. **User Auth & Family System** - Authentication and family management
3. **Database Models** - All app models and relationships
4. **Admin Interface** - Comprehensive admin with family scoping

### 🔄 **Active Development**
- **Current Branch**: `develop`
- **Next Feature**: Views and Templates (Prompt 5)
- **Status**: Ready for continued development

### 📦 **Ready for Deployment**
- **Staging**: Ready for testing with all features
- **Production**: Awaiting QA approval
- **Main**: Stable baseline for releases

## 🛡️ **Branch Protection Rules**

### `main` Branch
- ✅ Require pull request reviews
- ✅ Require status checks to pass
- ✅ Require up-to-date branches
- ✅ Restrict pushes to administrators only
- ✅ Required review from CODEOWNERS

### `develop` Branch  
- ✅ Require pull request reviews
- ✅ Require status checks to pass
- ⚠️ Allow administrators to bypass requirements

### `staging` & `production` Branches
- ✅ Require pull request reviews
- ✅ Automated deployment triggers
- ✅ Required testing suite passage

## 🔧 **Development Commands**

### Quick Branch Setup
```bash
# Switch to develop for new features
git checkout develop
git pull origin develop

# Create new feature branch
git checkout -b feature/your-feature-name

# Daily sync with develop
git checkout develop
git pull origin develop
git checkout feature/your-feature-name
git merge develop
```

### Release Commands
```bash
# Prepare staging deployment
git checkout staging
git merge develop --no-ff
git push origin staging

# Prepare production release
git checkout production  
git merge staging --no-ff
git push origin production

# Production release
git checkout main
git merge production --no-ff
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin main --tags
```

## 📝 **Commit Message Convention**

Following **Conventional Commits** standard:

```
<type>(scope): <description>

[optional body]

[optional footer]
```

### Types
- `feat`: New features
- `fix`: Bug fixes  
- `docs`: Documentation changes
- `style`: Code formatting
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

### Examples
```bash
feat(timesheet): add entry validation logic
fix(admin): resolve family scoping permission issue
docs(api): update authentication endpoints
chore(deps): update Django to 5.2.5
```

## 🎯 **Next Steps**

1. **Continue Development**: Start Prompt 5 on `develop` branch
2. **Feature Cleanup**: Archive completed feature branches
3. **Staging Deployment**: Set up staging environment testing
4. **CI/CD Setup**: Implement automated testing and deployment
5. **Production Planning**: Prepare for initial production release

---

**Current Status**: All Prompt 1-4 features integrated in `develop` branch
**Ready For**: Prompt 5 - Views and Templates Implementation
**Last Updated**: September 4, 2025
