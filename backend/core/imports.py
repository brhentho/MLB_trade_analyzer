"""
Centralized Import Management System
Handles all complex import patterns with proper fallbacks and error handling
"""

import sys
import logging
from typing import Any, Dict, List, Optional, Type, Callable
from importlib import import_module
from functools import lru_cache
import inspect

logger = logging.getLogger(__name__)


class ImportManager:
    """
    Centralized import manager with intelligent fallback patterns
    and caching for improved performance
    """
    
    def __init__(self):
        self._import_cache: Dict[str, Any] = {}
        self._failed_imports: Dict[str, str] = {}
        self._import_paths: Dict[str, List[str]] = {}
    
    def register_import_paths(self, module_name: str, paths: List[str]) -> None:
        """
        Register multiple import paths for a module with fallback priority
        
        Args:
            module_name: Name of the module/component to import
            paths: List of import paths in order of preference
        """
        self._import_paths[module_name] = paths
    
    @lru_cache(maxsize=128)
    def safe_import(self, module_name: str, fallback_paths: Optional[List[str]] = None) -> Optional[Any]:
        """
        Safely import a module with intelligent fallback patterns
        
        Args:
            module_name: Module to import
            fallback_paths: Optional list of fallback paths
            
        Returns:
            Imported module or None if all imports fail
        """
        # Check cache first
        if module_name in self._import_cache:
            return self._import_cache[module_name]
        
        # Check if we've already failed to import this
        if module_name in self._failed_imports:
            logger.debug(f"Skipping import of {module_name}: {self._failed_imports[module_name]}")
            return None
        
        # Get import paths
        import_paths = fallback_paths or self._import_paths.get(module_name, [module_name])
        
        for path in import_paths:
            try:
                module = import_module(path)
                self._import_cache[module_name] = module
                logger.debug(f"Successfully imported {module_name} from {path}")
                return module
                
            except ImportError as e:
                logger.debug(f"Failed to import {module_name} from {path}: {e}")
                continue
            except Exception as e:
                logger.warning(f"Unexpected error importing {module_name} from {path}: {e}")
                continue
        
        # All imports failed
        error_msg = f"Failed to import {module_name} from any of: {import_paths}"
        self._failed_imports[module_name] = error_msg
        logger.error(error_msg)
        return None
    
    def safe_import_from(self, module_path: str, item_name: str, 
                        fallback_paths: Optional[List[str]] = None) -> Optional[Any]:
        """
        Safely import a specific item from a module
        
        Args:
            module_path: Module path to import from
            item_name: Specific item to import
            fallback_paths: Optional list of fallback module paths
            
        Returns:
            Imported item or None if import fails
        """
        cache_key = f"{module_path}.{item_name}"
        
        # Check cache first
        if cache_key in self._import_cache:
            return self._import_cache[cache_key]
        
        # Get import paths
        import_paths = fallback_paths or [module_path]
        
        for path in import_paths:
            try:
                module = import_module(path)
                if hasattr(module, item_name):
                    item = getattr(module, item_name)
                    self._import_cache[cache_key] = item
                    logger.debug(f"Successfully imported {item_name} from {path}")
                    return item
                else:
                    logger.debug(f"Module {path} does not have {item_name}")
                    
            except ImportError as e:
                logger.debug(f"Failed to import {path}: {e}")
                continue
            except Exception as e:
                logger.warning(f"Unexpected error importing {path}: {e}")
                continue
        
        error_msg = f"Failed to import {item_name} from {module_path} or fallbacks"
        self._failed_imports[cache_key] = error_msg
        logger.error(error_msg)
        return None
    
    def get_available_modules(self) -> Dict[str, Any]:
        """Get all successfully imported modules"""
        return self._import_cache.copy()
    
    def get_failed_imports(self) -> Dict[str, str]:
        """Get all failed import attempts with reasons"""
        return self._failed_imports.copy()
    
    def clear_cache(self) -> None:
        """Clear the import cache"""
        self._import_cache.clear()
        self._failed_imports.clear()
        # Clear the lru_cache as well
        self.safe_import.cache_clear()


class ToolImportManager:
    """
    Specialized import manager for CrewAI tools with Baseball Trade AI patterns
    """
    
    def __init__(self):
        self.import_manager = ImportManager()
        self._setup_tool_paths()
    
    def _setup_tool_paths(self) -> None:
        """Setup standard import paths for tools"""
        tool_mappings = {
            'mlb_rules_tool': [
                'tools.mlb_rules',
                'backend.tools.mlb_rules',
                '..tools.mlb_rules'
            ],
            'roster_tool': [
                'tools.roster_management',
                'backend.tools.roster_management', 
                '..tools.roster_management'
            ],
            'salary_tool': [
                'tools.salary_tools',
                'backend.tools.salary_tools',
                '..tools.salary_tools'
            ],
            'statcast_tool': [
                'tools.statcast_data',
                'backend.tools.statcast_data',
                '..tools.statcast_data'
            ],
            'traditional_stats_tool': [
                'tools.traditional_stats',
                'backend.tools.traditional_stats',
                '..tools.traditional_stats'
            ],
            'projection_tool': [
                'tools.projections',
                'backend.tools.projections',
                '..tools.projections'
            ],
            'defensive_tool': [
                'tools.defensive_metrics',
                'backend.tools.defensive_metrics',
                '..tools.defensive_metrics'
            ],
            'scouting_tool': [
                'tools.scouting_reports',
                'backend.tools.scouting_reports',
                '..tools.scouting_reports'
            ],
            'prospect_tool': [
                'tools.prospect_rankings',
                'backend.tools.prospect_rankings',
                '..tools.prospect_rankings'
            ]
        }
        
        for tool_name, paths in tool_mappings.items():
            self.import_manager.register_import_paths(tool_name, paths)
    
    def get_tool(self, tool_name: str) -> Optional[Any]:
        """
        Get a tool by name with automatic fallback handling
        
        Args:
            tool_name: Name of the tool to import
            
        Returns:
            Tool function/class or None if not available
        """
        if not tool_name.endswith('_tool'):
            tool_name = f"{tool_name}_tool"
        
        # Get the module paths for this tool
        if tool_name in self.import_manager._import_paths:
            module_paths = self.import_manager._import_paths[tool_name]
            
            # Try to import the tool from each path
            for module_path in module_paths:
                try:
                    # Extract the expected tool function name from module path
                    module_name = module_path.split('.')[-1]
                    expected_tool_name = f"{module_name}_tool"
                    
                    tool = self.import_manager.safe_import_from(
                        module_path, 
                        expected_tool_name, 
                        fallback_paths=module_paths
                    )
                    
                    if tool is not None:
                        return tool
                        
                except Exception as e:
                    logger.debug(f"Failed to get tool {tool_name} from {module_path}: {e}")
                    continue
        
        logger.warning(f"Tool {tool_name} not available")
        return None
    
    def get_all_available_tools(self) -> Dict[str, Any]:
        """Get all available tools"""
        available_tools = {}
        
        for tool_name in self.import_manager._import_paths.keys():
            tool = self.get_tool(tool_name)
            if tool is not None:
                available_tools[tool_name] = tool
        
        return available_tools


class ServiceImportManager:
    """
    Import manager for services with proper async/sync handling
    """
    
    def __init__(self):
        self.import_manager = ImportManager()
        self._setup_service_paths()
    
    def _setup_service_paths(self) -> None:
        """Setup service import paths"""
        service_mappings = {
            'supabase_service': [
                'services.supabase_service',
                'backend.services.supabase_service'
            ],
            'data_service': [
                'services.data_ingestion',
                'backend.services.data_ingestion'
            ],
            'statcast_service': [
                'services.statcast_service',
                'backend.services.statcast_service'
            ],
            'cache_service': [
                'services.cache_service',
                'backend.services.cache_service'
            ],
            'queue_service': [
                'services.queue_service',
                'backend.services.queue_service'
            ]
        }
        
        for service_name, paths in service_mappings.items():
            self.import_manager.register_import_paths(service_name, paths)
    
    def get_service(self, service_name: str) -> Optional[Any]:
        """Get a service with proper error handling"""
        if not service_name.endswith('_service'):
            service_name = f"{service_name}_service"
        
        module_paths = self.import_manager._import_paths.get(service_name, [])
        
        for module_path in module_paths:
            try:
                service = self.import_manager.safe_import_from(
                    module_path, 
                    service_name,
                    fallback_paths=module_paths
                )
                
                if service is not None:
                    return service
                    
            except Exception as e:
                logger.debug(f"Failed to get service {service_name} from {module_path}: {e}")
                continue
        
        logger.error(f"Service {service_name} not available")
        return None


# Global instances
import_manager = ImportManager()
tool_import_manager = ToolImportManager()
service_import_manager = ServiceImportManager()


def get_tool(tool_name: str) -> Optional[Any]:
    """Global function to get any tool"""
    return tool_import_manager.get_tool(tool_name)


def get_service(service_name: str) -> Optional[Any]:
    """Global function to get any service"""
    return service_import_manager.get_service(service_name)


def safe_import(module_name: str, fallback_paths: Optional[List[str]] = None) -> Optional[Any]:
    """Global function for safe imports"""
    return import_manager.safe_import(module_name, fallback_paths)


def check_availability() -> Dict[str, Any]:
    """Check availability of all managed imports"""
    return {
        'tools': tool_import_manager.get_all_available_tools(),
        'services': {
            name: service_import_manager.get_service(name) is not None
            for name in ['supabase', 'data', 'statcast', 'cache', 'queue']
        },
        'failed_imports': import_manager.get_failed_imports()
    }