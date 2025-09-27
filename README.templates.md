# Azure DevOps Work Item Loader - Custom Field Templates

This work item loader supports custom field definitions through YAML template files, allowing you to map YAML input data to any Azure DevOps work item fields, including custom fields specific to your organization.

## 🎯 Overview

The template system allows you to:

- Define custom fields for different work item types (Feature, User Story, Task)
- Map YAML keys to Azure DevOps field paths
- Set default values and data types
- Mark fields as required or optional
- Support both built-in and custom Azure DevOps fields

## 📁 Files

- `ado.workitem-loader.py` - Main script with template support
- `templates.yaml` - YAML template configuration example
- `sample-backlog-with-custom-fields.yaml` - Sample input file with custom fields
- `README-templates.md` - This documentation

## 🚀 Quick Start

1. **Create a template file** (YAML format):

   ```yaml
   work_item_types:
     Feature:
       fields:
         - name: "Feature Value"
           azure_field_path: "Custom.FeatureValue"
           yaml_key: "FeatureValue"
           type: "string"
           required: false
           default: "Discovery"
   ```

2. **Update your YAML input file** to include the custom fields:

   ```yaml
   features:
     - Title: "My Feature"
       Description: "Feature description"
       FeatureValue: "Security"  # Custom field
   ```

3. **Run the script** with template file specified:

   ```python
   loader = AzureDevOpsWorkItemLoader(
       yaml_file_path="product.backlog.yaml",
       organization_url="https://dev.azure.com/myorg",
       project="MyProject",
       area_path="MyProject",
       iteration_path="MyProject", 
       personal_access_token="your_pat_here",
       template_file_path="work-item-templates.yaml"  # Add this line
   )
   ```

## 📋 Template File Structure

```yaml
work_item_types:
  Feature:                    # Work item type name
    description: "Optional description"
    fields:
      - name: "Display Name"           # Human-readable field name
        azure_field_path: "Custom.FieldName"  # Azure DevOps field path
        yaml_key: "YamlKey"           # Key to look for in YAML input
        type: "string"                # Data type: string, integer, float, boolean
        required: false               # Whether field is required
        default: "DefaultValue"       # Default value if not provided
        description: "Field purpose" # Optional documentation
```

## 🏷️ Field Types

- **string**: Text values
- **integer**: Whole numbers (e.g., priority levels)
- **float**: Decimal numbers (e.g., story points, hours)
- **boolean**: true/false values

## 🔧 Azure DevOps Field Paths

### System Fields (Standard)
- `System.Title` - Work item title
- `System.Description` - Work item description  
- `System.State` - Current state
- `System.AssignedTo` - Assigned user
- `System.AreaPath` - Area path
- `System.IterationPath` - Iteration path
- `System.Tags` - Tags (comma-separated)

### Microsoft VSTS Fields (Built-in)
- `Microsoft.VSTS.Common.Priority` - Priority (1-4)
- `Microsoft.VSTS.Common.Severity` - Severity (1-4)
- `Microsoft.VSTS.Common.AcceptanceCriteria` - Acceptance criteria
- `Microsoft.VSTS.Common.BusinessValue` - Business value score
- `Microsoft.VSTS.Common.Activity` - Activity type
- `Microsoft.VSTS.Scheduling.StoryPoints` - Story points
- `Microsoft.VSTS.Scheduling.OriginalEstimate` - Original estimate (hours)
- `Microsoft.VSTS.Scheduling.RemainingWork` - Remaining work (hours)
- `Microsoft.VSTS.Scheduling.CompletedWork` - Completed work (hours)
- `Microsoft.VSTS.Scheduling.StartDate` - Start date
- `Microsoft.VSTS.Scheduling.FinishDate` - Finish date

### Custom Fields (Organization-specific)
- `Custom.FieldName` - Generic custom field format
- `YourCompany.FieldName` - Company-prefixed custom fields

## 💡 Examples

### Feature with Custom Fields
```yaml
# Template definition
work_item_types:
  Feature:
    fields:
      - name: "Feature Value"
        azure_field_path: "Custom.FeatureValue"
        yaml_key: "FeatureValue"
        type: "string"
        default: "Discovery"

# YAML input
features:
  - Title: "User Authentication"
    Description: "Implement secure login"
    FeatureValue: "Security"  # Maps to Custom.FeatureValue
```

### User Story with Story Points
```yaml
# Template definition  
work_item_types:
  "User Story":
    fields:
      - name: "Story Points"
        azure_field_path: "Microsoft.VSTS.Scheduling.StoryPoints"
        yaml_key: "StoryPoints"
        type: "float"

# YAML input
user_stories:
  - Title: "Login Form"
    Description: "Create login interface"
    StoryPoints: 5  # Maps to Microsoft.VSTS.Scheduling.StoryPoints
```

### Task with Multiple Custom Fields
```yaml
# Template definition
work_item_types:
  Task:
    fields:
      - name: "Complexity"
        azure_field_path: "Custom.Complexity"
        yaml_key: "Complexity"
        type: "string"
        default: "Medium"
      - name: "Skill Required"
        azure_field_path: "Custom.SkillRequired"
        yaml_key: "SkillRequired"
        type: "string"

# YAML input
tasks:
  - Title: "Implement validation"
    Description: "Add form validation"
    Complexity: "High"           # Maps to Custom.Complexity
    SkillRequired: "Frontend"    # Maps to Custom.SkillRequired
```

## 🔍 Finding Azure DevOps Field Names

To find the exact field names in your Azure DevOps organization:

1. **Through Azure DevOps Web UI:**
   - Go to any work item
   - Right-click on a field → "Inspect Element"
   - Look for data attributes or field IDs

2. **Through REST API:**
   ```bash
   # Get work item fields
   curl -u :{PAT} https://dev.azure.com/{org}/{project}/_apis/wit/fields?api-version=7.1
   
   # Get work item type fields
   curl -u :{PAT} https://dev.azure.com/{org}/{project}/_apis/wit/workitemtypes/{type}/fields?api-version=7.1
   ```

3. **Through Process Template:**
   - Azure DevOps → Project Settings → Process
   - Select your process → Work item types → Select type → Fields

## ⚠️ Important Notes

1. **Custom Field Creation**: Custom fields must be created in Azure DevOps before using them in templates
2. **Field Permissions**: Ensure your PAT has permissions to write to all specified fields
3. **Data Validation**: Azure DevOps will validate field values according to field definitions
4. **Process Template**: Field availability depends on your project's process template (Agile, Scrum, etc.)

## 🐛 Troubleshooting

### "Field does not exist" errors
- Verify the Azure DevOps field path is correct
- Check if custom fields are properly created in your organization
- Ensure you have permissions to access the field

### Template not loading
- Check file path and permissions
- Validate YAML/JSON syntax
- Review console output for parsing errors

### Field mapping issues
- Verify `yaml_key` matches keys in your input file
- Check data type compatibility
- Review required field validations

## 📚 Additional Resources

- [Azure DevOps REST API Fields](https://docs.microsoft.com/en-us/rest/api/azure/devops/wit/fields)
- [Work Item Field Reference](https://docs.microsoft.com/en-us/azure/devops/boards/work-items/guidance/work-item-field)
- [Custom Fields Documentation](https://docs.microsoft.com/en-us/azure/devops/organizations/settings/work/customize-process-field)
