from thirdparty.guardian.backends import ObjectPermissionBackend

class AMMSPermissionBackend(ObjectPermissionBackend):
    supports_anonymous_user = False