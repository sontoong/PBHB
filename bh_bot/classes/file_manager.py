from typing import Dict,  Optional, Set
from pathlib import Path
from bh_bot.utils.helpers import resource_path


class FileManager:
    """Manages loading and detecting images from folder structures"""

    def __init__(self, base_path: str, cache_files: bool = True):
        """
        Initialize the file detection manager.

        Args:
            base_path: Base directory path for all file operations
            cache_files: Whether to cache loaded file lists for performance
        """
        self.base_path = Path(base_path)
        self.cache_files = cache_files
        self._file_cache: Dict[str, Dict[str, str]] = {}

    def load_files_from_folder(self, folder_path: str = "",
                               file_extensions: Optional[Set[str]] = None,
                               include_subdirs: bool = False,
                               refresh_cache: bool = False) -> Dict[str, str]:
        """
        Load all files from a specific folder.

        Args:
            folder_path: Relative path from base_path (empty string for base_path itself)
            file_extensions: Set of extensions to include (e.g., {'.png', '.jpg'}). 
                           If None, includes all files
            include_subdirs: Whether to recursively include subdirectories
            refresh_cache: Force reload even if cached

        Returns:
            Dict mapping file names (without extension) to full paths
        """
        # Create cache key
        cache_key = f"{folder_path}|{str(file_extensions)}|{include_subdirs}"

        if not refresh_cache and self.cache_files and cache_key in self._file_cache:
            return self._file_cache[cache_key]

        full_folder_path = self.base_path / folder_path if folder_path else self.base_path
        full_folder_path = resource_path(
            resource_folder_path=full_folder_path, resource_name="")
        full_folder_path = Path(full_folder_path)  # Ensure it's a Path object
        file_dict = {}

        if full_folder_path.exists() and full_folder_path.is_dir():
            if include_subdirs:
                # Recursive search
                pattern = "**/*" if file_extensions is None else "**/*.*"
                files = full_folder_path.glob(pattern)
            else:
                # Non-recursive search
                pattern = "*" if file_extensions is None else "*.*"
                files = full_folder_path.glob(pattern)

            for file_path in files:
                if file_path.is_file():
                    # Check extension if specified
                    if file_extensions is not None:
                        if file_path.suffix.lower() not in file_extensions:
                            continue

                    # Use stem (filename without extension) as key
                    name_without_ext = file_path.stem
                    file_dict[name_without_ext] = str(file_path)

        if self.cache_files:
            self._file_cache[cache_key] = file_dict

        return file_dict
