import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
from datetime import datetime

@dataclass
class Feature:
    name: str
    description: str
    industry: str
    business_goal: str
    business_model: str
    analysis_result: Optional[Dict] = None
    created_at: str = datetime.now().isoformat()

@dataclass
class Project:
    name: str
    description: str
    industry: str
    business_goals: str
    target_market: str
    features: List[Feature] = None
    created_at: str = datetime.now().isoformat()

    def __post_init__(self):
        if self.features is None:
            self.features = []

    def add_feature(self, feature: Feature) -> None:
        """Add a new feature to the project"""
        self.features.append(feature)

    def remove_feature(self, feature_name: str) -> bool:
        """Remove a feature from the project"""
        initial_length = len(self.features)
        self.features = [f for f in self.features if f.name != feature_name]
        return len(self.features) < initial_length

    def get_feature(self, feature_name: str) -> Optional[Feature]:
        """Get a feature by name"""
        for feature in self.features:
            if feature.name == feature_name:
                return feature
        return None

    def to_dict(self) -> Dict:
        """Convert project to dictionary"""
        return asdict(self)

class ProjectManager:
    def __init__(self):
        self.projects: Dict[str, Project] = {}

    def create_project(self, name: str, description: str, industry: str, 
                      business_goals: str, target_market: str) -> Project:
        """Create a new project"""
        if name in self.projects:
            raise ValueError(f"Project '{name}' already exists")
        
        project = Project(
            name=name,
            description=description,
            industry=industry,
            business_goals=business_goals,
            target_market=target_market
        )
        self.projects[name] = project
        return project

    def get_project(self, name: str) -> Optional[Project]:
        """Get a project by name"""
        return self.projects.get(name)

    def list_projects(self) -> List[str]:
        """List all project names"""
        return list(self.projects.keys())

    def delete_project(self, name: str) -> bool:
        """Delete a project"""
        if name in self.projects:
            del self.projects[name]
            return True
        return False

    def add_feature_to_project(self, project_name: str, feature: Feature) -> bool:
        """Add a feature to a project"""
        project = self.get_project(project_name)
        if project:
            project.add_feature(feature)
            return True
        return False

    def get_project_features(self, project_name: str) -> List[Feature]:
        """Get all features for a project"""
        project = self.get_project(project_name)
        return project.features if project else []

    def compare_features(self, project_name: str) -> List[Dict]:
        """Compare features in a project using RICE scores"""
        project = self.get_project(project_name)
        if not project or not project.features:
            return []

        comparisons = []
        for feature in project.features:
            if feature.analysis_result and 'rice_scores' in feature.analysis_result:
                rice = feature.analysis_result['rice_scores']
                comparisons.append({
                    'name': feature.name,
                    'rice_score': rice['final_rice_score'],
                    'reach': rice['Reach']['value'],
                    'impact': rice['Impact']['value'],
                    'confidence': rice['Confidence']['value'],
                    'effort': rice['Effort']['value']
                })
        
        return sorted(comparisons, key=lambda x: x['rice_score'], reverse=True)
