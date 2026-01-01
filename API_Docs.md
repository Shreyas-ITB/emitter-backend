# Emitter.dev API Developer documentation

- ``/signup``
    -
#### Arguments
```
username: string value (username of the user)
handle: string value (handle should be unique for every user)

bio: string value (the about me of the user)
pronouns: string value (should be given like They/Them, with a slash in the middle)

email: string value (email of the user, verification link will be sent to this email address)

password: string value (secure password of the user)

interests: string list value (should be a list of interests that the user likes to get posts recommended for)

socials: string list value (should be a list of other social media links of the user)

profile_picture: Can be a file upload, a URL string value or none (the profile picture can be uploaded or a URL can be used or this value can be none for the system to generate a profile picture)
```
#### Status codes and responses
```
StatusCode: 403, Response: This email has been banned from this platform

StatusCode: 400, Response: Email already registered

StatusCode: 400, Response: File size exceeds the 15 MB limit.

StatusCode: 400, Response: Error processing the uploaded image

StatusCode: 400, Response: Bio contains inappropriate language and is not allowed.

StatusCode: 400, Response: Handle is already taken. Please choose a different one.

StatusCode: 400, Response: Invalid profile picture URL.

StatusCode: 200, Response: User registered. Please verify your email.
```

- ``/auth/google``
    -
#### Description
This endpoint is used for google Oauth signup/login, you call this it opens up the google account pages for the user to proceed signing up or logging in. 

``/auth/google/callback`` is the callback endpoint for this endpoint.

```
StatusCode: 400 Response: Failed top fetch user from google

StatusCode: 403 Response: This email has been banned from the platform.

StatusCode: 200 Response: Login successful, user: user
```

- ``/auth/github``
    -
#### Description
This endpoint is used for github Oauth signup/login, you call this it opens up the github account pages for the user to proceed signing up or logging in. 

``/auth/github/callback`` is the callback endpoint for this endpoint.

```
StatusCode: 400 Response: Failed top fetch user from github

StatusCode: 403 Response: This email has been banned from the platform.

StatusCode: 200 Response: Login successful, user: user
```

- ``/auth/apple``
    -
#### Description
This endpoint is used for apple Oauth signup/login, you call this it opens up the apple account pages for the user to proceed signing up or logging in. 

``/auth/apple/callback`` is the callback endpoint for this endpoint.

```
StatusCode: 400 Response: Failed top fetch user from apple

StatusCode: 403 Response: This email has been banned from the platform.

StatusCode: 400 Response: Email is missing from Apple user info

StatusCode: 200 Response: Login successful, user: user
```

- ``/auth/discord``
    -
#### Description
This endpoint is used for discord Oauth signup/login, you call this it opens up the discord account pages for the user to proceed signing up or logging in. 

``/auth/discord/callback`` is the callback endpoint for this endpoint.

```
StatusCode: 400 Response: Failed top fetch user from discord

StatusCode: 403 Response: This email has been banned from the platform.

StatusCode: 200 Response: Login successful, user: user
```

For all the above Oauth endpoints the ENV must be configured with the right client_id and client_secret key values.

- ``/auth/verify/{verification_code}``
    -
#### Arguments
The only argument provided in the URL is the verification code. The code is only valid for 10 mins and can only be used once.

#### Status codes and responses
```
StatusCode: 200 Response: Email verified successfully
```

- ``/user/edithandle``
    - 
#### Arguments
```
handle: string value (new handle for the user)
```

This endpoint is there for the Oauth users, who do not get the option to enter their own value during the signup process as they get redirected to the callbacks.

#### Status codes and responses
```
StatusCode: 400 Response: Invalid access token payload

StatusCode: 400 Response: Inappropriate words is not allowed in handle

StatusCode: 400 Response: Handle is already taken. Please choose a different one.

StatusCode: 200 Response: Handle updated successfully
```

- ``/user/editbio``
    - 
#### Arguments
```
bio: string value (new bio for the user)
```

This endpoint is there for the Oauth users, who do not get the option to enter their own value during the signup process as they get redirected to the callbacks.

#### Status codes and responses
```
StatusCode: 400 Response: Invalid access token payload

StatusCode: 400 Response: Inappropriate words is not allowed in bio

StatusCode: 404 Response: User not found

StatusCode: 200 Response: Bio updated successfully
```

- ``/user/editpronouns``
    - 
#### Arguments
```
pronouns: string value (new pronouns for the user)
```
This endpoint is there for the Oauth users, who do not get the option to enter their own value during the signup process as they get redirected to the callbacks.

#### Status codes and responses
```
StatusCode: 400 Response: Invalid access token payload

StatusCode: 404 Response: User not found

StatusCode: 200 Response: Pronouns updated successfully for the user username
```

- ``/user/socials/add``
    -
#### Arguments
```
socials: list of httpURL (list of URLs for users socials)
```

#### Status codes and responses
```
StatusCode: 400 Response: Invalid access token payload

StatusCode: 404 Response: User not found

StatusCode: 400 Response: Invalid URL: link

StatusCode: 200 Response: Social links added successfully for user username
```

- ``/user/socials/remove``
    - 
#### Arguments
```
socials: list of httpURL (list of URLs for users socials)
```

#### Status codes and responses
```
StatusCode: 400 Response: Invalid access token payload

StatusCode: 404 Response: Invalid URL link

StatusCode: 400 Response: URL does not exist in your socials list

StatusCode: 200 Response: Social links removed successfully for user username
```

- ``/user/follow``
    -
#### Arguments
```
user_id: string value (the user_id of the user who you want to follow)
```

#### Status codes and responses
```
StatusCode: 400 Response: Invalid access token payload

StatusCode: 404 Response: Current user not found

StatusCode: 400 Response: You are already following this user

StatusCode: 200 Response: You are now following username
```
- ``/user/unfollow``
    -
#### Arguments
```
user_id: string value (the user_id of the user who you want to unfollow)
```

#### Status codes and responses
```
StatusCode: 400 Response: Invalid access token payload

StatusCode: 404 Response: Current user not found

StatusCode: 404 Response: User to unfollow not found

StatusCode: 400 Response: You are not following this user

StatusCode: 200 Response: You have unfollowed username
```

- ``/user/get``
    - 
#### Arguments
```
user_id: string value (the user_id of the user who you want the get the data about)
```

# Status code and responses
```
StatusCode: 400 Response: Invalid access token payload

StatusCode: 404 Response: User not found

StatuCode: 200 Response: returns the data of the user
```

- ``/login``
    -
#### Arguments
```
email_or_username: string value (the email or username of a registered user)
password: string value (the password of a registered user)
```

#### Status code and responses
```
StatusCode: 400 Response: Invalid credentials

StatusCode: 400 Response: Please verify your email before logging in

StatusCode: 200 Response: success True
```

- ``/resend-verification``
    - 
#### Arguments
```
email: string value (email of the registered user)
```

#### Status codes and responses
```
StatusCode: 404 Response: User not found

StatusCode: 400 Response: Your email is already verified

StatusCode: 200 Response: Verification email resent Please check your inbox
```
This endpoint is ratelimited and can only be used once every 5 minutes.

- ``/genauthtoken``
    -
This endpoint is used to generate authentication (access) tokens when expired using refresh tokens.
The refreshtoken is fetched from the cookies.

#### Status codes and responses
```
StatusCode: 400 Response: Refresh token missing

StatusCode: 401 Response: Invalid refresh token

StatusCode: 401 Response: Refresh token expired

StatusCode: 200 Response: returns new access token and saves it in the cookies
```

- ``/images/{image_id}``
    -
This is where the images stored in the database are shown, the uploaded profile pictures etc.. are given out in the form of URL.

#### Status codes and responses
```
StatusCode: 404 Response: Image not found

StatusCode: 200 Response: returns image
```

- ``/interests/add``
    - 
#### Arguments
```
interests: list of strings (interests, these interests are which you want to add to the users profile)
```

#### Status codes and responses
```
StatusCode: 400 Response: Invalid access token payload

StatusCode: 404 Response: User not found 

StatusCode: 400 Response: All interests already exists

StatusCode: 200 Response success true
```

- ``/interests/remove``
    -
#### Arguments
```
interests: list of strings (interests, these interests are which you want to remove from the users profile)
```

#### Status codes and responses
```
StatusCode: 400 Response: Invalid access token payload

StatusCode: 404 Response: User not found

StatusCode: 400 Response: No interests to delete

StatusCode: 404 Response: Some interests not found in the list list

StatusCode: 200 Response: success true
```

- ``/interests/get``
    -
#### Description
Returns a bunch of interests which are essentially tags the users can select and get the posts recommended on these selected interests

#### Status codes and responses
```
StatusCode: 200 Response: success returns all_interests
```

- ``/post/create``
    -
#### Arguments
```
heading: string value (heading of the post)

description: string value (description of the post)

image: URL or a file upload (thumbnail for the post)

community_id: Optional string value (should be provided when posting inside a community)
```

#### Status codes and responses
```
StatusCode: 400 Response: Invalid access token payload

StatusCode: 400 Response: Heading cannot exceed 250 characters

StatusCode: 400 Response: Description cannot exceed 1000 characters

StatusCode: 400 Response: The post content is flagged as spam

StatusCode: 400 Response: Invalid URL format for image

StatusCode: 400 Response: Invalid image format

StatusCode: 400 Response: The post contains too many inappropriate words (more than 6) and cannot be published

StatusCode: 400 Response: You cannot create a post with identical content more than once

StatusCode: 404 Response: Community not found

StatusCode: 404 Response: User profile not found

StatusCode: 400 Response: You must be a member of the community to post in it

StatusCode: 403 Response: Only Admins and Moderators are allowed to post in this community

StatusCode: 200 Response: Post created successfully
```

- ``/post/edit``
    -
#### Arguments
```
post_id: string value (the id of the post that you are trying to edit)

heading: Optional string argument if you are trying to edit the heading of the post.

description: Optional string argument if you are trying to edit the description of the post

image: Optional URL value or File upload if you are trying to edit the thumbnail of the post

community_id: Optional string argument if you are editing the post inside a community
```

#### Status codes and responses
```
StatusCode: 400 Response: Invalid access token payload

StatusCode: 404 Response: Post not found

StatusCode: 403 Response: You are not authorized to edit the post

StatusCode: 400 Response: No new data to update

StatusCode: 400 Response: Heading cannot exceed 250 characters

StatusCode: 400 Response: Description cannot exceed 1000 characters

StatusCode: 400 Response: No changes detected in the provided data 

StatusCode: 400 Response: The post heading is flagged as spam

StatusCode: 400 Response: The post description is flagged as spam

StatusCode: 400 Response: The post contains too many inappropriate words (more than 6) and cannot be updated

StatusCode: 404 Response: Community not found

StatusCode: 404 Response: Post not found in the specified community

StatusCode: 200 Response: Post updated successfully in the community

StatusCode: 200 Response: Post updated successfully
```

- ``/post/get``
    -
#### Arguments
```
post_id: string value (id of the post that you want to request)

community_id: Optional string argument (only to be given when a post inside the community is being requested)
```

#### Status codes and responses
```
StatusCode: 400 Response: Invalid access token payload

StatusCode: 404 Response: Community not found

StatusCode: 404 Response: Post not found in the specified community

StatusCode: 404 Response: Post not found

StatusCode: 404 Response: User not found

StatusCode: 200 Response: returns the post details
```

- ``/post/delete``
    -
#### Arguments
```
post_id: string value of the post ID that needs to be deleted

community_id: Optional string value of the post inside the community which needs to be deleted
```

#### Status codes and responses 
```
StatusCode: 400 Response: Invalid access token

StatusCode: 404 Response: Community not found

StatusCode: 404 Response: Post not found 

StatusCode: 403 Response: You are not authorized to delete this post

StatusCode: 200 Response: Post deleted successfully
```

- ``/post/like``
    -
#### Arguments
```
post_id: string value (id of the post that you want to like)

community_id: Optional string argument (only to be given when a post inside the community is being liked)
```

#### Status codes and responses
```
StatusCode: 400 Response: Invalid access token

StatusCode: 404 Response: Community not found

StatusCode: 404 Response: Post not found in the specified community

StatusCode: 200 Response: Like removed

StatusCode: 200 Response: Post liked
```

- ``/post/dislike``
    -
#### Arguments 
```
post_id: string value (id of the post that you want to dislike)

community_id: Optional string argument (only to be given when a post inside the community is being disliked)
```

#### Status codes and responses
```
StatusCode: 400 Response: Invalid access token payload

StatusCode: 404 Response: Community not found

StatusCode: 404 Response: Post not found in the specified community

StatusCode: 200 Response: Dislike removed

StatusCode: 200 Response: Post disliked
```

- ``/post/comment/create`` 
    -
#### Arguments
```
post_id: string value (the id of the post where you want to comment on)

text: string value (the text of the comment)

community_id: Optional string value (the id of the community if you are posting the comment inside a post inside a community)
```

#### Status codes and responses
```
StatusCode: 400 Response: Invalid access token payload

StatusCode: 404 Response: Community not found

StatusCode: 404 Response: Post not found in the specified community

StatusCode: 404 Response: Post not found

StatusCode: 400 Response: The comment is flagged as spam

StatusCode: 400 Response: The comment contains too many inappropriate words (more than 6) and cannot be created

StatusCode: 400 Response: You cannot post the same comment text multiple times

StatusCode: 200 Response: Comment added successfully
```

- ``/post/comment/edit``
    -
#### Arguments
```
comment_id: string value (the id of the comment which you want to edit)

text: string value (the new text value of the comment)

community_id: optional string value (id of the community where the post is located and needs to be edited)
```

#### Status codes and responses
```
StatusCode: 400 Response: Invalid access token payload

StatusCode: 404 Response: Community not found

StatusCode: 404 Response: Comment not found in the specified community

StatusCode: 404 Response: Comment not found

StatusCode: 400 Response: The comment is flagged as spam

StatusCode: 400 Response: The comment contains too many inappropriate words (more than 6) and cannot be edited

StatusCode: 403 Response: You are not authorized to edit this comment

StatusCode: 400 Response: No changes detected in the comment textr

StatusCode: 200 Response: Comment edited successfully
```

- ``/post/comment/delete``
    -
#### Arguments
```
comment_id: string value of the comment that needs to be deleted

community_id: Optional string value of the community id that the comment belongs to which needs to be deleted
```

#### Status codes and responses
```
StatusCode: 400 Response: Invalid access token payload

StatusCode: 404 Response: Community not found

StatusCode: 404 Response: Comment not found in the specified community

StatusCode: 404 Response: Comment not found

StatusCode: 403 Response: You are not authorized to delete this comment

StatusCode: 200 Response: Comment deleted successfully
```

- ``/comment/like``
    -
#### Arguments
```
comment_id: string value of the comment that needs to be liked

community_id: Optional string value if the comment is held inside the community 
```

#### Status codes and responses
```
StatusCode: 400 Response: Invalid access token payload

StatusCode: 404 Response: Community not found

StatusCode: 404 Response: Comment not found in the specified community

StatusCode: 404 Response: Comment not found

StatusCode: 200 Response: Comment liked/unliked successfully
```

- ``/comment/dislike``
    -
#### Arguments
```
comment_id: string value of the comment id that you want to dislike

community_id: Optional string value if you want to dislike a post inside the community 
```

#### Status codes and responses
```
StatusCode: 400 Response: Invalid access token payload

StatusCode: 404 Response: Community not found

StatusCode: 404 Response: Comment not found in the specified community

StatusCode: 404 Response: Comment not found

StatusCode: 200 Response: Comment disliked/undisliked successfully
```

- ``/post/report``
    -
#### Arguments
```
post_id: string value of the post id that you want to report

reason: string value (the reason why you want to report this post)

description: string value (the description for more clarity)

community_id: Optional string value if you want to report a post inside the community
```

#### Status code and responses
```
StatusCode: 400 Response: Invalid access token payload

StatusCode: 404 Response: User not found

StatusCode: 400 Response: Reason cannot exceed 250 characters

StatusCode: 400 Response: Description cannot exceed 1000 characters

StatusCode: 404 Response: Community not found

StatusCode: 404 Response: Post not found in the specified community

StatusCode: 404 Response: Post not found

StatusCode: 400 Response: You are reporting the same post too many times.

StatusCode: 200 Response: Report submitted successfully
```

- ``/comment/report``
    -
#### Arguments
```
comment_id: String value of the comment_id that is being reported

reason: String value (the reason why you want to report this comment)

description: String value (the description for more clarity)

community_id: Optional string value if you want to report a comment inside the community
```

#### Status code and responses
```
StatusCode: 400 Response: Invalid access token

StatusCode: 404 Response: User not found

StatusCode: 400 Response: Reason cannot exceed 250 characters

StatusCode: 400 Response: Description cannot exceed 1000 characters

StatusCode: 404 Response: Comment not found

StatusCode: 400 Response: You are reporting the same comment too many times

StatusCode: 200 Response: Report submitted successfully returns report_id
```

- ``/streak/restore``
    -
#### Description
This endpoint is used to restore the streak count of a user, it takes lumens as a cost to restore your streak

#### Status code and responses
```
StatusCode: 400 Response: Invalid access token payload

StatusCode: 404 Response: User not found

StatusCode: 400 Response: No previous streak data available

StatusCode: 400 Response: Your streak has not been reset; no restoration needed

StatusCode: 400 Response: Not enough lumens points to restore streak

StatusCode: 200 Response: Your streak has been restored to streak, 1 lumens point has been deducted.
```

- ``/community/create``
    -
#### Arguments
```
community_name: string value (the name of the community)

community_description: string value (the description of the community)

community_tags: list of strings (the tags for the community, recommend the same interests/categories that the /interests/get returns you)

posts_is_admin_only: Optional boolean value (default false) lets everyone post in the community if set to true
```

#### Status code and responses
```
StatusCode: 400 Response: Invalid access token payload

StatusCode: 400 Response: You have already created a community with the same name and description

StatusCode: 200 Response: success true, community created successfully
```

- ``/community/get``
    -
#### Arguments
```
community_id: string value (optional) the ID of the community

invitation_id: string value (optional) the community's invitation id
```

#### Status code and responses
```
StatusCode: 400 Response: Invalid access token payload

StatusCode: 403 Response: You are not a member of this community

StatusCode: 404 Response: Community not found

StatusCode: 403 Response: You must be the Admin, Owner or Moderator of the community to access this information

StatusCode: 200 Response: success true returns community details
```

- ``/community/posts``
    -
#### Arguments
```
community_id: string value (id of the community)

posts: integer value (returns the number of posts from the community latest to oldest)
```

#### Status code and responses
```
StatusCode: 400 Response: Invalid access token payload

StatusCode: 404 Response: Community not found

StatusCode: 404 Response: No posts available in this community

StatusCode: 200 Response: success true returns community_id and posts
```

- ``/community/role/create``
    -
#### Arguments
```
community_id: string value (id of the community)

role_name: string value (name of the role that the user wants to create)

role_colour: string value (the hex of the role colour that the user wants to keep)
```

#### Status code and responses
```
StatusCode: 400 Response: Invalid access token payload

StatusCode: 404 Response: Community not found

StatusCode: 403 Response: You are not autorized to create roles in this community

StatusCode: 400 Response: Role with this name already exists in the community

StatusCode: 400 Response: Role name contains inappropriate or foul language

StatusCode: 200 Response: Role created successfully in community community name 
```

- ``/community/role/edit``
    - 
#### Arguments
```
community_id: String value (the id of the community)

role_name: string value (name of the role you want to edit)

new_role_name: Optional string value if you are trying to edit the name of the role

role_colour: string value (new role colour or the exact old role colour if you are editing the name only)
```

#### Status code and responses
```
StatusCode: 400 Response: Invalid access token payload

StatusCode: 404 Response: Community not found

StatusCode: 400 Response: You are not authorized to edit roles in this community

StatusCode: 403 Response: Cannot change the name of system_created roles like Admin or Moderator

StatusCode: 400 Response: The new role name is the same as the current role name, No new changes were made

StatusCode: 400 Response: Role name contains inappropriate or foul language

StatusCode: 200 Response: success true returns role name updated
```

- ``/community/role/add``
    -
### Arguments
```
role_name: string value (the name of the role that is being assigned)

user_id: string value (the user id of the person who the role is being assigned to)

community_id: string value (the community id)
```

#### Status code and responses
```
StatusCode: 400 Response: Invalid access token payload

StatusCode: 404 Response: Community not found

StatusCode: 400 Response: You are not a member of this community and cannot add roles

StatusCode: 403 Response: You are not authorized to add roles in this community

StatusCode: 400 Response: Role does not exist in this community

StatusCode: 400 Response: Target user is not a member of this community

StatusCode: 400 Response: User already has this role in the community

StatusCode: 200 Response: Role successfully added to the user
```

- ``/community/role/remove``
    -
#### Arguments
```
role_name: string value (the name of the role that is being removed)

user_id: string value (the user_id of the person who the role is being removed from)

community_id: string value (the community id)
```

#### Status code and responses
```
StatusCode: 400 Response: Invalid access token payload

StatusCode: 404 Response: Community not found

StatusCode: 403 Response: You are not a member of this community and cannot remove roles

StatusCode: 403 Response: You are not authorized to remove roles in this community

StatusCode: 400 Response: Target user is not a member of this community

StatusCode: 400 Response: User does not have this role in the community

StatusCode: 400 Response: Moderators cannot remove the Admin's role

StatusCode: 200 Response: Role successfully removed from the user
```

- ``/community/role/delete``
    -
#### Arguments
```
community_id: string value (the community id)

role_name: string value (the name of the role that needs to be deleted)
```

#### Status code and responses
```
StatusCode: 400 Response: Invalid access token payload

StatusCode: 404 Response: Community not found

StatusCode: 403 Response: You are not a memvber of this community

StatusCode: 403 Response: You are not authorized to delete roles in this community

StatusCode: 404 Response: Role not found in the community's created_roles list

StatusCode: 403 Response: System created roles like Admin and Moderator cannot be deleted

StatusCode: 200 Response: Role deleted successfully from community
```

- ``/community/delete``
    -

#### Arguments
```
community_id: string value (the community id)
```

#### Status code and responses
```
StatusCode: 400 Response: Invalid access token payload

StatusCode: 404 Response: Community not found

StatusCode: 403 Response: You are not a member of this community

StatusCode: 403 Response: You are not authorized to delete this community

StatusCode: 200 Response: Community 'community_name' has been deleted successfully.
```

- ``/community/join``
    -

#### Arguments
```
community_id: string value (the community id, optional)

invitation_id: string value (the invitation id, optional)
```

#### Status code and responses
```
StatusCode: 400 Response: Invalid access token payload

StatusCode: 404 Response: Community not found

StatusCode: 404 Response: User profile not found

StatusCode: 400 Response: User is already a member of this community

StatusCode: 403 Response: You are banned from this community and cannot join.

StatusCode: 200 Response: Successfully joined the community 'community_name'
```

- ``/community/leave``
    -

#### Arguments
```
community_id: string value (the community id, optional)

invitation_id: string value (the invitation id, optional)
```

#### Status code and responses
```
StatusCode: 400 Response: Invalid access token payload

StatusCode: 404 Response: Community not found

StatusCode: 404 Response: User profile not found

StatusCode: 400 Response: User is not a member of this community

StatusCode: 403 Response: Admin of the community cannot leave the community they created

StatusCode: 200 Response: Successfully left the community 'community_name'
```

- ``/community/report``
    -

#### Arguments
```
community_id: string value (the community id)

reason: string value (reason for reporting the community, maximum 250 characters)

description: string value (detailed description of the report, maximum 1000 characters)
```

#### Status code and responses
```
StatusCode: 400 Response: Invalid access token payload

StatusCode: 404 Response: User not found

StatusCode: 400 Response: Reason cannot exceed 250 characters

StatusCode: 400 Response: Description cannot exceed 1000 characters

StatusCode: 404 Response: Community not found

StatusCode: 400 Response: You are reporting the same community too many times.

StatusCode: 200 Response: Report submitted successfully
```

- ``/community/ban``
    -

#### Arguments
```
community_id: string value (the community id)

user_id: string value (the user id of the target user to be banned)
```

#### Status code and responses
```
StatusCode: 400 Response: Invalid access token payload

StatusCode: 404 Response: You are not a member of this community

StatusCode: 403 Response: You don't have Moderator or Admin privileges

StatusCode: 400 Response: User is not a member of this community

StatusCode: 200 Response: User has been banned from the community
```

- ``/community/unban``
    -

#### Arguments
```
community_id: string value (the community id)

user_id: string value (the user id of the target user to be unbanned)
```

#### Status code and responses
```
StatusCode: 400 Response: Invalid access token payload

StatusCode: 404 Response: You are not a member of this community

StatusCode: 403 Response: You don't have Moderator or Admin privileges

StatusCode: 400 Response: User is not banned from this community

StatusCode: 200 Response: User has been unbanned from the community
```

- ``/community/kick``
    -

#### Arguments
```
community_id: string value (the community id)

user_id: string value (the user id of the target user to be kicked)
```

#### Status code and responses
```
StatusCode: 400 Response: Invalid access token payload

StatusCode: 404 Response: You are not a member of this community

StatusCode: 403 Response: You don't have Moderator or Admin privileges

StatusCode: 400 Response: User is not a member of this community

StatusCode: 200 Response: User has been kicked from the community
```

- ``/team/report/get``
    -

#### Description
This endpoint is used by team members to get the reports submitted by users

#### Status code and responses
```
StatusCode: 404 Response: User not found

StatusCode: 403 Response: You are not authorized to access this endpoint

StatusCode: 200 Response: { "success": true, "reports": [list of report objects] }
```

- ``/team/report/clear``
    -

#### Arguments
```
report_id: string value (the unique ID of the report to be cleared)
```

#### Status code and responses
```
StatusCode: 400 Response: Report ID is required.

StatusCode: 404 Response: User not found.

StatusCode: 403 Response: You are not authorized to access this endpoint.

StatusCode: 404 Response: Report not found.

StatusCode: 200 Response: { "success": true, "message": "Report has been cleared successfully." }
```

- ``/team/user/warn``
    -
#### Arguments
```
user_id: string value (the user_id of the person who needs to be warn)
```

#### Status code and responses
```
StatusCode: 404 Response: User not found

StatusCode: 403 Response: Unauthorized access

StatusCode: 404 Response: User to warn not found

StatusCode: 403 Response: Cannot warn another team member

StatusCode: 200 Response: User username has been successfully warned
```

- ``/team/user/ban``
    -
#### Arguments
```
user_id: string value (the user_id of the person who needs to be banned from the platform)
```

#### Status code and responses
```
StatusCode: 404 Response: User not found

StatusCode: 403 Response: Unauthorized access

StatusCode: 403 Response: Cannot ban another team member

StatusCode: 200 Response: success true user username has been successfully banned
```

- ``/team/role/add``
    -
#### Arguments
```
user_id: string value (the user_id of the person to whom the role needs to be added)  
role_name: string value (the name of the role to assign to the user)  
role_colour: string value (the color associated with the role, typically in hex format)  
```

#### Status code and responses
```
StatusCode: 404 Response: User profile not found  

StatusCode: 403 Response: You are not authorized to use this endpoint  

StatusCode: 404 Response: Target user not found  

StatusCode: 400 Response: Role with this name already exists for the user  

StatusCode: 400 Response: Role name contains inappropriate or foul language  

StatusCode: 200 Response: success true message "Role '{role_name}' added successfully to user '{username}'" role {role details}  
```

- ``/team/role/remove``
    -
#### Arguments
```
user_id: string value (the user_id of the person from whom the role needs to be removed)  
role_name: string value (the name of the role to be removed from the user)  
role_colour: string value (the color associated with the role, required for input but not used for removal)  
```

#### Status code and responses
```
StatusCode: 404 Response: User profile not found  

StatusCode: 403 Response: You are not authorized to use this endpoint  

StatusCode: 404 Response: Target user not found  

StatusCode: 404 Response: Role not found for the user  

StatusCode: 200 Response: success true message "Role '{role_name}' removed successfully from user '{username}'"  
```

- ``/algorithm/recommend/posts``
    -
#### Arguments
```
posts: integer value (the number of posts to be recommended)
```

#### Status code and responses
```
StatusCode: 403 Response: Invalid access token payload

StatusCode: 404 Response: No recommended posts found

StatusCode: 200 Response: returns recommended posts
```

- ``/algorithm/recommend/communities``
    -
#### Arguments
```
communities: integer value (the number of communities to be recommended) 
```

#### Status code and responses
```
StatusCode: 403 Response: Invalid access token payload

StatusCode: 404 Response: No recommended communities found

StatusCode: 200 Response: returns recommended communities
```

- ``/algorithm/recommend/users``
    -
#### Arguments
```
users: integer value (the number of users to be recommended)
```

#### Status code and responses
```
StatusCode: 403 Response: Invalid access token payload

StatusCode: 404 Response: No recommended users found

StatusCode: 200 Response: returns recommended users
```

- ``/spark/chat``
    -
#### Arguments
```
post_ids: Optional string list value (the id of the post or the ids of the post if the user wants to ask about a post or none)

question: string value (the question)
```

#### Status code and responses
```
StatusCode: 403 Response: Invalid access token payload

StatusCode: 400 Response: Profanity detected in the question

StatusCode: 200 Response: returns answer
```
