def get_user_role(user):
    user_group = user.groups.values_list('name', flat='True')
    if len(user_group) == 1:
        if user_group[0] == 'Admin':
            return 'Admin'
        elif user_group[0] == 'Customer':
            return 'Customer'
        else:
            return 'Worker'
    else:
        return 'hey you mfs'
