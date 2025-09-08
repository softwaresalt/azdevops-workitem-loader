# Azure DevOps Work Item Loader

A Python script to load features, user stories, and tasks into Azure DevOps from YAML files with support for custom fields and templates.

## 🚀 Quick Start

1. **Install dependencies**:
   ```bash
   pip install azure-devops PyYAML
   ```

2. **Configure the script**:
   ```bash
   cp parameters.yaml.sample parameters.yaml
   # Edit parameters.yaml with your Azure DevOps settings
   ```

3. **Set up your Personal Access Token**:
   - Go to `https://dev.azure.com/yourorg/_usersSettings/tokens`
   - Create a token with "Work Items (Read & Write)" scope
   - Update `personal_access_token` in `parameters.yaml`

4. **Run the script**:
   ```bash
   python ado.workitem-loader.py
   ```

## 📁 Configuration

The script uses a `parameters.yaml` file for all configuration. This file must be in the same directory as the script.

### Required Configuration: parameters.yaml

```yaml
azure_devops:
  organization_url: "https://dev.azure.com/yourorg"
  project: "YourProject"
  area_path: "YourProject"
  iteration_path: "YourProject" 
  personal_access_token: "your_pat_token_here"

file_paths:
  yaml_file_path: "path/to/your/backlog.yaml"
  template_file_path: "work-item-templates.yaml"  # Optional, relative to script directory

formatting:
  enable_markdown: true  # Enable Markdown to HTML conversion
```

**Note**: File paths can be absolute or relative to the script directory. Relative paths are automatically resolved to the directory containing the script.

## ✨ Markdown Support

The script supports converting Markdown to HTML for rich formatting in description and acceptance criteria fields.

### Enabling Markdown Support

1. **Install the markdown package**:
   ```bash
   pip install markdown
   ```

2. **Enable in parameters.yaml**:
   ```yaml
   formatting:
     enable_markdown: true
   ```

3. **Use Markdown in your YAML files**:
   ```yaml
   features:
     - Title: "User Authentication"
       Description: |
         ## Overview
         Implement **secure** authentication with:
         - Username/password login
         - Multi-factor authentication
         - Password reset functionality
         
         > **Note**: This is a critical security feature.
       
       user_stories:
         - Title: "User Login"
           Acceptance_Criteria: |
             ## Acceptance Criteria
             
             ### ✅ Successful Login
             1. **Given** valid credentials
             2. **When** user logs in
             3. **Then** redirect to dashboard
             
             ### ❌ Failed Login
             - Show error message
             - Log failed attempt
             - Implement rate limiting
   ```

### Supported Markdown Features

- **Headers**: `# H1`, `## H2`, `### H3`
- **Emphasis**: `**bold**`, `*italic*`
- **Lists**: Bulleted and numbered lists
- **Code blocks**: Fenced code blocks with syntax highlighting
- **Tables**: Markdown table syntax
- **Blockquotes**: `> Important note`
- **Links**: `[text](url)`
- **Checkboxes**: `- [ ] Task item`

### Benefits

- **Rich Formatting**: Create visually appealing work items with proper formatting
- **Better Readability**: Use headers, lists, and emphasis for clear documentation
- **Code Examples**: Include formatted code snippets in descriptions
- **Professional Documentation**: Generate work items that look great in Azure DevOps
```

### Setup Steps

1. Copy the sample configuration:
   ```bash
   cp parameters.yaml.sample parameters.yaml
   ```

2. Edit `parameters.yaml` with your values:
   - Update Azure DevOps organization URL and project name
   - Set your Personal Access Token
   - Set paths to your YAML files

3. **Security**: Add `parameters.yaml` to `.gitignore` (already included)

## 📋 Features

- **YAML-based work item definition**: Define features, user stories, and tasks in YAML
- **Custom field support**: Map YAML fields to any Azure DevOps fields via templates
- **Markdown support**: Convert Markdown to HTML for rich formatting in descriptions and acceptance criteria
- **Hierarchical relationships**: Automatically creates parent-child links
- **Environment variable support**: Use environment variables for sensitive data
- **Template system**: Define custom field mappings for different work item types

## 🔍 Identifying Azure DevOps Field Names

To use custom fields in your templates, you need to know the exact Azure DevOps field names. Here's how to identify them using the Azure CLI:

### Prerequisites for Field Discovery

1. **Install Azure CLI**: Download from [https://docs.microsoft.com/en-us/cli/azure/install-azure-cli](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli)
2. **Install Azure DevOps Extension**:
   ```bash
   az extension add --name azure-devops
   ```
3. **Login to Azure CLI**:
   ```bash
   az login
   ```
4. **Set default organization** (optional):
   ```bash
   az devops configure --defaults organization=https://dev.azure.com/yourorg project=YourProject
   ```

### Method 1: Examine Existing Work Items

The best way to identify field names is to examine an existing work item that has the fields you want to use:

```bash
# Get a work item by ID and show all fields
az boards work-item show --id 123 --org https://dev.azure.com/yourorg --project YourProject

# Save output to file for easier analysis
az boards work-item show --id 123 --org https://dev.azure.com/yourorg --project YourProject > workitem.json
```

**Example Output Analysis**:
```json
{
  "fields": {
    "System.Title": "Example User Story",
    "System.Description": "Story description",
    "Microsoft.VSTS.Scheduling.StoryPoints": 5,
    "Microsoft.VSTS.Common.Priority": 2,
    "Microsoft.VSTS.Common.BusinessValue": 100,
    "Custom.FeatureValue": "Security",
    "Custom.UserType": "End User"
  }
}
```

### Method 2: List Available Fields for Work Item Types

```bash
# List all fields available for a specific work item type
az boards work-item type show --type "User Story" --org https://dev.azure.com/yourorg --project YourProject

# List all work item types in your project
az boards work-item type list --org https://dev.azure.com/yourorg --project YourProject
```

### Method 3: Query Work Items with Specific Fields

```bash
# Use WIQL (Work Item Query Language) to see fields in use
az boards query --wiql "SELECT [System.Id], [System.Title], [Microsoft.VSTS.Scheduling.StoryPoints], [Custom.FeatureValue] FROM WorkItems WHERE [System.WorkItemType] = 'User Story'" --org https://dev.azure.com/yourorg --project YourProject
```

### Common Field Name Patterns

| Field Type | Pattern | Examples |
|------------|---------|----------|
| System Fields | `System.FieldName` | `System.Title`, `System.State`, `System.AssignedTo` |
| Microsoft VSTS | `Microsoft.VSTS.Category.FieldName` | `Microsoft.VSTS.Scheduling.StoryPoints`, `Microsoft.VSTS.Common.Priority` |
| Custom Fields | `Custom.FieldName` | `Custom.FeatureValue`, `Custom.BusinessPriority` |
| Organization Custom | `YourOrg.FieldName` | `Contoso.Department`, `Fabrikam.CostCenter` |

### Creating Template Mappings

Once you identify the field names, create mappings in your `work-item-templates.yaml`:

```yaml
work_item_types:
  "User Story":
    fields:
      - name: "Story Points"
        azure_field_path: "Microsoft.VSTS.Scheduling.StoryPoints"  # Found via az CLI
        yaml_key: "StoryPoints"
        type: "float"
        
      - name: "Business Value"
        azure_field_path: "Microsoft.VSTS.Common.BusinessValue"   # Found via az CLI
        yaml_key: "BusinessValue"
        type: "integer"
        
      - name: "Feature Category"
        azure_field_path: "Custom.FeatureValue"                   # Found via az CLI
        yaml_key: "FeatureValue"
        type: "string"
```

### Troubleshooting Field Discovery

**Field not showing in output?**
- Create a test work item manually in Azure DevOps with the desired fields populated
- Use `az boards work-item show` on that test work item
- Look for the field in the `fields` section of the JSON output

**Custom fields not visible?**
- Ensure custom fields are added to your process template
- Verify you have permissions to view the fields
- Check if fields are hidden on the work item form but still exist in the backend

**Field names with spaces or special characters?**
- Azure DevOps automatically converts display names to reference names
- Example: "Story Points" becomes "Microsoft.VSTS.Scheduling.StoryPoints"
- Use the exact reference name from the CLI output, not the display name

### Practical Example

Here's a complete example using the default organization from this project:

```bash
# Set default configuration (replace with your values from parameters.yaml)
az devops configure --defaults organization=https://dev.azure.com/datacognition project=Work-Item-Loader-Agile

# Find an existing User Story to examine
az boards query --wiql "SELECT [System.Id], [System.Title] FROM WorkItems WHERE [System.WorkItemType] = 'User Story'" --top 5

# Examine a specific work item (replace 123 with actual ID from above query)
az boards work-item show --id 123

# Look for custom fields - save to file for easier searching
az boards work-item show --id 123 > sample-user-story.json

# Search the file for field patterns
# Windows PowerShell:
Get-Content sample-user-story.json | Select-String "Custom\.|Microsoft\.VSTS"

# Linux/Mac/Git Bash:
grep -E "Custom\.|Microsoft\.VSTS" sample-user-story.json
```

**Example Template Creation Workflow**:

1. **Identify fields from existing work item**:
   ```bash
   az boards work-item show --id 123 | findstr /C:"StoryPoints" /C:"Priority" /C:"BusinessValue"
   ```

2. **Update your template file**:
   ```yaml
   work_item_types:
     "User Story":
       fields:
         - name: "Story Points"
           azure_field_path: "Microsoft.VSTS.Scheduling.StoryPoints"
           yaml_key: "StoryPoints"
           type: "float"
   ```

3. **Test with your YAML data**:
   ```yaml
   features:
     - Title: "Test Feature"
       user_stories:
         - Title: "Test Story"
           StoryPoints: 5  # This will map to Microsoft.VSTS.Scheduling.StoryPoints
   ```

## 📚 Documentation

- **[Parameters Configuration](README-parameters.md)** - Detailed configuration guide
- **[Custom Field Templates](README-templates.md)** - Template system documentation
- **[Sample Files](#sample-files)** - Example YAML files and templates

## 📁 Files

| File | Description |
|------|-------------|
| `ado.workitem-loader.py` | Main script |
| `parameters.yaml.sample` | Sample configuration file |
| `work-item-templates.yaml` | Sample custom field templates |
| `sample-backlog-with-custom-fields.yaml` | Sample work items with custom fields |
| `sample-backlog-with-markdown.yaml` | Sample work items with Markdown formatting |
| `README-parameters.md` | Configuration documentation |
| `README-templates.md` | Template system documentation |

## 🔧 Prerequisites

- Python 3.7+
- Azure DevOps organization and project
- Personal Access Token with "Work Items (Read & Write)" scope
- Required Python packages:
  - `azure-devops`
  - `PyYAML`
  - `markdown` (optional, for Markdown to HTML conversion)

## 🛡️ Security Notes

- Never commit `parameters.yaml` with real tokens to version control
- Use environment variables for sensitive data in CI/CD scenarios
- Keep your Personal Access Token secure and rotate it regularly
- The `.gitignore` file is configured to exclude sensitive files

## 📖 Example Usage

1. **Basic setup**:
   ```yaml
   # parameters.yaml
   azure_devops:
     organization_url: "https://dev.azure.com/mycompany"
     project: "MyProject"
     personal_access_token: "your_token_here"
   
   file_paths:
     yaml_file_path: "my-backlog.yaml"
   ```

2. **Run the loader**:
   ```bash
   python ado.workitem-loader.py
   ```

3. **Using environment variables**:
   ```bash
   export AZURE_DEVOPS_PAT="your_token_here"
   # Set use_env_for_pat: true in parameters.yaml
   python ado.workitem-loader.py
   ```

## 🐛 Troubleshooting

### Authentication Errors
- Verify your Personal Access Token is valid and has correct scopes
- Ensure your account has access to the organization and project
- Check organization URL and project name in `parameters.yaml`

### Configuration Errors
- Ensure `parameters.yaml` exists in the script directory
- Validate YAML syntax using a YAML validator
- Check file paths are correct and accessible

### Work Item Creation Errors
- Verify area path and iteration path exist in your project
- Check custom field definitions match your Azure DevOps configuration
- Ensure work item types exist in your process template

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with your Azure DevOps environment
5. Submit a pull request

## 📄 License

This project is provided as-is for educational and productivity purposes.
