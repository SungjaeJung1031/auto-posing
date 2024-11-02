from typing import Optional

from utils.bvh import Skeleton


class RenderObject:
    def __init__(self, skeleton: Optional[Skeleton] = None) -> None:
        self.skeleton = skeleton
        
class Renderer:
    def __init__(self) -> None:
        pass