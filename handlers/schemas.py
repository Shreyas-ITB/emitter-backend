from pydantic import BaseModel, EmailStr, HttpUrl
from typing import List, Optional, Union
from fastapi import UploadFile

class UserSignup(BaseModel):
    username: str
    handle: str
    bio: str
    pronouns: str
    email: EmailStr
    password: str
    interests: List[str]
    socials: List[str]
    profile_picture: Optional[Union[UploadFile, str]] = None 

class HandleSchema(BaseModel):
    handle: str

class BioSchema(BaseModel):
    bio: str

class UserLogin(BaseModel):
    email_or_username: str
    password: str

class ResendVerificationRequest(BaseModel):
    email: str

class TokenData(BaseModel):
    token: str

class Interests(BaseModel):
    interests: List[str]

class PostCreateSchema(BaseModel):
    heading: str
    description: str
    image: Union[UploadFile, str]
    community_id: Optional[str] = None # Optional field for specifying a community  # Accepts file upload or a URL

class PostGetSchema(BaseModel):
    post_id: str  # ID of the post to retrieve
    community_id: Optional[str] = None

# Updated PostDeleteSchema
class PostDeleteSchema(BaseModel):
    post_id: str  # ID of the post to be deleted
    community_id: Optional[str] # Optional ID of the community to search for the post

class PostEditSchema(BaseModel):
    post_id: str  # ID of the post to edit
    heading: Optional[str] = None # Optional field for specifying
    description: Optional[str] = None # Optional field for specifying
    image: Optional[Union[UploadFile, str]] = None
    community_id: Optional[str] = None # Optional field for specifying the community

class CommentCreateSchema(BaseModel):
    post_id: str
    text: str
    community_id: Optional[str] = None

class CommentEditSchema(BaseModel):
    comment_id: str
    text: str
    community_id: Optional[str] = None

class CommentDeleteSchema(BaseModel):
    comment_id: str
    community_id: Optional[str] = None  # Optional community ID

class CommentLikeSchema(BaseModel):
    comment_id: str
    community_id: Optional[str] = None  # Optional community ID

class CommentDislikeSchema(BaseModel):
    comment_id: str
    community_id: Optional[str] = None  # Optional community ID

class PostReportSchema(BaseModel):
    post_id: str
    reason: str
    description: str
    community_id: Optional[str] = None  # Optional community ID

class CommentReportSchema(BaseModel):
    comment_id: str
    reason: str
    description: str
    community_id: Optional[str] = None  # Optional community ID

class CommunityCreateSchema(BaseModel):
    community_name: str
    community_description: str
    community_tags: List[str]
    posts_is_admin_only: Optional[bool] = False  # Optional boolean, defaults to False

class CommunityDeleteSchema(BaseModel):
    community_id: str

class RoleCreateSchema(BaseModel):
    community_id: str
    role_name: str
    role_colour: str

class RoleGiveSchema(BaseModel):
    user_id: str
    role_name: str
    role_colour: str

class RoleEditSchema(BaseModel):
    community_id: str
    role_name: str  # The original role name
    new_role_name: Optional[str] = None  # The new role name (optional)
    role_colour: str  # The new or unchanged role color

class RoleDeleteSchema(BaseModel):
    community_id: str
    role_name: str

class RoleAssignSchema(BaseModel):
    role_name: str
    user_id: str
    community_id: str

class CommunityActionSchema(BaseModel):
    community_id: str = None  # community_id is optional
    invitation_id: str = None  # invitation_id is optional

class CommunityPostsSchema(BaseModel):
    community_id: str
    posts: int

class CommunityReportSchema(BaseModel):
    community_id: str
    reason: str
    description: str

class CommunityModerationSchema(BaseModel):
    community_id: str
    user_id: str

class FollowUnfollowSchema(BaseModel):
    user_id: str  # The ID of the user to follow/unfollow

class ReportClearSchema(BaseModel):
    report_id: str

class AlgorithmRecommendPostsSchema(BaseModel):
    posts: int

class AlgorithmRecommendCommunitySchema(BaseModel):
    communities: int

class AlgorithmRecommendUsersSchema(BaseModel):
    users: int

class SocialLinksSchema(BaseModel):
    socials: list[HttpUrl]

class PronounsSchema(BaseModel):
    pronouns: str

class ChatRequestSchema(BaseModel):
    post_ids: Optional[List[str]] = None
    question: str
