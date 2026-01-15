"""
Terraform Analyzer - Analyze infrastructure configuration
"""

import os
import re
from typing import Dict, List, Optional
from pathlib import Path

try:
    import hcl2
    HCL2_AVAILABLE = True
except ImportError:
    HCL2_AVAILABLE = False

from langchain_openai import ChatOpenAI
from app.core.config import settings


class TerraformAnalyzer:
    """
    Analyzes Terraform configuration files to understand
    infrastructure and its connection to the application.
    """
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            openai_api_key=settings.OPENAI_API_KEY,
            temperature=0.1
        )
    
    async def analyze(self, path: str, include_modules: bool = True) -> Dict:
        """
        Perform comprehensive analysis of Terraform configuration.
        """
        tf_files = self._find_tf_files(path)
        
        if not tf_files:
            return {
                "error": "No Terraform files found",
                "path": path
            }
        
        result = {
            "files": len(tf_files),
            "resources": await self.list_resources(path),
            "modules": await self.list_modules(path) if include_modules else [],
            "variables": await self.list_variables(path),
            "outputs": await self._list_outputs(path),
            "providers": await self._list_providers(path)
        }
        
        result["summary"] = await self._generate_summary(result)
        
        return result
    
    async def list_resources(self, path: str) -> List[Dict]:
        """
        List all Terraform resources in the configuration.
        """
        resources = []
        tf_files = self._find_tf_files(path)
        
        for tf_file in tf_files:
            try:
                content = self._read_tf_file(tf_file)
                
                # Parse resources using regex (fallback if hcl2 not available)
                resource_pattern = r'resource\s+"([^"]+)"\s+"([^"]+)"\s*{'
                matches = re.findall(resource_pattern, content)
                
                for resource_type, resource_name in matches:
                    resources.append({
                        "type": resource_type,
                        "name": resource_name,
                        "file": os.path.relpath(tf_file, path)
                    })
                
                # Also try parsing with hcl2 if available
                if HCL2_AVAILABLE:
                    try:
                        with open(tf_file, 'r') as f:
                            parsed = hcl2.load(f)
                        
                        for resource in parsed.get('resource', []):
                            for res_type, res_config in resource.items():
                                for res_name in res_config.keys():
                                    if not any(r['type'] == res_type and r['name'] == res_name 
                                              for r in resources):
                                        resources.append({
                                            "type": res_type,
                                            "name": res_name,
                                            "file": os.path.relpath(tf_file, path)
                                        })
                    except:
                        pass
                        
            except Exception as e:
                continue
        
        return resources
    
    async def list_modules(self, path: str) -> List[Dict]:
        """
        List all Terraform modules and their relationships.
        """
        modules = []
        tf_files = self._find_tf_files(path)
        
        for tf_file in tf_files:
            try:
                content = self._read_tf_file(tf_file)
                
                # Parse modules
                module_pattern = r'module\s+"([^"]+)"\s*{([^}]+)}'
                matches = re.findall(module_pattern, content, re.DOTALL)
                
                for module_name, module_body in matches:
                    # Extract source
                    source_match = re.search(r'source\s*=\s*"([^"]+)"', module_body)
                    source = source_match.group(1) if source_match else "unknown"
                    
                    modules.append({
                        "name": module_name,
                        "source": source,
                        "file": os.path.relpath(tf_file, path)
                    })
                    
            except Exception as e:
                continue
        
        return modules
    
    async def list_variables(self, path: str) -> List[Dict]:
        """
        List all Terraform variables and their usage.
        """
        variables = []
        tf_files = self._find_tf_files(path)
        
        for tf_file in tf_files:
            try:
                content = self._read_tf_file(tf_file)
                
                # Parse variables
                var_pattern = r'variable\s+"([^"]+)"\s*{([^}]*)}'
                matches = re.findall(var_pattern, content, re.DOTALL)
                
                for var_name, var_body in matches:
                    # Extract type and default
                    type_match = re.search(r'type\s*=\s*(\S+)', var_body)
                    default_match = re.search(r'default\s*=\s*([^\n]+)', var_body)
                    desc_match = re.search(r'description\s*=\s*"([^"]*)"', var_body)
                    
                    variables.append({
                        "name": var_name,
                        "type": type_match.group(1) if type_match else "any",
                        "default": default_match.group(1).strip() if default_match else None,
                        "description": desc_match.group(1) if desc_match else None,
                        "file": os.path.relpath(tf_file, path)
                    })
                    
            except Exception as e:
                continue
        
        return variables
    
    async def _list_outputs(self, path: str) -> List[Dict]:
        """List all Terraform outputs."""
        outputs = []
        tf_files = self._find_tf_files(path)
        
        for tf_file in tf_files:
            try:
                content = self._read_tf_file(tf_file)
                
                output_pattern = r'output\s+"([^"]+)"\s*{([^}]*)}'
                matches = re.findall(output_pattern, content, re.DOTALL)
                
                for output_name, output_body in matches:
                    value_match = re.search(r'value\s*=\s*([^\n]+)', output_body)
                    desc_match = re.search(r'description\s*=\s*"([^"]*)"', output_body)
                    
                    outputs.append({
                        "name": output_name,
                        "value": value_match.group(1).strip() if value_match else None,
                        "description": desc_match.group(1) if desc_match else None,
                        "file": os.path.relpath(tf_file, path)
                    })
                    
            except:
                continue
        
        return outputs
    
    async def _list_providers(self, path: str) -> List[Dict]:
        """List all Terraform providers."""
        providers = []
        tf_files = self._find_tf_files(path)
        
        for tf_file in tf_files:
            try:
                content = self._read_tf_file(tf_file)
                
                provider_pattern = r'provider\s+"([^"]+)"\s*{'
                matches = re.findall(provider_pattern, content)
                
                for provider_name in matches:
                    if provider_name not in [p["name"] for p in providers]:
                        providers.append({
                            "name": provider_name,
                            "file": os.path.relpath(tf_file, path)
                        })
                    
            except:
                continue
        
        return providers
    
    async def map_application_links(self, path: str) -> Dict:
        """
        Map how Terraform resources connect to the application.
        Infrastructure → Cloud Resources → Services → APIs → Frontend
        """
        resources = await self.list_resources(path)
        outputs = await self._list_outputs(path)
        
        # Categorize resources by layer
        layers = {
            "infrastructure": [],
            "cloud_resources": [],
            "services": [],
            "api_gateway": [],
            "frontend": []
        }
        
        resource_categories = {
            "infrastructure": ["aws_vpc", "aws_subnet", "aws_security_group", 
                             "google_compute_network", "azurerm_virtual_network"],
            "cloud_resources": ["aws_rds", "aws_dynamodb", "aws_s3", "aws_sqs",
                               "google_sql_database", "azurerm_storage_account"],
            "services": ["aws_ecs", "aws_lambda", "aws_eks", "google_cloud_run",
                        "azurerm_kubernetes_cluster", "aws_instance"],
            "api_gateway": ["aws_api_gateway", "aws_apigatewayv2", "google_api_gateway"],
            "frontend": ["aws_cloudfront", "aws_s3_bucket_website", "google_compute_url_map"]
        }
        
        for resource in resources:
            res_type = resource["type"]
            categorized = False
            
            for layer, types in resource_categories.items():
                if any(t in res_type for t in types):
                    layers[layer].append(resource)
                    categorized = True
                    break
            
            if not categorized:
                layers["cloud_resources"].append(resource)
        
        # Identify links through outputs
        links = []
        for output in outputs:
            links.append({
                "output": output["name"],
                "connects_to": "application",
                "value_type": self._infer_output_type(output)
            })
        
        return {
            "layers": layers,
            "links": links,
            "flow": "Terraform Config → Cloud Provider → Resources → Services → API → Frontend"
        }
    
    async def explain(self, path: str) -> str:
        """
        Generate a human-readable summary of the infrastructure.
        """
        tf_files = self._find_tf_files(path)
        
        if not tf_files:
            return "No Terraform configuration found in the specified path."
        
        # Collect all TF content
        all_content = []
        for tf_file in tf_files[:10]:  # Limit files
            try:
                content = self._read_tf_file(tf_file)
                rel_path = os.path.relpath(tf_file, path)
                all_content.append(f"=== {rel_path} ===\n{content[:3000]}")
            except:
                continue
        
        prompt = f"""Analyze this Terraform configuration and provide a clear explanation of the infrastructure.

{chr(10).join(all_content)}

Provide:
1. **Overview**: What infrastructure is being provisioned?
2. **Cloud Provider**: Which cloud provider(s) are used?
3. **Main Resources**: What are the key resources being created?
4. **Architecture**: How do the resources connect and work together?
5. **Application Connection**: How might this infrastructure support an application?

Write in a clear, readable format suitable for developers who need to understand the infrastructure."""

        response = await self.llm.ainvoke(prompt)
        return response.content
    
    async def _generate_summary(self, analysis: Dict) -> str:
        """Generate a summary of the Terraform analysis."""
        return f"""Infrastructure Summary:
- {len(analysis['resources'])} resources across {analysis['files']} files
- {len(analysis['modules'])} modules referenced
- {len(analysis['variables'])} input variables
- {len(analysis['outputs'])} outputs defined
- Providers: {', '.join([p['name'] for p in analysis['providers']]) or 'None detected'}"""
    
    def _find_tf_files(self, path: str) -> List[str]:
        """Find all Terraform files in a path."""
        tf_files = []
        
        if os.path.isfile(path) and path.endswith('.tf'):
            return [path]
        
        if not os.path.isdir(path):
            return []
        
        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if d not in ['.terraform', '.git']]
            
            for f in files:
                if f.endswith('.tf'):
                    tf_files.append(os.path.join(root, f))
        
        return tf_files
    
    def _read_tf_file(self, file_path: str) -> str:
        """Read a Terraform file."""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    
    def _infer_output_type(self, output: Dict) -> str:
        """Infer the type of connection from an output."""
        name = output["name"].lower()
        
        if "endpoint" in name or "url" in name:
            return "API Endpoint"
        if "arn" in name:
            return "AWS Resource ARN"
        if "id" in name:
            return "Resource ID"
        if "connection" in name or "host" in name:
            return "Connection String"
        if "key" in name or "secret" in name:
            return "Credential"
        
        return "Configuration Value"

