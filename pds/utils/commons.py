def ssh_to_https_query_by_tag(ssh_repo_git, tag):
    # We receive something like this:
    # git@github.com:jclopeza/webapp.git
    # We have to get:
    # https://github.com/jclopeza/webapp/releases/tag/1.3.0-B6
    # 1.- I must obtain the user
    user = ssh_repo_git.split(":")[1].split("/")[0]
    # slug
    slug = ssh_repo_git.split("/")[1].split(".")[0]
    return "https://github.com/" + user + "/" + slug + "/tree/" + tag
