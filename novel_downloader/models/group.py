from dataclasses import dataclass, field
from typing import Any

from novel_downloader.models import DownloadMode


@dataclass
class Group:
    group_name:str
    novel_name:str
    file_path:str
    url:str
    mode:DownloadMode | None = None
    thread_count:int | None = None
    timeout:int | None = None
    delay:list[float] | None = None
    max_retry:int | None = None
    interval:int | None = None
    user_data_dir:str | None = None
    port:int | None = None
    headless:bool | None = None
    api_address:str | None = None
    api_key:str | None = None
    endpoint:dict[str,Any] | None = None
    params: list[str] | None = None
    cookies:dict[str, str] | None = None
    headers:dict[str, str] | None = None
    proxies:dict[str, str] | None = None
    save_method:Any | None = None

    def __hash__(self) -> int:
        return hash((self.group_name, self.novel_name))

@dataclass
class Groups:
    version:str|None = None
    groups:dict[str,list[Group]] = field(default_factory=dict)

    def find_group(self, group_name: str = None, novel_name: str = None, url:str = None) -> list[Group]:
        results = []
        if group_name is None and novel_name is None and url is None:
            return []
        for groups in self.groups.values():
            for group in groups:
                match = True
                if group_name is not None:
                    if group.group_name != group_name:
                        match = False

                if novel_name is not None:
                    if group.novel_name != novel_name:
                        match = False

                if url is not None:
                    if group.url != url:
                        match = False
                if match:
                    results.append(group)
        return results
    def update(self, group):
        to_remove = set()
        for groups_list in self.groups.values():
            for existing in groups_list:
                if existing.group_name == group.group_name or existing.url == group.url:
                    to_remove.add(existing)

        new_groups_dict = {}
        for grp_name, groups_list in self.groups.items():
            filtered = [g for g in groups_list if g not in to_remove]
            if filtered:
                new_groups_dict[grp_name] = filtered

        if group.group_name in new_groups_dict:
            new_groups_dict[group.group_name].append(group)
        else:
            new_groups_dict[group.group_name] = [group]

        self.groups = new_groups_dict
    def create_group(self,group_name:str):
        if group_name not in self.groups.keys():
            self.groups[group_name] = []