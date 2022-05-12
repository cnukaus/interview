### Input

a list of handles, default location is at parent folder


### Process

grab user information, and repos information, loop through repos to get max and total counts, on metrics specified by user

### Output

user level data stored as JSON file

repo summary data stored by line as text file

### ref

https://docs.github.com/en/rest/overview/other-authentication-methods#via-oauth-and-personal-access-tokens

https://developer.github.com/changes/2020-02-10-deprecating-auth-through-query-param/

[Implementing header `Authorisation: token <insert-token-here>` and for `Authentication` as well.]: https://docs.github.com/en/developers/apps/building-github-apps/identifying-and-authorizing-users-for-github-apps
