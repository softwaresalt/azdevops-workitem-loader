"""
Script to load features, user stories, and tasks into Azure DevOps from YAML files.
Python equivalent of ado.yaml-import.ps1 using azure-devops library

Configuration:
- All configuration parameters are loaded from 'parameters.yaml' in the script directory
- The parameters.yaml file must exist in the same directory as this script
- See parameters.yaml for configuration options including Azure DevOps settings and file paths

Prerequisites:
- azure-devops package installed (pip install azure-devops)
- PyYAML package installed (pip install PyYAML)
- Personal Access Token (PAT) for authentication (configured in parameters.yaml)
- parameters.yaml file with all required configuration parameters
- Optional: markdown package for Markdown to HTML conversion (pip install markdown)
"""

import yaml
import sys
import os
from typing import Dict, List, Any, Optional

try:
    import markdown
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False

from azure.devops.connection import Connection
from azure.devops.v7_1.work_item_tracking.models import (
    JsonPatchOperation, 
    WorkItem, 
    WorkItemRelation
)
from msrest.authentication import BasicAuthentication

class AzureDevOpsWorkItemLoader:
    def __init__(self, yaml_file_path: str, organization_url: str, project: str, 
                 area_path: str, iteration_path: str, personal_access_token: str,
                 template_file_path: Optional[str] = None, enable_markdown: bool = False):
        """
        Initialize the work item loader.
        
        Args:
            yaml_file_path: Path to the YAML file containing work items
            organization_url: Azure DevOps organization URL (e.g., https://dev.azure.com/myorg)
            project: Azure DevOps project name
            area_path: Area path for work items
            iteration_path: Iteration path for work items
            personal_access_token: Personal Access Token for authentication
            template_file_path: Optional path to template file (YAML) defining work item fields
            enable_markdown: Enable Markdown to HTML conversion for description fields
        """
        self.yaml_file_path = yaml_file_path
        self.organization_url = organization_url
        self.project = project
        self.area_path = area_path
        self.iteration_path = iteration_path
        self.template_file_path = template_file_path
        self.enable_markdown = enable_markdown
        self.connection = None
        self.work_item_tracking_client = None
        self.work_item_templates = {}
        
        # Check markdown support
        if self.enable_markdown and not MARKDOWN_AVAILABLE:
            print("WARNING: Markdown support requested but 'markdown' package not installed.")
            print("Install with: pip install markdown")
            print("Falling back to plain text for descriptions.")
            self.enable_markdown = False
        elif self.enable_markdown:
            print("✓ Markdown support enabled - descriptions will be converted to HTML")
        
        # Load templates if provided
        if template_file_path:
            self.work_item_templates = self.load_work_item_templates()
        
        # Initialize connection
        self._initialize_connection(personal_access_token)
        
    def convert_markdown_to_html(self, text: str) -> str:
        """
        Convert Markdown text to HTML if Markdown support is enabled.
        
        Args:
            text: Input text (may contain Markdown)
            
        Returns:
            HTML formatted text if Markdown is enabled, otherwise original text
        """
        if not self.enable_markdown or not text:
            return text
            
        if not MARKDOWN_AVAILABLE:
            return text
            
        try:
            # Convert Markdown to HTML
            # Extensions for better Azure DevOps compatibility
            html = markdown.markdown(
                text, 
                extensions=[
                    'markdown.extensions.tables',      # Support tables
                    'markdown.extensions.fenced_code', # Support code blocks
                    'markdown.extensions.nl2br',       # Convert newlines to <br>
                    'markdown.extensions.toc'          # Support table of contents
                ]
            )
            return html
        except Exception as e:
            print(f"Warning: Failed to convert Markdown to HTML: {e}")
            print("Falling back to plain text")
            return text
        
    def _initialize_connection(self, personal_access_token: str) -> None:
        """Initialize connection to Azure DevOps using Personal Access Token."""
        if not personal_access_token:
            raise ValueError("Personal Access Token is required for authentication")
        
        try:
            # Use provided PAT with BasicAuthentication
            credentials = BasicAuthentication('', personal_access_token)
            print("Using Personal Access Token for authentication")
            
            # Create connection
            self.connection = Connection(base_url=self.organization_url, creds=credentials)
            self.work_item_tracking_client = self.connection.clients.get_work_item_tracking_client()
            
            print("Successfully connected to Azure DevOps")
            
            # Test the connection by trying to get project info
            try:
                print(f"Testing access to project: {self.project}")
                core_client = self.connection.clients.get_core_client()
                project_info = core_client.get_project(self.project)
                print(f"✓ Access confirmed for project: {project_info.name}")
            except Exception as access_error:
                print(f"✗ Access test failed: {access_error}")
                raise
                raise Exception(f"User not authorized to access project '{self.project}' in organization '{self.organization_url}'. "
                              f"Please ensure the user has appropriate permissions or use a Personal Access Token with correct scope.")
            
        except Exception as e:
            print(f"Failed to initialize Azure DevOps connection: {e}")
            raise

    def load_work_item_templates(self) -> Dict[str, Any]:
        """
        Load work item templates from YAML file.
        
        Returns:
            Dictionary containing template definitions for different work item types
        """
        if not self.template_file_path:
            print("No template file specified - using default field mappings only")
            return {}
            
        if not os.path.exists(self.template_file_path):
            print(f"Template file not found: {self.template_file_path}")
            print("Note: Relative paths are resolved relative to the script directory")
            return {}
        
        try:
            with open(self.template_file_path, 'r', encoding='utf-8') as file:
                file_extension = os.path.splitext(self.template_file_path)[1].lower()
                
                if file_extension not in ['.yaml', '.yml']:
                    print(f"Unsupported template file format: {file_extension}. Use .yaml or .yml")
                    return {}
                
                templates = yaml.safe_load(file)
                
                print(f"Successfully loaded work item templates from: {self.template_file_path}")
                
                # Validate template structure
                if not isinstance(templates, dict):
                    print("Warning: Template file should contain a dictionary at root level")
                    return {}
                
                # Print loaded work item types
                if 'work_item_types' in templates:
                    work_item_types = templates['work_item_types']
                    print(f"Available work item types in template: {list(work_item_types.keys())}")
                    
                    # Validate each work item type has fields defined
                    for wit_name, wit_config in work_item_types.items():
                        if 'fields' not in wit_config:
                            print(f"Warning: Work item type '{wit_name}' missing 'fields' definition")
                        else:
                            field_count = len(wit_config['fields'])
                            print(f"  - {wit_name}: {field_count} custom fields defined")
                
                return templates
                
        except yaml.YAMLError as e:
            print(f"Error parsing YAML template file: {e}")
            return {}
        except Exception as e:
            print(f"Error loading template file: {e}")
            return {}

    def get_work_item_fields(self, work_item_type: str, work_item_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get field mappings for a work item based on templates and input data.
        
        Args:
            work_item_type: Type of work item (e.g., 'Feature', 'User Story', 'Task')
            work_item_data: Input data from YAML file
            
        Returns:
            Dictionary of field paths and values to apply to the work item
        """
        additional_fields = {}
        
        # Check if we have templates loaded
        if not self.work_item_templates or 'work_item_types' not in self.work_item_templates:
            return additional_fields
        
        work_item_types = self.work_item_templates['work_item_types']
        
        # Find template for this work item type (case-insensitive)
        template_config = None
        for template_type, config in work_item_types.items():
            if template_type.lower() == work_item_type.lower():
                template_config = config
                break
        
        if not template_config or 'fields' not in template_config:
            return additional_fields
        
        # Map fields from template
        template_fields = template_config['fields']
        
        for field_config in template_fields:
            field_name = field_config.get('name')
            field_path = field_config.get('azure_field_path')
            yaml_key = field_config.get('yaml_key', field_name)  # Default to field name if no yaml_key specified
            field_type = field_config.get('type', 'string')
            required = field_config.get('required', False)
            default_value = field_config.get('default')
            
            if not field_name or not field_path:
                print(f"Warning: Invalid field configuration for {work_item_type}: {field_config}")
                continue
            
            # Get value from work item data
            field_value = work_item_data.get(yaml_key)
            
            # Handle missing required fields
            if required and field_value is None:
                if default_value is not None:
                    field_value = default_value
                    print(f"Using default value for required field '{field_name}': {default_value}")
                else:
                    print(f"Warning: Required field '{field_name}' not found in work item data")
                    continue
            
            # Skip if no value and not required
            if field_value is None:
                continue
            
            # Type conversion
            try:
                if field_type == 'integer':
                    field_value = int(field_value)
                elif field_type == 'float':
                    field_value = float(field_value)
                elif field_type == 'boolean':
                    field_value = bool(field_value)
                elif field_type == 'string':
                    field_value = str(field_value)
                # For other types, keep as-is
                
                additional_fields[field_path] = field_value
                print(f"Mapped field: {yaml_key} -> {field_path} = {field_value}")
                
            except (ValueError, TypeError) as e:
                print(f"Warning: Type conversion failed for field '{field_name}': {e}")
                continue
        
        return additional_fields
    
    def load_yaml_data(self) -> Optional[Dict[str, Any]]:
        """Load and parse the YAML file."""
        try:
            with open(self.yaml_file_path, 'r', encoding='utf-8') as file:
                data = yaml.safe_load(file)
                print(f"YAML file found: {self.yaml_file_path}")
                return data
        except FileNotFoundError:
            print(f"YAML file not found: {self.yaml_file_path}")
            return None
        except yaml.YAMLError as e:
            print(f"Error parsing YAML file: {e}")
            return None
    
    def create_work_item_patch_document(self, work_item_type: str, title: str, 
                                      description: str, **additional_fields) -> List[JsonPatchOperation]:
        """Create a patch document for work item creation."""
        
        # Convert description to HTML if Markdown is enabled
        processed_description = self.convert_markdown_to_html(description)
        
        patch_document = [
            JsonPatchOperation(
                op="add",
                path="/fields/System.Title",
                value=title
            ),
            JsonPatchOperation(
                op="add",
                path="/fields/System.WorkItemType",
                value=work_item_type
            ),
            JsonPatchOperation(
                op="add",
                path="/fields/System.Description",
                value=processed_description
            ),
            JsonPatchOperation(
                op="add",
                path="/fields/System.AreaPath",
                value=self.area_path
            ),
            JsonPatchOperation(
                op="add",
                path="/fields/System.IterationPath",
                value=self.iteration_path
            )
        ]
        
        # Add any additional fields
        for field_path, field_value in additional_fields.items():
            patch_document.append(
                JsonPatchOperation(
                    op="add",
                    path=f"/fields/{field_path}",
                    value=field_value
                )
            )
        
        return patch_document
    
    def create_feature(self, feature: Dict[str, Any]) -> Optional[int]:
        """Create a Feature work item."""
        title = feature.get('Title', '')
        description = feature.get('Description', '')
        
        print(f"Creating Feature: {title}")
        
        try:
            # Get template-based field mappings
            template_fields = self.get_work_item_fields("Feature", feature)
            
            patch_document = self.create_work_item_patch_document(
                work_item_type="Feature",
                title=title,
                description=description,
                **template_fields
            )
            
            work_item = self.work_item_tracking_client.create_work_item(
                document=patch_document,
                project=self.project,
                type="Feature"
            )
            
            feature_id = work_item.id
            print(f"Successfully created Feature with ID: {feature_id}")
            return feature_id
            
        except Exception as e:
            print(f"Failed to create feature '{title}': {e}")
            return None
    
    def create_user_story(self, story: Dict[str, Any], feature_id: int) -> Optional[int]:
        """Create a User Story work item."""
        title = story.get('Title', '')
        description = story.get('Description', '')
        acceptance_criteria = story.get('Acceptance_Criteria', '')
        
        print(f"  Creating User Story: {title}")
        
        if not acceptance_criteria or acceptance_criteria.strip() == "":
            acceptance_criteria = "Acceptance criteria to be defined"
        
        # Convert acceptance criteria to HTML if Markdown is enabled
        processed_acceptance_criteria = self.convert_markdown_to_html(acceptance_criteria)
        
        print(f"    Acceptance Criteria Length: {len(acceptance_criteria)}")
        print(f"    First 200 chars: {acceptance_criteria[:200]}")
        if self.enable_markdown and processed_acceptance_criteria != acceptance_criteria:
            print(f"    ✓ Converted Markdown to HTML for acceptance criteria")
        
        try:
            # Start with default fields for User Story
            additional_fields = {
                "Microsoft.VSTS.Common.AcceptanceCriteria": processed_acceptance_criteria
            }
            
            # Get template-based field mappings and merge with default fields
            template_fields = self.get_work_item_fields("User Story", story)
            additional_fields.update(template_fields)
            
            patch_document = self.create_work_item_patch_document(
                work_item_type="User Story",
                title=title,
                description=description,
                **additional_fields
            )
            
            work_item = self.work_item_tracking_client.create_work_item(
                document=patch_document,
                project=self.project,
                type="User Story"
            )
            
            story_id = work_item.id
            print(f"  Successfully created User Story with ID: {story_id} (with acceptance criteria)")
            
            # Add parent-child link to feature
            self.add_parent_child_link(story_id, feature_id)
            print(f"  Linked Story {story_id} to Feature {feature_id}")
            
            return story_id
            
        except Exception as e:
            print(f"  Failed to create story '{title}': {e}")
            return None
    
    def create_task(self, task: Dict[str, Any], story_id: int) -> Optional[int]:
        """Create a Task work item."""
        title = task.get('Title', '')
        description = task.get('Description', '')
        activity = task.get('Activity', 'Development')
        remaining_work = task.get('Remaining_Work', 0)
        
        print(f"    Creating Task: {title}")
        
        try:
            # Start with default fields for Task
            additional_fields = {
                "Microsoft.VSTS.Common.Activity": activity,
                "Microsoft.VSTS.Scheduling.RemainingWork": remaining_work
            }
            
            # Get template-based field mappings and merge with default fields
            template_fields = self.get_work_item_fields("Task", task)
            additional_fields.update(template_fields)
            
            patch_document = self.create_work_item_patch_document(
                work_item_type="Task",
                title=title,
                description=description,
                **additional_fields
            )
            
            work_item = self.work_item_tracking_client.create_work_item(
                document=patch_document,
                project=self.project,
                type="Task"
            )
            
            task_id = work_item.id
            print(f"    Successfully created Task with ID: {task_id}")
            
            # Add parent-child link to user story
            self.add_parent_child_link(task_id, story_id)
            print(f"    Linked Task {task_id} to Story {story_id}")
            
            return task_id
            
        except Exception as e:
            print(f"    Failed to create task '{title}': {e}")
            return None
    
    def add_parent_child_link(self, child_id: int, parent_id: int) -> bool:
        """Add a parent-child relationship between work items."""
        try:
            # Create the relation patch document
            patch_document = [
                JsonPatchOperation(
                    op="add",
                    path="/relations/-",
                    value={
                        "rel": "System.LinkTypes.Hierarchy-Reverse",
                        "url": f"{self.organization_url}/{self.project}/_apis/wit/workItems/{parent_id}",
                        "attributes": {
                            "comment": "Parent-child link created by work item loader"
                        }
                    }
                )
            ]
            
            self.work_item_tracking_client.update_work_item(
                document=patch_document,
                id=child_id,
                project=self.project
            )
            
            return True
            
        except Exception as e:
            print(f"Failed to add parent-child link (child: {child_id}, parent: {parent_id}): {e}")
            return False
    
    def process_work_items(self) -> bool:
        """Process all work items from the YAML file."""
        # Load YAML data
        work_items_data = self.load_yaml_data()
        if not work_items_data:
            return False
        
        # Process features
        features = work_items_data.get('features', [])
        if not features:
            print("No features found in YAML file")
            return False
        
        try:
            for feature in features:
                # Create feature
                feature_id = self.create_feature(feature)
                if not feature_id:
                    continue
                
                # Process user stories for this feature
                user_stories = feature.get('user_stories', [])
                for story in user_stories:
                    story_id = self.create_user_story(story, feature_id)
                    if not story_id:
                        continue
                    
                    # Process tasks for this user story (if they exist)
                    tasks = story.get('tasks', [])
                    for task in tasks:
                        self.create_task(task, story_id)
            
            print("Work item creation completed successfully!")
            return True
            
        except Exception as e:
            print(f"An error occurred during processing: {e}")
            return False


def load_parameters() -> Dict[str, Any]:
    """Load configuration parameters from parameters.yaml file in the script directory."""
    # Get the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parameters_file = os.path.join(script_dir, "parameters.yaml")
    
    if not os.path.exists(parameters_file):
        print(f"ERROR: parameters.yaml file not found at: {parameters_file}")
        print("Please create a parameters.yaml file in the same directory as this script.")
        print("See the README for the expected format.")
        sys.exit(1)
    
    try:
        with open(parameters_file, 'r', encoding='utf-8') as file:
            parameters = yaml.safe_load(file)
            
        if not parameters:
            print("ERROR: parameters.yaml file is empty or invalid")
            sys.exit(1)
            
        return parameters
        
    except yaml.YAMLError as e:
        print(f"ERROR: Failed to parse parameters.yaml file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Failed to load parameters.yaml file: {e}")
        sys.exit(1)


def main():
    """Main function to run the work item loader."""
    # Load configuration from parameters.yaml
    print("Loading configuration from parameters.yaml...")
    parameters = load_parameters()
    
    # Extract Azure DevOps configuration
    azure_config = parameters.get('azure_devops', {})
    file_config = parameters.get('file_paths', {})
    env_config = parameters.get('environment_variables', {})
    formatting_config = parameters.get('formatting', {})
    
    # Get Azure DevOps settings
    organization_url = azure_config.get('organization_url')
    project = azure_config.get('project')
    area_path = azure_config.get('area_path')
    iteration_path = azure_config.get('iteration_path')
    
    # Get file paths
    yaml_file_path = file_config.get('yaml_file_path')
    template_file_path = file_config.get('template_file_path')
    
    # Get formatting options
    enable_markdown = formatting_config.get('enable_markdown', False)
    
    # Get Personal Access Token with environment variable fallback
    personal_access_token = azure_config.get('personal_access_token')
    if env_config.get('use_env_for_pat', False) or personal_access_token in [None, '', 'your_pat_token_here']:
        env_pat = os.environ.get('AZURE_DEVOPS_PAT')
        if env_pat:
            personal_access_token = env_pat
            print("Using Personal Access Token from AZURE_DEVOPS_PAT environment variable")
        elif personal_access_token in [None, '', 'your_pat_token_here']:
            print("ERROR: Please set your Personal Access Token!")
            print(f"Option 1: Update personal_access_token in parameters.yaml")
            print(f"Option 2: Set AZURE_DEVOPS_PAT environment variable")
            print(f"Go to: {organization_url}/_usersSettings/tokens")
            print("Create a token with 'Work Items (Read & Write)' scope")
            sys.exit(1)
    
    # Override with environment variables if requested
    if env_config.get('use_env_for_yaml_path', False):
        env_yaml_path = os.environ.get('YAML_FILE_PATH')
        if env_yaml_path:
            yaml_file_path = env_yaml_path
            print("Using YAML file path from YAML_FILE_PATH environment variable")
    
    if env_config.get('use_env_for_template_path', False):
        env_template_path = os.environ.get('TEMPLATE_FILE_PATH')
        if env_template_path:
            template_file_path = env_template_path
            print("Using template file path from TEMPLATE_FILE_PATH environment variable")
    
    # Resolve relative paths to be relative to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Resolve YAML file path
    if yaml_file_path and not os.path.isabs(yaml_file_path):
        yaml_file_path = os.path.join(script_dir, yaml_file_path)
        print(f"Resolved relative YAML file path to: {yaml_file_path}")
    
    # Resolve template file path
    if template_file_path and not os.path.isabs(template_file_path):
        template_file_path = os.path.join(script_dir, template_file_path)
        print(f"Resolved relative template file path to: {template_file_path}")
    
    # Validate required parameters
    required_params = {
        'organization_url': organization_url,
        'project': project,
        'area_path': area_path,
        'iteration_path': iteration_path,
        'yaml_file_path': yaml_file_path,
        'personal_access_token': personal_access_token
    }
    
    missing_params = [param for param, value in required_params.items() if not value]
    if missing_params:
        print("ERROR: Missing required parameters in parameters.yaml:")
        for param in missing_params:
            print(f"  - {param}")
        sys.exit(1)
    
    print(f"Configuration loaded successfully:")
    print(f"  Organization: {organization_url}")
    print(f"  Project: {project}")
    print(f"  YAML file: {yaml_file_path}")
    print(f"  Template file: {template_file_path if template_file_path else 'None (using defaults)'}")
    print(f"  Markdown support: {'Enabled' if enable_markdown else 'Disabled'}")
    print(f"  Personal Access Token: {'*' * (len(personal_access_token) - 4) + personal_access_token[-4:] if personal_access_token else 'Not set'}")
    
    try:
        # Create and run the loader
        print("\nInitializing Azure DevOps connection...")
        loader = AzureDevOpsWorkItemLoader(
            yaml_file_path=yaml_file_path,
            organization_url=organization_url,
            project=project,
            area_path=area_path,
            iteration_path=iteration_path,
            personal_access_token=personal_access_token,
            template_file_path=template_file_path,
            enable_markdown=enable_markdown
        )
        
        print("Starting work item processing...")
        success = loader.process_work_items()
        if success:
            print("\n✅ All work items processed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Failed to process work items.")
            sys.exit(1)
            
    except Exception as e:
        error_msg = str(e)
        print(f"\n❌ Failed to initialize or run work item loader: {e}")
        
        if "TF400813" in error_msg or "not authorized" in error_msg:
            print("\n🔐 AUTHORIZATION ERROR:")
            print("The current user doesn't have access to the Azure DevOps organization/project.")
            print("\nPossible solutions:")
            print(f"1. Ensure your account has access to: {organization_url}")
            print(f"2. Ensure your account has 'Basic' or higher access in the '{project}' project")
            print("3. Verify your Personal Access Token is valid and has the correct scopes:")
            print(f"   - Go to: {organization_url}/_usersSettings/tokens")
            print("   - Create token with 'Work Items (Read & Write)' scope")
            print("   - Update personal_access_token in parameters.yaml")
        else:
            print("\nAuthentication troubleshooting:")
            print(f"Create a Personal Access Token at: {organization_url}/_usersSettings/tokens")
            print("Required scopes: Work Items (Read & Write)")
            print("Update personal_access_token in parameters.yaml or set AZURE_DEVOPS_PAT environment variable")
        sys.exit(1)


if __name__ == "__main__":
    main()