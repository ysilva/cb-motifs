from dataclasses import dataclass
from datetime import datetime


@dataclass
class Session:
    unit_id: int
    posted_at: datetime
    owner_user_name: str
    owner_comment: str
    num_likes: int
    num_bullying_comments: int
    num_comments: int
    main_victim: str
