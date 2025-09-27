# Azure DevOps Work Item Loader

This script loads features, user stories, and tasks into Azure DevOps from a YAML file using configuration parameters from a `parameters.yaml` file.

## Configuration

The script expects a `parameters.yaml` file in the same directory as the script. This file contains all the configuration parameters needed to run the work item loader.

### Required Configuration File: `parameters.yaml`

Create a `parameters.yaml` file in the same directory as `ado.workitem-loader.py` with the following structure:

```yaml
# Azure DevOps Configuration
azure_devops:
  organization_url: "https://dev.azure.com/yourorg"
  project: "YourProject"
  area_path: "YourProject"
  iteration_path: "YourProject"
  personal_access_token: "your_pat_token_here"

# File Paths Configuration
file_paths:
  yaml_file_path: "path/to/your/work-items.yaml"
  template_file_path: "path/to/your/work-item-templates.yaml"  # Optional

# Optional: Environment Variables
environment_variables:
  use_env_for_pat: false
  use_env_for_yaml_path: false
  use_env_for_template_path: false
```

### Configuration Parameters

#### Azure DevOps Settings
- `organization_url`: Your Azure DevOps organization URL (e.g., https://dev.azure.com/myorg)
- `project`: Azure DevOps project name
- `area_path`: Area path for work items (usually the project name)
- `iteration_path`: Iteration path for work items (usually the project name)
- `personal_access_token`: Personal Access Token with "Work Items (Read & Write)" scope

#### File Paths

- `yaml_file_path`: Path to the YAML file containing work items to import (absolute or relative to script directory)
- `template_file_path`: Optional path to template file for custom field definitions (absolute or relative to script directory)

#### Environment Variables Support
You can optionally use environment variables instead of hardcoded values:

- Set `use_env_for_pat: true` to use `AZURE_DEVOPS_PAT` environment variable
- Set `use_env_for_yaml_path: true` to use `YAML_FILE_PATH` environment variable  
- Set `use_env_for_template_path: true` to use `TEMPLATE_FILE_PATH` environment variable

## Usage

1. **Create parameters.yaml**: Copy the sample parameters.yaml and update with your values
2. **Set up Personal Access Token**: 
   - Go to `https://dev.azure.com/yourorg/_usersSettings/tokens`
   - Create a token with "Work Items (Read & Write)" scope
   - Update `personal_access_token` in parameters.yaml
3. **Run the script**:
   ```bash
   python ado.workitem-loader.py
   ```

## Security Notes

- Keep your `parameters.yaml` file secure and never commit it to version control with real tokens
- Consider using environment variables for sensitive data like Personal Access Tokens
- Add `parameters.yaml` to your `.gitignore` file

## Example parameters.yaml

```yaml
azure_devops:
  organization_url: "https://dev.azure.com/datacognition"
  project: "Work-Item-Loader-Agile"
  area_path: "Work-Item-Loader-Agile"
  iteration_path: "Work-Item-Loader-Agile"
  personal_access_token: "your_actual_pat_token_here"

file_paths:
  yaml_file_path: "C:\\Users\\username\\Documents\\product.backlog.yaml"
  template_file_path: "work-item-templates.yaml"

environment_variables:
  use_env_for_pat: false
  use_env_for_yaml_path: false
  use_env_for_template_path: false
```

## Prerequisites

- Python 3.7+
- azure-devops package: `pip install azure-devops`
- PyYAML package: `pip install PyYAML`
- Valid Azure DevOps Personal Access Token
- `parameters.yaml` configuration file

## Error Troubleshooting

If you get authentication errors:
1. Verify your Personal Access Token is valid and has the correct scopes
2. Ensure your account has access to the Azure DevOps organization and project
3. Check that the organization URL and project name are correct in parameters.yaml
