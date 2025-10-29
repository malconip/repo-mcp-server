"""
Database layer for Emperion Knowledge Base
"""
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import (
    create_engine, Column, String, DateTime, Integer,
    Text, JSON, Index, text
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from config import config
from models import FileKnowledge, SearchQuery, IndexStats, DependencyGraph

Base = declarative_base()


class FileIndex(Base):
    """Database model for file index"""
    __tablename__ = 'file_index'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    path = Column(String(500), unique=True, nullable=False, index=True)
    repo = Column(String(100), nullable=False, index=True)
    file_type = Column(String(50), nullable=False, index=True)
    technology = Column(String(50), nullable=False, index=True)
    
    summary = Column(Text, nullable=False)
    key_elements = Column(JSON, nullable=False, default=list)
    dependencies = Column(JSON, nullable=False, default=list)
    dependents = Column(JSON, nullable=False, default=list)
    tags = Column(JSON, nullable=False, default=list)
    
    content_hash = Column(String(64), nullable=False)
    indexed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    file_metadata = Column(JSON, nullable=False, default=dict)
    
    # Indexes for better query performance
    __table_args__ = (
        Index('idx_repo_filetype', 'repo', 'file_type'),
        Index('idx_technology', 'technology'),
        Index('idx_indexed_at', 'indexed_at'),
    )


class DatabaseManager:
    """Manage database operations"""
    
    def __init__(self):
        self.engine = create_engine(config.DATABASE_URL)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
    def init_db(self):
        """Initialize database tables"""
        Base.metadata.create_all(self.engine)
        print("✅ Database tables created")
        
    def get_session(self) -> Session:
        """Get database session"""
        return self.SessionLocal()
    
    # ==================== INDEXING ====================
    
    def index_file(self, file_knowledge: FileKnowledge) -> bool:
        """Index a single file"""
        session = self.get_session()
        try:
            # Check if file already exists
            existing = session.query(FileIndex).filter_by(path=file_knowledge.path).first()
            
            if existing:
                # Update existing
                existing.repo = file_knowledge.repo
                existing.file_type = file_knowledge.file_type.value
                existing.technology = file_knowledge.technology.value
                existing.summary = file_knowledge.summary
                existing.key_elements = file_knowledge.key_elements
                existing.dependencies = file_knowledge.dependencies
                existing.dependents = file_knowledge.dependents
                existing.tags = file_knowledge.tags
                existing.content_hash = file_knowledge.content_hash
                existing.indexed_at = datetime.utcnow()
                existing.file_metadata = file_knowledge.file_metadata
            else:
                # Create new
                new_file = FileIndex(
                    path=file_knowledge.path,
                    repo=file_knowledge.repo,
                    file_type=file_knowledge.file_type.value,
                    technology=file_knowledge.technology.value,
                    summary=file_knowledge.summary,
                    key_elements=file_knowledge.key_elements,
                    dependencies=file_knowledge.dependencies,
                    dependents=file_knowledge.dependents,
                    tags=file_knowledge.tags,
                    content_hash=file_knowledge.content_hash,
                    file_metadata=file_knowledge.file_metadata
                )
                session.add(new_file)
            
            session.commit()
            return True
            
        except Exception as e:
            session.rollback()
            print(f"❌ Error indexing file {file_knowledge.path}: {e}")
            return False
        finally:
            session.close()
    
    def index_batch(self, files: List[FileKnowledge]) -> Dict[str, int]:
        """Index multiple files"""
        results = {"success": 0, "failed": 0}
        
        for file in files:
            if self.index_file(file):
                results["success"] += 1
            else:
                results["failed"] += 1
        
        return results
    
    # ==================== SEARCH ====================
    
    def search_knowledge(self, query: SearchQuery) -> List[FileIndex]:
        """Search for files matching query"""
        session = self.get_session()
        try:
            q = session.query(FileIndex)
            
            # Text search in summary and key_elements
            search_filter = text(
                "(summary ILIKE :query OR "
                "EXISTS (SELECT 1 FROM json_array_elements_text(key_elements) elem WHERE elem ILIKE :query) OR "
                "EXISTS (SELECT 1 FROM json_array_elements_text(tags) tag WHERE tag ILIKE :query))"
            )
            q = q.filter(search_filter.bindparams(query=f"%{query.query}%"))
            
            # Apply filters
            if query.file_types:
                q = q.filter(FileIndex.file_type.in_([ft.value for ft in query.file_types]))
            
            if query.technologies:
                q = q.filter(FileIndex.technology.in_([t.value for t in query.technologies]))
            
            if query.repos:
                q = q.filter(FileIndex.repo.in_(query.repos))
            
            if query.tags:
                # Filter by tags (at least one match)
                tag_filter = text(
                    "EXISTS (SELECT 1 FROM json_array_elements_text(tags) tag WHERE tag = ANY(:tags))"
                )
                q = q.filter(tag_filter.bindparams(tags=query.tags))
            
            # Order by most recent
            q = q.order_by(FileIndex.indexed_at.desc())
            
            # Limit results
            q = q.limit(query.limit)
            
            return q.all()
            
        finally:
            session.close()
    
    def get_file_context(self, path: str) -> Optional[FileIndex]:
        """Get complete context for a specific file"""
        session = self.get_session()
        try:
            return session.query(FileIndex).filter_by(path=path).first()
        finally:
            session.close()
    
    def find_related(self, path: str, limit: int = 10) -> List[FileIndex]:
        """Find files related to the given path"""
        session = self.get_session()
        try:
            # Get the source file
            source = session.query(FileIndex).filter_by(path=path).first()
            if not source:
                return []
            
            # Find files with similar tags or in same repo
            q = session.query(FileIndex).filter(
                FileIndex.path != path
            )
            
            # Same repo
            q = q.filter(FileIndex.repo == source.repo)
            
            # Order by same technology first, then by date
            q = q.order_by(
                (FileIndex.technology == source.technology).desc(),
                FileIndex.indexed_at.desc()
            )
            
            return q.limit(limit).all()
            
        finally:
            session.close()
    
    def search_by_type(
        self,
        file_type: str,
        repo: Optional[str] = None,
        limit: int = 50
    ) -> List[FileIndex]:
        """Search files by type"""
        session = self.get_session()
        try:
            q = session.query(FileIndex).filter_by(file_type=file_type)
            
            if repo:
                q = q.filter_by(repo=repo)
            
            q = q.order_by(FileIndex.indexed_at.desc())
            return q.limit(limit).all()
            
        finally:
            session.close()
    
    # ==================== ANALYSIS ====================
    
    def get_stats(self) -> IndexStats:
        """Get statistics about indexed knowledge"""
        session = self.get_session()
        try:
            total = session.query(FileIndex).count()
            
            # Files by type
            by_type = {}
            for row in session.query(
                FileIndex.file_type,
                text("COUNT(*) as count")
            ).group_by(FileIndex.file_type).all():
                by_type[row.file_type] = row.count
            
            # Files by repo
            by_repo = {}
            for row in session.query(
                FileIndex.repo,
                text("COUNT(*) as count")
            ).group_by(FileIndex.repo).all():
                by_repo[row.repo] = row.count
            
            # Files by technology
            by_tech = {}
            for row in session.query(
                FileIndex.technology,
                text("COUNT(*) as count")
            ).group_by(FileIndex.technology).all():
                by_tech[row.technology] = row.count
            
            # Last indexed
            last = session.query(FileIndex.indexed_at).order_by(
                FileIndex.indexed_at.desc()
            ).first()
            
            # Total dependencies
            total_deps = session.query(
                text("SUM(json_array_length(dependencies)) as total")
            ).scalar() or 0
            
            return IndexStats(
                total_files=total,
                files_by_type=by_type,
                files_by_repo=by_repo,
                files_by_technology=by_tech,
                last_indexed=last[0] if last else None,
                total_dependencies=total_deps
            )
            
        finally:
            session.close()
    
    def analyze_dependencies(self, path: str, max_depth: int = 3) -> DependencyGraph:
        """Analyze dependency graph for a file"""
        session = self.get_session()
        try:
            file = session.query(FileIndex).filter_by(path=path).first()
            if not file:
                raise ValueError(f"File not found: {path}")
            
            # Get direct dependencies and dependents
            dependencies = file.dependencies or []
            dependents = file.dependents or []
            
            return DependencyGraph(
                root=path,
                dependencies=dependencies,
                dependents=dependents,
                depth=1  # TODO: Implement recursive depth analysis
            )
            
        finally:
            session.close()


# Global database manager instance
db = DatabaseManager()
