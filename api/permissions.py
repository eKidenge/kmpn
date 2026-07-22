from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admins to edit objects.
    """
    
    def has_permission(self, request, view):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to admin users
        return request.user and request.user.is_staff
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to admin users
        return request.user and request.user.is_staff


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        elif hasattr(obj, 'author'):
            return obj.author == request.user
        
        return False


class IsMemberOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow verified members to edit.
    """
    
    def has_permission(self, request, view):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to verified members
        if request.user and request.user.is_authenticated:
            try:
                member = Member.objects.get(user=request.user)
                return member.verification_status == 'verified'
            except Member.DoesNotExist:
                return False
        
        return False


class HasAPIPermission(permissions.BasePermission):
    """
    Custom permission to check API token permissions.
    """
    
    def has_permission(self, request, view):
        # Check if user has API access
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user has specific API permissions
        # This can be extended based on your needs
        return True